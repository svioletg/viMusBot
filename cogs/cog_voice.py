"""Cog file for voice chat operations."""

# Standard imports
import asyncio
import glob
import logging
import os
import random
import re
import time
from collections import deque
from dataclasses import dataclass
from math import ceil
from typing import Optional, Self, cast
from unittest.mock import MagicMock

import requests
import yt_dlp
# External imports
from discord import (Embed, FFmpegPCMAudio, Member, Message,
                     PCMVolumeTransformer, User, VoiceClient, VoiceState)
from discord.ext import commands
from yt_dlp import YoutubeDL

# Local imports
import utils.configuration as cfg
from cogs.common import (EMOJI, SilentCancel, command_aliases, edit_or_send,
                         embedq, is_command_enabled, prompt_for_choice)
from utils import media
from utils.miscutil import timestamp_from_seconds

log = logging.getLogger('viMusBot')

# Configure youtube dl
ytdl_format_options = {
    'format': 'bestaudio/best',
    'outtmpl': '%(extractor)s-#-%(id)s-#-%(title)s.%(ext)s',
    'restrictfilenames': True,
    'noplaylist': True,
    'nocheckcertificate': True,
    'ignoreerrors': False,
    'logtostderr': False,
    'quiet': False,
    'no_warnings': False,
    'default_search': 'auto',
    'extract_flat': True,
    'source_address': '0.0.0.0', # bind to ipv4 since ipv6 addresses cause issues sometimes
}

ytdl = YoutubeDL(ytdl_format_options)

ffmpeg_options = {
    'options': '-vn',
}

class YTDLSource(PCMVolumeTransformer):
    """Creates an AudioSource using yt_dlp."""
    def __init__(self, source, *, data, volume=0.5):
        super().__init__(source, volume)

        self.data = data

        self.title = data.get('title')
        self.url = data.get('url')
        self.ID = data.get('id')
        self.src = data.get('extractor')

    @classmethod
    async def from_url(cls, url, *, loop=None, stream=False):
        """Creates a YTDLSource from a URL."""
        loop = loop or asyncio.get_event_loop()
        data = await loop.run_in_executor(None, lambda: ytdl.extract_info(url, download=not stream))

        try:
            if 'entries' in data: # type: ignore
                # take first item from a playlist
                data = data['entries'][0] # type: ignore
        except Exception as e:
            raise e

        filename = data['url'] if stream else ytdl.prepare_filename(data) # type: ignore
        src = filename.split('-#-')[0] # pylint: disable=unused-variable
        ID = filename.split('-#-')[1] # pylint: disable=unused-variable
        return cls(FFmpegPCMAudio(filename, **ffmpeg_options), data=data) # type: ignore

@dataclass
class QueueItem:
    """Items which are to be placed inside of a `MediaQueue`, and nothing else. Holds a `TrackInfo` and the user that queued it."""
    info: media.TrackInfo
    queued_by: User | Member

    @classmethod
    def from_list(cls, playlist: list[media.TrackInfo], queued_by: User | Member) -> list[Self]:
        """Creates a list of individual `QueueItem` instances from a valid playlist or album.

        @playlist: Either a URL to a SoundCloud or ytdl-compatible playlist, or a list of Spotify tracks
        @queued_by: A discord Member object of the user who queued the playlist
        """
        return [cls(item, queued_by) for item in playlist]

class MediaQueue(list[QueueItem]):
    """Manages a media queue, keeping track of what's currently playing, what has previously played, whether looping is on, etc."""
    def __init__(self):
        self.is_looping: bool = False
        self.now_playing: Optional[YTDLSource] = None
        self.last_played: Optional[YTDLSource] = None
        self.current_item: Optional[QueueItem] = None
        self.now_playing_msg: Optional[Message] = None
        self.queue_msg: Optional[Message] = None

    def append(self, item: QueueItem):
        if not isinstance(item, QueueItem):
            raise ValueError('Attempt to append a non-QueueItem to a MediaQueue.')
        super().append(item)

    def extend(self, item: list[QueueItem]):
        if any(not isinstance(i, QueueItem) for i in item):
            raise ValueError('Attempt to append a non-QueueItem to a MediaQueue.')
        super().extend(item)

    def queue(self, to_queue: QueueItem | list[QueueItem]) -> int | tuple[int, int]:
        """Takes either a single `QueueItem` or a list of them, and queues them."""
        start: int = len(self)
        if isinstance(to_queue, list):
            self.extend(to_queue)
            end: int = len(self) - 1
            return start, end

        if isinstance(to_queue, QueueItem):
            self.append(to_queue)
            return start

class AlbumLimitError(Exception):
    """Raised when a playlist exceeds its maximum length, set by user configuration."""
class PlaylistLimitError(Exception):
    """Raised when a playlist exceeds its maximum length, set by user configuration."""

async def author_in_vc(ctx: commands.Context) -> bool:
    """Checks whether the command author is connected to a voice channel before allowing it to run."""
    command_author = cast(Member, ctx.author)
    if not command_author.voice:
        log.info('Command author not connected to voice, cancelling.')
        await ctx.send(embed=embedq(EMOJI['cancel'] + ' You must be connected to a voice channel to do this.'))
        return False
    return True

class Voice(commands.Cog):
    """Handles voice and music-related tasks."""

    def __init__(self, bot: commands.bot.Bot):
        self.bot = bot
        self.voice_client: Optional[VoiceClient] = None
        self.media_queue = MediaQueue()
        self.play_history: deque = deque(maxlen=5)
        self.advance_lock: bool = False

        self.skip_votes_placed: list[Member] = []

        self.paused_at: float = 0.0
        self.pause_duration: float = 0.0
        self.audio_time_elapsed: float = 0.0

        self.current: dict[str, Optional[YTDLSource | QueueItem]] = {'source': None, 'item': None}
        self.previous = self.current.copy()

        self.now_playing_msg: Optional[Message] = None
        self.queue_msg: Optional[Message] = None

    @commands.Cog.listener()
    async def on_voice_state_update(self, member: Member, before: VoiceState, after): # pylint: disable=unused-variable
        """Listener for the voice state update event. Currently handles inactivity timeouts and tracks how long audio has been playing."""
        if not (member.id == self.bot.user.id):
            return
        if before.channel is None:
            # Disconnect after set amount of inactivity
            if cfg.INACTIVITY_TIMEOUT_MINS == 0:
                return
            timeout_counter = 0
            while True:
                await asyncio.sleep(1)
                timeout_counter += 1

                if self.voice_client.is_playing() and not self.voice_client.is_paused():
                    timeout_counter = 0
                    self.audio_time_elapsed += 1

                if timeout_counter == cfg.INACTIVITY_TIMEOUT_MINS * 60:
                    log.info('Leaving voice due to inactivity...')
                    await self.voice_client.disconnect()
                if not self.voice_client.is_connected():
                    log.debug('Voice doesn\'t look connected, waiting three seconds...')
                    await asyncio.sleep(3)
                    if not self.voice_client.is_connected():
                        log.debug('Still disconnected. Discarding voice client reference...')
                        # Delay discarding this reference until we're sure that we actually disconnected
                        # Sometimes a brief network hiccup can be detected as not being connected to voice,
                        # even though the bot is still present in Discord...
                        # ...in which case, if we discard our reference to it too soon, everything voice-related breaks
                        self.voice_client = None
                        break
                    else:
                        log.debug('Voice looks connected again. Continuing as normal...')


    #region COMMANDS
    @commands.command(aliases=command_aliases('join'))
    @commands.check(is_command_enabled)
    @commands.check(author_in_vc)
    async def join(self, ctx: commands.Context):
        """Joins the same voice channel the command user is connected to."""
        await ctx.send(embed=embedq(f'Joining voice channel: {cast(Member, ctx.author).voice.channel.name}'))

    @commands.command(aliases=command_aliases('leave'))
    @commands.check(is_command_enabled)
    @commands.check(author_in_vc)
    async def leave(self, ctx: commands.Context):
        """Leaves the currently connected to voice channel."""
        if self.voice_client.is_connected():
            log.info('Clearing the queue...')
            self.media_queue.clear()
            log.info('Leaving voice channel: %s', self.voice_client.channel.name)
            await self.voice_client.disconnect()
            self.voice_client = None
        else:
            log.debug('No channel to leave.')

    @commands.command(aliases=command_aliases('queue'))
    @commands.check(is_command_enabled)
    async def queue(self, ctx: commands.Context, page: int=1):
        """Displays the current queue, up to 10 items per page."""
        if not self.media_queue:
            await ctx.send(embed=embedq('Queue is empty.'))
            return

        total_pages = ceil(len(self.media_queue) / 10)
        if page > total_pages:
            await ctx.send(embed=embedq(f'Out of range; the current queue has {total_pages} pages.', f'{len(self.media_queue)} items in total.'))
            return

        queue_time = 0
        for item in self.media_queue:
            queue_time += item.info.length_seconds

        queue_time += cast(QueueItem, self.current['item']).info.length_seconds - self.audio_time_elapsed

        queue_time = timestamp_from_seconds(queue_time)
        embed = Embed(title=f'{len(self.media_queue)} items in queue.\n*(Approx. time remaining: {queue_time})*',color=cfg.EMBED_COLOR)
        start = (10 * page) - 10
        end = 10 * page
        if (10 * page) > len(self.media_queue):
            end = len(self.media_queue)

        for num, item in enumerate(self.media_queue[start:end]):
            submitter_text = self.get_queued_by_text(item.queued_by) # type: ignore
            length_text = f'[{timestamp_from_seconds(item.info.length_seconds)}]' if timestamp_from_seconds(item.info.length_seconds) != '00:00' else ''
            embed.add_field(name=f'#{num + 1 + start}. {item.info.title} {length_text}', value=f'Link: {item.info.url}{submitter_text}', inline=False)

        embed.description = f'Showing {start + 1} to {end} of {len(self.media_queue)} items. Use -queue [page] to see more.'
        await ctx.send(embed=embed)

    @commands.command(aliases=command_aliases('move'))
    @commands.check(is_command_enabled)
    @commands.check(author_in_vc)
    async def move(self, ctx: commands.Context):
        raise NotImplementedError

    @commands.command(aliases=command_aliases('shuffle'))
    @commands.check(is_command_enabled)
    @commands.check(author_in_vc)
    async def shuffle(self, ctx: commands.Context):
        raise NotImplementedError

    @commands.command(aliases=command_aliases('remove'))
    @commands.check(is_command_enabled)
    @commands.check(author_in_vc)
    async def remove(self, ctx: commands.Context, n: int):
        """Removes an item from the queue at the given index."""
        if n >= len(self.media_queue):
            await ctx.send(embed=embedq(f'Out of range. The current queue is {len(self.media_queue)} items long.'))

        # Anyone using this command will be using the displayed numbers from -queue to figure out what index to use...
        # ...which starts at 1, not 0, so we're making sure this index will be accurate
        n -= 1
        removed = self.media_queue.pop(n)
        await ctx.send(embed=embedq(f'Removed "{removed.info.title}" from spot #{n} in the queue.'))

    @commands.command(aliases=command_aliases('clear'))
    @commands.check(is_command_enabled)
    @commands.check(author_in_vc)
    async def clear(self, ctx: commands.Context):
        """Removes everything from the queue."""
        log.info('Clearing the queue...')
        if self.media_queue:
            self.media_queue.clear()
            await ctx.send(embed=embedq('Queue is now empty.'))
        else:
            await ctx.send(embed=embedq('Queue is already empty.'))

    @commands.command(aliases=command_aliases('skip'))
    @commands.check(is_command_enabled)
    @commands.check(author_in_vc)
    async def skip(self, ctx: commands.Context):
        """Skips the current track. If vote-to-skip is disabled for this bot, it will be skipped immediately."""
        ctx.author = cast(Member, ctx.author)
        vote_requirement_real = cfg.SKIP_VOTES_EXACT if cfg.SKIP_VOTES_TYPE == 'exact'\
            else ceil(len(ctx.author.voice.channel.members) * (cfg.SKIP_VOTES_PERCENTAGE / 100))
        vote_requirement_display = cfg.SKIP_VOTES_EXACT if cfg.SKIP_VOTES_TYPE == 'exact' else f'{cfg.SKIP_VOTES_PERCENTAGE}%'
        skip_msg: Optional[Message] = None

        if self.voice_client.is_playing() or self.voice_client.is_paused():
            if cfg.VOTE_TO_SKIP:
                if ctx.author not in self.skip_votes_placed:
                    self.skip_votes_placed.append(ctx.author)
                    skip_msg = await ctx.send(embed=embedq('Voted to skip. '+
                        f'({len(self.skip_votes_placed)}/{vote_requirement_real})',
                        subtext=f'Vote-skipping mode is set to "{cfg.SKIP_VOTES_TYPE}", and {vote_requirement_display} votes are required.'))
                else:
                    await ctx.send(embed=embedq('You have already voted to skip.'))

            if (not cfg.VOTE_TO_SKIP) or (len(self.skip_votes_placed) >= vote_requirement_real):
                skip_msg = await edit_or_send(ctx, skip_msg, embed=embedq('Skipping...'))
                self.voice_client.stop()
                await self.advance_queue(ctx, skipping=True)
                skip_msg = await skip_msg.delete()
        else:
            await ctx.send(embed=embedq('Nothing to skip.'))

    @commands.command(aliases=command_aliases('loop'))
    @commands.check(is_command_enabled)
    @commands.check(author_in_vc)
    async def loop(self, ctx: commands.Context):
        raise NotImplementedError

    @commands.command(aliases=command_aliases('pause'))
    @commands.check(is_command_enabled)
    @commands.check(author_in_vc)
    async def pause(self, ctx: commands.Context):
        """Pauses the player."""
        if self.voice_client.is_playing():
            log.info('Pausing audio...')
            self.voice_client.pause()
            self.paused_at = time.time()
        elif self.voice_client.is_paused():
            await ctx.send(embed=embedq('Already paused. Use `play` to unpause.'))
        else:
            await ctx.send(embed=embedq('Nothing to pause.'))

    @commands.command(aliases=command_aliases('stop'))
    @commands.check(is_command_enabled)
    @commands.check(author_in_vc)
    async def stop(self, ctx: commands.Context):
        """Stops audio and clears the remaining queue."""
        log.info('Stopping audio and clearing the queue...')
        self.voice_client.stop()
        self.media_queue.clear()

    @commands.command(aliases=command_aliases('nowplaying'))
    @commands.check(is_command_enabled)
    async def nowplaying(self, ctx: commands.Context):
        """Shows what's currently playing, if any exists."""
        if self.voice_client.is_playing():
            await ctx.send(embed=self.embed_now_playing())
        else:
            await ctx.send(embed=embedq('Nothing is playing.'))

    @commands.command(aliases=command_aliases('play'))
    @commands.check(is_command_enabled)
    @commands.check(author_in_vc)
    async def play(self, ctx: commands.Context, *queries: str):
        """Adds a link to the queue. Plays immediately if the queue is empty.

        @queries: Can either be a single URL string, a list of URL strings, or a non-URL string for text searching
        """
        log.info('Running "play" command...')
        log.debug('Args: queries=%s', repr(queries))

        ctx.author = cast(Member, ctx.author)

        async def play_or_enqueue(item: QueueItem | list[QueueItem]):
            """Adds the given `QueueItem` to the media queue. If the queue is empty, the item will attempt to play immediately.
            Otherwise, the item is appended to the queue.

            @item: Either a single `QueueItem` or a list of `QueueItem`s to queue up.
            """
            log.info('Adding to queue...')
            queue_was_empty = self.media_queue == []
            item_index = self.media_queue.queue(item)

            if isinstance(item, list):
                item_index = cast(tuple[int, int], item_index)
                self.queue_msg = await edit_or_send(ctx, self.queue_msg,
                    embed=embedq(f'Added {len(item)} items to the queue, from #{item_index[0] + 1} to #{item_index[1] + 1}.'))

            if (not self.voice_client.is_playing()) and (queue_was_empty):
                log.info('Voice client is not playing and the queue is empty, going to try playing...')
                starting_msg = await ctx.send(embed=embedq('Starting...'))
                await self.advance_queue(ctx)
                starting_msg = await starting_msg.delete()
            else:
                if isinstance(item, QueueItem):
                    self.queue_msg = await edit_or_send(ctx, self.queue_msg,
                        embed=embedq(f'Added {item.info.title} to the queue at spot #{cast(int, item_index) + 1}'))

        # Using -play alone with no args should resume the bot if we're paused
        if not queries:
            if self.voice_client.is_paused():
                log.debug('Player is paused; resuming...')
                self.voice_client.resume()
                await ctx.send(embed=embedq('Player is resuming.'))
                self.pause_duration = time.time() - self.paused_at
            elif (not self.voice_client.is_playing()) and (self.media_queue != []):
                await ctx.send(embed=embedq('Starting queue...'))
                await self.advance_queue(ctx, skipping=True)
            else:
                await ctx.send(embed=embedq('No URL or search terms given.'))
            return

        # If we have queries, start sorting them
        url_strings: list[str] = []
        plain_strings: list[str] = []

        for item in queries:
            if item.startswith('https://'):
                url_strings.append(item)
            else:
                plain_strings.append(item)

        if url_strings and plain_strings:
            log.debug('Both URLs and plain text detected; cancelling.')
            await ctx.send('URLs and plain search terms can\'t be used at the same time.')
            return

        # We now have only queries of either one text search, or one or more URLs
        async with ctx.typing():
            log.info('Searching...')
            if self.queue_msg:
                self.queue_msg = await self.queue_msg.delete()
            self.queue_msg = await ctx.send(embed=embedq('Searching...'))

            #region play: PLAIN TEXT
            if plain_strings:
                text_search: str = ' '.join(plain_strings)
                log.debug('Using plain-text search: %s', text_search)
                top_songs, top_videos, top_albums = map(media.search_ytmusic_text(text_search).get, ('songs', 'videos', 'albums'))

                if cfg.USE_TOP_MATCH:
                    log.debug('USE_TOP_MATCH on.')
                    if top_songs:
                        log.debug('Queueing top song...')
                        await play_or_enqueue(QueueItem(top_songs[0], ctx.author))
                        return
                    elif top_videos:
                        log.debug('Queueing top video...')
                        await play_or_enqueue(QueueItem(top_videos[0], ctx.author))
                        return
                    else:
                        await ctx.send(embed=embedq('No close matches could be found.'))
                        return

                choice_embed = Embed(color=cfg.EMBED_COLOR, title='Please choose a search result to queue...')
                choice_options = {}
                position: int = 0
                # TODO: Probably can be condensed
                if top_songs:
                    position += 1
                    choice_embed.add_field(name='Top song result:',
                        value=EMOJI['num'][position] + f'**{top_songs[0].title}** | *{top_songs[0].artist}*')
                    choice_options[position] = top_songs[0]
                if top_videos:
                    position += 1
                    choice_embed.add_field(name='Top video result:',
                        value=EMOJI['num'][position] + f'**{top_videos[0].title}** | *{top_videos[0].artist}*')
                    choice_options[position] = top_videos[0]
                if top_albums:
                    position += 1
                    choice_embed.add_field(name='Top album result:',
                        value=EMOJI['num'][position] + f'**{top_albums[0].title}** | *{top_albums[0].artist}*')
                    choice_options[position] = top_albums[0]

                choice_prompt = await ctx.send(embed=choice_embed)
                choice = await prompt_for_choice(self.bot, ctx, choice_prompt, choice_nums=position, result_msg=self.queue_msg)
                if choice == 0:
                    return

                choice = choice_options[choice]

                await play_or_enqueue(QueueItem(choice, ctx.author) if not choice.contents else QueueItem.from_list(choice.contents, ctx.author))
                return
            #endregion play: PLAIN TEXT

            #region play: FROM URL
            if url_strings:
                if len(url_strings) > cfg.MAX_CONSECUTIVE_URLS:
                    log.debug('Cancelling play command: too many consecutive URLs.')
                    await ctx.send(embed=embedq(f'Too many URLs provided. (Max: {cfg.MAX_CONSECUTIVE_URLS})'))
                    return

                # Does Spotify even use spotify.link URLs anymore? I can barely test this because I can't seem to get one now
                url_strings = [requests.get(u, timeout=1).url if u.startswith('https://spotify.link') else u for u in url_strings]

                if len(url_strings) > 1 and any(re.findall(r"(playlist|album|sets)", link) for link in url_strings):
                    log.debug('Cancelling play command: album/playlist URL present in a set of URLs.')
                    await ctx.send(embed=embedq('Albums or playlists must be queued on their own.',
                        'Multi-URL queueing is allowed only for single tracks.'))
                    return

                # [ ] Handle playlists, albums
                if re.findall(r"(playlist|album|sets)", url_strings[0]):
                    log.debug('URL looks like a playlist or an album.')
                    # Because of the previous checks we know this has to only be one URL, no need to keep the list
                    url = url_strings[0]
                    media_list: Optional[media.PlaylistInfo | media.AlbumInfo] = None

                    if re.findall(r"https://(?:music\.|www\.|)youtube\.com/playlist\?list=", url):
                        # Convert to a normal YouTube playlist URL because dealing with YTMusic playlists/albums are a hassle
                        media_list = media.PlaylistInfo.from_ytdl(url.replace('Voice.', 'www.'))

                    if url.startswith('https://open.spotify.com/album/'):
                        media_list = media.AlbumInfo.from_spotify_url(url)
                    if url.startswith('https://open.spotify.com/playlist/'):
                        media_list = media.PlaylistInfo.from_spotify_url(url)

                    if re.findall(r"https://soundcloud\.com/\w+/sets/", url):
                        media_list = media.soundcloud_set(url)

                    # Final checks
                    if media_list:
                        if isinstance(media_list, media.AlbumInfo) and (len(media_list.contents) > cfg.MAX_ALBUM_LENGTH):
                            await self.queue_msg.edit(embed=embedq(EMOJI['cancel'] + 'Album is too long.',
                                f'Current limit is set to {cfg.MAX_ALBUM_LENGTH}.'))
                            return
                        if isinstance(media_list, media.PlaylistInfo) and (len(media_list.contents) > cfg.MAX_PLAYLIST_LENGTH):
                            await self.queue_msg.edit(embed=embedq(EMOJI['cancel'] + 'Playlist is too long.',
                                f'Current limit is set to {cfg.MAX_PLAYLIST_LENGTH}.'))
                            return

                        if isinstance(media_list, media.AlbumInfo) and media_list.source == media.SPOTIFY:
                            # Find a YTMusic equivalent album if we have a Spotify album
                            await self.queue_msg.edit(embed=embedq('Trying to match this Spotify album with a YouTube Music equivalent...'))
                            if match_result := media.match_ytmusic_album(media_list, threshold=50):
                                yt_album = match_result[0]
                                await self.queue_msg.edit(embed=embedq('A possible match was found. Queue this album?')\
                                    .add_field(name=yt_album.album_name, value=yt_album.artist)\
                                    .set_thumbnail(url=yt_album.thumbnail))

                                confirmation = await prompt_for_choice(self.bot, ctx, prompt_msg=self.queue_msg, yesno=True, delete_prompt=False)

                                if isinstance(confirmation, asyncio.TimeoutError):
                                    await self.queue_msg.edit(embed=embedq(f'{EMOJI['cancel']} Choice prompt timed out, nothing queued.'))
                                    return
                                if confirmation == 0:
                                    await self.queue_msg.edit(embed=embedq('Selection cancelled.', 'Nothing will be queued.'))
                                    return
                                if confirmation == 1:
                                    media_list = yt_album
                            else:
                                await self.queue_msg.edit(embed=embedq('Couldn\'t find any close matches for this album.',
                                    'Try using a source other than Spotify, if possible.'))
                                return

                        # If we've reached here, something was successfully found and can be queued without issue
                        await play_or_enqueue(QueueItem.from_list(media_list.contents, ctx.author))
                    else:
                        return
                else:
                    # Single track links
                    to_queue: list[QueueItem] = []
                    for n, url in enumerate(url_strings):
                        log.debug('Checking URL %s of %s: %s', n + 1, len(url_strings), url)
                        await self.queue_msg.edit(embed=embedq(f'Queueing item {n + 1} of {len(url_strings)}...', url))
                        if re.findall(r"https://(?:music\.|www\.|)youtube\.com/watch\?v=", url):
                            log.debug('Looks like a YouTube Music or YouTube URL, creating QueueItem...')
                            to_queue.append(QueueItem(media.TrackInfo.from_pytube(url), ctx.author))
                        elif url.startswith('https://open.spotify.com/track/'):
                            log.debug('Looks like a Spotify URL, creating QueueItem...')
                            to_queue.append(QueueItem(media.TrackInfo.from_spotify_url(url), ctx.author))
                        elif url.startswith('https://soundcloud.com/'):
                            log.debug('Looks like a SoundCloud URL, creating QueueItem...')
                            to_queue.append(QueueItem(media.TrackInfo.from_soundcloud_url(url), ctx.author))
                        else:
                            log.debug('Creating QueueItem generically...')
                            to_queue.append(QueueItem(media.TrackInfo.from_other(url), ctx.author))
                    await play_or_enqueue(to_queue if len(to_queue) > 1 else to_queue[0])
                    return
            #endregion FROM URL

    @join.before_invoke
    @leave.before_invoke
    @play.before_invoke
    @skip.before_invoke
    @stop.before_invoke
    @nowplaying.before_invoke
    async def ensure_voice(self, ctx: commands.Context):
        """Joins the author's voice channel if no voice client is active."""
        author = cast(Member, ctx.author)
        auto_connect_commands = ['join', 'play']
        if (not self.voice_client) and author.voice:
            if ctx.command.name in auto_connect_commands:
                log.info('Joining voice channel: %s', author.voice.channel.name)
                self.voice_client = await author.voice.channel.connect()
            else:
                # No reason to auto-connect for something like -leave, -skip, etc.
                await ctx.send(embed=embedq('No voice connection found.',
                    'The bot will automatically connect to a voice channel if one of these commands are used: '+
                    f'{', '.join(auto_connect_commands)}'))
                raise SilentCancel

    #endregion COMMANDS
    #region END OF COMMANDS
    #endregion END OF COMMANDS

    def get_queued_by_text(self, member: Member) -> str:
        """Returns the nickname (if set, username otherwise) of who queued the current item if that is enabled,
        otherwise an empty string."""
        return f'\nQueued by {member.nick or member.name}' if cfg.SHOW_USERS_IN_QUEUE else ''

    def get_loop_icon(self) -> str:
        """Returns a looping emoji is looping is enabled, nothing otherwise."""
        return EMOJI['repeat'] + ' ' if self.media_queue.is_looping else ''

    def embed_now_playing(self) -> Embed:
        """Constructs and returns the "Now playing" message embed."""
        item = cast(QueueItem, self.current['item'])
        submitter_text = self.get_queued_by_text(cast(Member, item.queued_by))
        embed = Embed(title=self.get_loop_icon() + \
            f'{self.get_loop_icon()}Now playing: {item.info.title} [{item.info.length_hms()}]',
            description=f'Link: {item.info.url}{submitter_text}', color=cfg.EMBED_COLOR).set_thumbnail(url=item.info.thumbnail)
        return embed

    async def make_and_start_player(self, item: QueueItem, ctx: commands.Context):
        """Create a new player from the given `QueueItem` and starts playing audio.
        Handles matching individual Spotify tracks to YTVoice.

        Use `advance_queue()` to attempt moving the queue along, do not use this function directly."""
        log.info('Trying to start playing...')

        self.previous = self.current.copy()

        if self.now_playing_msg:
            self.now_playing_msg = await self.now_playing_msg.delete()

        # Start the player with retrieved URL
        if item.info.source == media.SPOTIFY:
            log.debug('Spotify source detected, matching to YouTube music if possible...')
            self.queue_msg = await edit_or_send(ctx, self.queue_msg,
                embed=embedq('Spotify link detected, searching for a YouTube Music match...'))
            matches = media.match_ytmusic_track(item.info)
            if isinstance(matches, list):
                if cfg.USE_TOP_MATCH:
                    matches = matches[0]
                else:
                    prompt_msg = await ctx.send(embed=embedq('Some close matches were found. Please choose one to queue.',
                        '\n'.join([EMOJI['num'][n + 1] + f' **{track.title}**\n*{track.artist}*' for n, track in enumerate(matches)])))
                    choice = await prompt_for_choice(self.bot, ctx,
                        prompt_msg=prompt_msg, choice_nums=len(matches), result_msg=self.queue_msg)
                    if isinstance(choice, int) and choice != 0:
                        item.info = matches[choice]
                    else:
                        await self.advance_queue(ctx)
                        return
            if isinstance(matches, media.TrackInfo):
                item.info = matches

        try:
            log.debug('Creating YTDLSource...')
            player = await YTDLSource.from_url(item.info.url, loop=self.bot.loop, stream=False)
            self.current['player'] = player
        except yt_dlp.utils.DownloadError:
            log.info('Download error occurred; skipping this item...')
            await ctx.send(embed=embedq('This video is unavailable.', f'URL: {item.info.url}'))
            await self.advance_queue(ctx)
            return

        self.current['item'] = item

        self.voice_client.stop()
        log.info('Starting audio playback...')
        self.voice_client.play(player, after=lambda e: asyncio.run_coroutine_threadsafe(self.advance_queue(ctx), self.bot.loop))

        self.now_playing_msg = await ctx.send(embed=self.embed_now_playing())

        if self.queue_msg:
            self.queue_msg = await self.queue_msg.delete()

        if self.previous['source']:
            for file in glob.glob(f'*-#-{cast(YTDLSource, self.previous['source']).ID}-#-*'):
                # Delete last played file
                try:
                    log.debug('Removing file: %s', file)
                    os.remove(file)
                except PermissionError:
                    log.debug('Permission denied removing file: %s', file)

    async def advance_queue(self, ctx: commands.Context, skipping: bool=False):
        """Attempts to advance forward in the queue, if the bot is clear to do so.
        Set to run whenever the audio player finishes its current item."""
        if not self.voice_client.is_connected():
            return
        if not self.advance_lock and (skipping or not self.voice_client.is_playing()):
            log.debug('Locking...')
            self.advance_lock = True
            self.skip_votes_placed.clear()
            try:
                if not self.media_queue:
                    self.voice_client.stop()
                else:
                    await self.make_and_start_player(self.media_queue.pop(0), ctx)
            finally:
                # finally statement makes sure we still unlock if an error occurs
                log.debug('Tasks finished; unlocking...')
                self.advance_lock = False
        elif self.advance_lock:
            log.debug('Attempted call while locked; ignoring...')

# #region TESTS
# class Tests:
#     test_sources = ['youtube', 'spotify', 'bandcamp', 'soundcloud']
#     test_urls = {
#             'single': {
#                 'valid': {
#                     'youtube':    ['https://www.youtube.com/watch?v=bNpEUbWOBiM',
#                                    'https://www.youtube.com/watch?v=3XAhEUHt3zY',
#                                    'https://www.youtube.com/watch?v=Q-i1XZc8ZwA'],
#                     'spotify':    ['https://open.spotify.com/track/1E2WTcYLP1dFe1tiGDwRmT?si=e83bb1fcb80640ad',
#                                    'https://open.spotify.com/track/0WHtcCpZnoyFlQg3Mf2cdN?si=73230e1b24084038',
#                                    'https://open.spotify.com/track/56k2ztFw7hQRzDeoe80pJo?si=90310e0adbf0472a'],
#                     'bandcamp':   ['https://jeffrosenstock.bandcamp.com/track/graveyard-song',
#                                    'https://jeffrosenstock.bandcamp.com/track/9-10',
#                                    'https://jeffrosenstock.bandcamp.com/track/leave-it-in-the-sun'],
#                     'soundcloud': ['https://soundcloud.com/sethgibbsmusic/rain',
#                                    'https://soundcloud.com/weeppiko/like-a-thunder',
#                                    'https://soundcloud.com/griffinmcelroy/the-adventure-zone-ethersea-theme']
#                 },
#                 'invalid': {
#                     'youtube':    ['https://www.youtube.com/watch?v=THISISANINVALIDURLANDDOESNTEXIST'],
#                     'spotify':    ['https://open.spotify.com/track/THISISANINVALIDURLANDDOESNTEXIST'],
#                     'bandcamp':   ['https://THISISANINVALIDURLANDDOESNTEXIST.bandcamp.com/track/THISISANINVALIDURLANDDOESNTEXIST'],
#                     'soundcloud': ['https://soundcloud.com/THISISANINVALIDURLANDDOESNTEXIST/THISISANINVALIDURLANDDOESNTEXIST']
#                 }
#             },
#             'playlist': {
#                 'valid': {
#                     'youtube':    ['https://www.youtube.com/playlist?list=PL0uKqjIajhzGshCt76OeXLspFh5MmM-Vu',
#                                    'https://www.youtube.com/playlist?list=PL67cMGyeB5sEh3ZjGgo8oXzIrbDggG1gs',
#                                    'https://www.youtube.com/playlist?list=OLAK5uy_m-FE5IenHYY2Fd1M2RX-k11yKohFrvZi0'],
#                     'spotify':    ['https://open.spotify.com/playlist/7IjLgeYeUkFzNvBirgfsAf?si=c55c2848887249da',
#                                    'https://open.spotify.com/playlist/1FkZjVP9O80Chh37YhyKaU?si=d12241575b444d45',
#                                    'https://open.spotify.com/playlist/3jlpvgHatDehrSrR72DYVq?si=932b79272c7c4a30'],
#                     'bandcamp':   ['https://jeffrosenstock.bandcamp.com/album/hellmode',
#                                    'https://jeffrosenstock.bandcamp.com/album/post',
#                                    'https://jeffrosenstock.bandcamp.com/album/no-dream'],
#                     'soundcloud': ['https://soundcloud.com/sethgibbsmusic/sets/2019-releases',
#                                    'https://soundcloud.com/sethgibbsmusic/sets/original-tracks-2020',
#                                    'https://soundcloud.com/sethgibbsmusic/sets/remixes']
#                 },
#                 'invalid': {
#                     'youtube':    ['https://www.youtube.com/playlist?list=THISISANINVALIDURLANDDOESNTEXIST'],
#                     'spotify':    ['https://open.spotify.com/playlist/THISISANINVALIDURLANDDOESNTEXIST'],
#                     'bandcamp':   ['https://THISISANINVALIDURLANDDOESNTEXIST.bandcamp.com/album/THISISANINVALIDURLANDDOESNTEXIST'],
#                     'soundcloud': ['https://soundcloud.com/THISISANINVALIDURLANDDOESNTEXIST/sets/THISISANINVALIDURLANDDOESNTEXIST']
#                 }
#             },
#             'album': {
#                 'valid': {
#                     'youtube':    ['https://Voice.youtube.com/playlist?list=OLAK5uy_lQT8aLCDHiFu4_NkoxHt1VSfUBpjSIwHY',
#                                    'https://Voice.youtube.com/playlist?list=OLAK5uy_kb8kfsyt08s2Z29752CH_lelHdl_JDwgg',
#                                    'https://Voice.youtube.com/playlist?list=OLAK5uy_mp-RVdXLFGSC62WMsBlrqlF3RlZatyowA'],
#                     'spotify':    ['https://open.spotify.com/album/1KMfjy6MmPorahRjxhTnxm?si=CS0F1ZFsQqSsn0xH_ahDiA',
#                                    'https://open.spotify.com/album/74QTwjBLo1eLqpjL320rXX?si=1ehOqrxBR8WjHftNReHAtw',
#                                    'https://open.spotify.com/album/3fn4HfVz5dhmE0PG24rh6h?si=tFUiBS7iSq6QGg-rNNgXkg'],
#                     'bandcamp':   ['https://jeffrosenstock.bandcamp.com/album/hellmode',
#                                    'https://jeffrosenstock.bandcamp.com/album/post',
#                                    'https://jeffrosenstock.bandcamp.com/album/no-dream'],
#                     'soundcloud': ['https://soundcloud.com/sethgibbsmusic/sets/2019-releases',
#                                    'https://soundcloud.com/sethgibbsmusic/sets/original-tracks-2020',
#                                    'https://soundcloud.com/sethgibbsmusic/sets/remixes']
#                 },
#                 'invalid': {
#                     'youtube':    ['https://Voice.youtube.com/playlist?list=WROOOOOOOOONGLIIIIIIIIIIIINK'],
#                     'spotify':    ['https://open.spotify.com/album/THISISALSOINCORRECTNOTAREALALBUM'],
#                     'bandcamp':   ['https://THISISANINVALIDURLANDDOESNTEXIST.bandcamp.com/album/THISISANINVALIDURLANDDOESNTEXIST'],
#                     'soundcloud': ['https://soundcloud.com/THISISANINVALIDURLANDDOESNTEXIST/sets/THISISANINVALIDURLANDDOESNTEXIST']
#                 }
#             }
#         }

#     def __init__(self, inst: Voice):
#         self.inst = inst

#     @classmethod
#     async def test_play(cls, source: str, flags: Optional[list[str]]=None) -> Optional[dict]:
#         """NOT a completely comprehensive test, but covers most common bases

#         Valid flags:
#         - `invalid` = Use an intentionally invalid URL
#         - `multiple` = Use multiple URLs
#         - `playlist` = Use a playlist URL
#         - `album` = Use an album URL

#         "playlist" and "album" can't be used together
#         """
#         debugctx = MagicMock(spec=commands.Context)
#         # if (not bypass_ctx) and (debugctx is None):
#         #     log.error('Debug context is not set; aborting test. Use the "dctx" bot command while in a voice channel to grab one.')
#         #     return

#         if source not in cls.test_sources + ['any', 'mixed']:
#             log.error('Invalid source; aborting test. Valid sources are: %s', {', '.join(cls.test_sources)})
#             return

#         flags = flags or []

#         valid: str = 'invalid' if 'invalid' in flags else 'valid'
#         playlist_or_album: str | bool = 'playlist' if 'playlist' in flags else 'album' if 'album' in flags else False
#         multiple_urls: bool = 'multiple' in flags

#         passed: bool = False
#         conclusion: str = ''
#         arguments: str = f'SOURCE? {source} | VALID? {valid} | MULTIPLE? {multiple_urls} | PLAYLIST/ALBUM? {playlist_or_album}'

#         log.info('### START TEST! play command; {arguments}')

#         if 'playlist' in flags and 'album' in flags:
#             log.error('Invalid flags; aborting test. The "playlist" and "album" flags cannot be used together.')
#             return

#         src = random.choice(cls.test_sources) if source in ['any', 'mixed'] else source
#         url_type = playlist_or_album if playlist_or_album else 'single'

#         await Voice.ensure_voice(Voice, debugctx)
#         if not multiple_urls:
#             await Voice.play(Voice, debugctx, random.choice(cls.test_urls[url_type][valid][src]))
#             if voice.is_playing():
#                 conclusion = 'voice client is playing. Test likely passed.'
#                 log.info(conclusion); passed = True
#             else:
#                 if valid == 'invalid':
#                     conclusion = 'voice client is not playing, and an intentionally invalid URL was used. Test likely passed.'
#                     log.info(conclusion); passed = True
#                 else:
#                     conclusion = 'voice client is not playing, but a valid URL was used. Test likely failed.'
#                     log.info(conclusion)
#         else:
#             urls = []
#             if source == 'mixed':
#                 for s in cls.test_sources:
#                     urls.append(random.choice(cls.test_urls[url_type][valid][s]))
#             else:
#                 urls = cls.test_urls[url_type][valid][src]

#             await Voice.play(Voice, debugctx, *urls)
#             if voice.is_playing() and media_queue.get(debugctx) != []:
#                 conclusion = f'Voice client is playing and the queue is not empty. Test likely passed.'
#                 log.info(conclusion); passed = True
#             else:
#                 if valid == 'invalid':
#                     conclusion = f'Voice client is not playing, and an intentionally invalid URL was used. Test likely passed.'
#                     log.info(conclusion); passed = True
#                 elif playlist_or_album:
#                     conclusion = f'Voice client is not playing, all URLs were valid, but multiple {playlist_or_album} URLs were used. Test likely passed.'
#                     log.info(conclusion); passed = True
#                 elif media_queue.get(debugctx) != []:
#                     conclusion = f'Voice client is not playing, but the queue is not empty. Test likely failed.'
#                     log.info(conclusion)
#                 else:
#                     conclusion = f'Voice client is not playing, but all valid URLs were used. Test likely failed.'
#                     log.info(conclusion)

#         log.info(f'Waiting 2 seconds...')
#         time.sleep(2)
#         log.info(f'Clearing media queue and stopping voice client...')
#         media_queue.clear(debugctx)
#         voice.stop()
#         log.info(f'Waiting 2 seconds...')
#         time.sleep(2)
#         log.info(f'### END TEST!')
#         return {'passed': passed, 'arguments': arguments, 'conclusion': conclusion}
# #endregion TESTS
