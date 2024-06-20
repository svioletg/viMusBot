"""Cog file for voice chat operations."""

# Standard imports
import asyncio
import logging
import os
import random
import re
import time
from collections import deque
from dataclasses import dataclass
from math import ceil
from pathlib import Path
from typing import Callable, Optional, Self, cast

# External imports
import requests
import yt_dlp
from discord import (Embed, FFmpegPCMAudio, Member, Message,
                     PCMVolumeTransformer, User, VoiceClient, VoiceState)
from discord.ext import commands

# Local imports
import utils.configuration as cfg
from cogs.common import (EmojiStr, SilentCancel, command_aliases, edit_or_send,
                         embedq, is_command_enabled, prompt_for_choice)
from cogs.messages import CommonMsg
from cogs.test_voice import VoiceTest
from utils import media
from utils.miscutil import seconds_to_hms

log = logging.getLogger('lydian')

# Configure youtube dl
ytdl = yt_dlp.YoutubeDL(media.ytdl_format_options)

ffmpeg_options = media.ffmpeg_options

class YTDLSource(PCMVolumeTransformer):
    """Creates an AudioSource using yt_dlp."""
    def __init__(self, source, *, data, filepath: Path, volume: float=0.5):
        super().__init__(source, volume)

        self.data = data
        self.filepath = filepath

        self.title = data.get('title')
        self.url = data.get('url')
        self.ID = data.get('id') # pylint: disable=invalid-name
        self.src = data.get('extractor')

    @classmethod
    async def from_url(cls, url, *, loop=None, stream=False) -> Self:
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
        ID = filename.split('-#-')[1] # pylint: disable=unused-variable, invalid-name
        return cls(FFmpegPCMAudio(filename, **ffmpeg_options), data=data, filepath=Path(filename)) # type: ignore

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
        self.roulette_mode: bool = False
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

    def enqueue(self, to_queue: QueueItem | list[QueueItem]) -> int | tuple[int, int]:
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
    """Checks whether the command author is connected to a voice channel before allowing it to run.

    If the author *is* connected, they must be connected to the same voice channel the bot is in for this to pass."""
    command_author = cast(Member, ctx.author)
    if not command_author.voice:
        log.info('Command author not connected to voice, cancelling.')
        await ctx.send(embed=embedq(EmojiStr.cancel + ' You must be connected to a voice channel to do this.'))
        return False

    if ctx.voice_client:
        if ctx.voice_client.channel == command_author.voice.channel:
            return True
        else:
            await ctx.send(embed=embedq(EmojiStr.cancel + ' You must be in the same voice channel as the bot to do this.',
                f'The bot is currently connected to "{ctx.voice_client.channel}"'))
            return False
    else:
        return True

class Voice(commands.Cog):
    """Handles voice and music-related tasks."""

    def __init__(self, bot: commands.bot.Bot):
        self.bot = bot
        self.voice_client: Optional[VoiceClient] = None
        self.media_queue = MediaQueue()
        self.play_history: deque[Optional[QueueItem]] = deque([None, None, None, None, None], maxlen=5)
        self.current_item: Optional[QueueItem] = None
        self.previous_item: Optional[QueueItem] = None
        self.files_to_del: list[Path] = []
        self.player: Optional[YTDLSource] = None

        self.advance_lock: bool = False
        self.after_advance_queue: Optional[Callable] = None

        self.skip_votes_placed: list[Member] = []

        self.paused_at: float = 0.0
        self.pause_duration: float = 0.0
        self.audio_time_elapsed: float = 0.0

        self.now_playing_msg: Optional[Message] = None
        self.queue_msg: Optional[Message] = None

    @commands.Cog.listener()
    async def on_voice_state_update(self, member: Member, before: VoiceState, after: VoiceState): # pylint: disable=unused-argument
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

                if self.voice_client is None:
                    break

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
    @commands.command(aliases=command_aliases('test'))
    @commands.check(is_command_enabled)
    async def test(self, ctx: commands.Context, to_test: str, *args):
        """Runs a test for the given command name.

        @to_test: The name of the test to run. Usually a command's name.
        """
        tester = VoiceTest(self)
        await tester.perform_test(ctx, to_test, *args)

    @commands.command(aliases=command_aliases('join'))
    @commands.check(is_command_enabled)
    @commands.check(author_in_vc)
    async def join(self, ctx: commands.Context):
        """Joins the same voice channel the command user is connected to."""
        author = cast(Member, ctx.author)
        await ctx.send(embed=embedq(f'Joining voice channel: {author.voice.channel.name}'))

    @commands.command(aliases=command_aliases('leave'))
    @commands.check(is_command_enabled)
    @commands.check(author_in_vc)
    async def leave(self, ctx: commands.Context): # pylint: disable=unused-argument
        """Leaves the currently connected to voice channel."""
        if self.voice_client.is_connected():
            log.info('Clearing the queue...')
            self.media_queue.clear()
            self.current_item = None
            self.previous_item = None
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
            await ctx.send(embed=CommonMsg.queue_is_empty())
            return

        total_pages = ceil(len(self.media_queue) / 10)
        if page > total_pages:
            await ctx.send(embed=CommonMsg.queue_out_of_range(len(self.media_queue)))
            return

        queue_length_seconds = seconds_to_hms(sum(item.info.length_seconds for item in self.media_queue) +
            self.current_item.info.length_seconds - self.audio_time_elapsed)

        embed = embedq(title=f'{len(self.media_queue)} items in queue.\n*(Approx. time remaining: {queue_length_seconds})*',)
        start = (10 * page) - 10
        end = 10 * page
        if (10 * page) > len(self.media_queue):
            end = len(self.media_queue)

        for num, item in enumerate(self.media_queue[start:end]):
            submitter_text = self.get_queued_by_text(item.queued_by) # type: ignore
            length_text = f'[{item.info.length_hms()}]' if item.info.length_seconds != 0 else ''
            embed.add_field(name=f'#{num + 1 + start}. {item.info.title} {length_text}',
                value=f'Link: {item.info.url}{submitter_text}', inline=False)

        embed.description = ('**Roulette mode is ON.**\n' if self.media_queue.roulette_mode else '') + \
            f'Showing {start + 1} to {end} of {len(self.media_queue)} items. Use -queue [page] to see more.'
        await ctx.send(embed=embed)

    @commands.command(aliases=command_aliases('history'))
    @commands.check(is_command_enabled)
    async def history(self, ctx: commands.Context):
        """Shows the 5 most recently played tracks."""
        if not any(item is not None for item in self.play_history):
            await ctx.send(embed=embedq(EmojiStr.cancel + ' Play history is empty.'))
            return

        history_embed = embedq('Recently played:')
        for n, item in enumerate(self.play_history):
            if not item:
                continue
            history_embed.add_field(name=f'#{n + 1}. {item.info.title}', value=item.info.artist, inline=False)

        await ctx.send(embed=history_embed)

    @commands.command(aliases=command_aliases('move'))
    @commands.check(is_command_enabled)
    @commands.check(author_in_vc)
    async def move(self, ctx: commands.Context, origin: int, destination: int):
        """Moves the queue item located at `origin` to `destination`.

        @origin: Index of the queue item to be moved.
        @destination: What spot the item should be moved to."""
        if self.media_queue == []:
            await ctx.send(embed=CommonMsg.queue_is_empty())
            return
        if (origin < 1) or (destination < 1):
            await ctx.send(embed=embedq(EmojiStr.cancel + ' Origin or destination can\'t be less than 1.'))
            return
        if destination >= len(self.media_queue):
            await ctx.send(embed=CommonMsg.queue_out_of_range(len(self.media_queue)))
            return
        if origin == destination:
            await ctx.send(embed=embedq(EmojiStr.cancel + ' Origin and destination can\'t be the same.'))
            return

        self.media_queue.insert(destination - 1, origin_item := self.media_queue.pop(origin - 1))
        direction = 'up' if destination < origin else 'down'
        await ctx.send(embed=embedq(EmojiStr.arrow_u if direction == 'up' else EmojiStr.arrow_d + f' Moved #{origin} ({origin_item.info.title}) ' +
            f'{direction} to spot #{destination}.'))

    @commands.command(aliases=command_aliases('shuffle'))
    @commands.check(is_command_enabled)
    @commands.check(author_in_vc)
    async def shuffle(self, ctx: commands.Context):
        """Shuffles the order of the queue."""
        if self.media_queue == []:
            await ctx.send(embed=CommonMsg.queue_is_empty())
            return

        random.shuffle(self.media_queue)
        log.info('Queue has been shuffled.')
        await ctx.send(embed=embedq(f'{EmojiStr.shuffle} Queue shuffled.'))

    @commands.command(aliases=command_aliases('roulette'))
    @commands.check(is_command_enabled)
    @commands.check(author_in_vc)
    async def roulette(self, ctx: commands.Context, toggle: str=''):
        """Toggles "roulette" mode. If no argument is given, roulette mode will be turned on if its currently off, and vice versa.
        Alternatively, you can use "roulette on" or "roulette off" to toggle it explicitly.

        If roulette mode is enabled, the queue will be used as a pool of random choices instead of a strict order.
        In other words, instead of moving to the next song when one finishes playing, a random choice from the queue will be selected to play.
        """
        if toggle in ['on', 'off']:
            self.media_queue.roulette_mode = {'on': True, 'off': False}[toggle]
            log.info('Roulette mode changed to %s.', self.media_queue.roulette_mode)
        else:
            if toggle == '':
                self.media_queue.roulette_mode = not self.media_queue.roulette_mode
                log.info('Roulette mode changed to %s.', self.media_queue.roulette_mode)
            else:
                await ctx.send(embed=embedq(f'{EmojiStr.cancel} Invalid option; must be either "on" or "off"'))
                return
        await ctx.send(embed=embedq(f'Roulette mode is {'ON' if self.media_queue.roulette_mode else 'OFF'}.'))

    @commands.command(aliases=command_aliases('remove'))
    @commands.check(is_command_enabled)
    @commands.check(author_in_vc)
    async def remove(self, ctx: commands.Context, n: int):
        """Removes an item from the queue at the given index."""
        if n >= len(self.media_queue):
            await ctx.send(embed=CommonMsg.queue_out_of_range(len(self.media_queue)))
            return

        # Anyone using this command will be using the displayed numbers from -queue to figure out what index to use...
        # ...which starts at 1, not 0, so we're making sure this index will be accurate
        n -= 1
        removed = self.media_queue.pop(n)
        await ctx.send(embed=embedq(f'{EmojiStr.outbox} Removed "{removed.info.title}" from spot #{n + 1} in the queue.'))

    @commands.command(aliases=command_aliases('clear'))
    @commands.check(is_command_enabled)
    @commands.check(author_in_vc)
    async def clear(self, ctx: commands.Context):
        """Removes everything from the queue."""
        log.info('Clearing the queue...')
        if self.media_queue:
            self.media_queue.clear()
            await ctx.send(embed=embedq(f'{EmojiStr.outbox} Queue is now empty.'))
        else:
            await ctx.send(embed=embedq('Queue is already empty.'))

    @commands.command(aliases=command_aliases('skip'))
    @commands.check(is_command_enabled)
    @commands.check(author_in_vc)
    async def skip(self, ctx: commands.Context):
        """Skips the current track. If vote-to-skip is disabled for this bot, it will be skipped immediately."""
        ctx.author = cast(Member, ctx.author)
        vote_requirement_real = cfg.SKIP_VOTES_EXACT if cfg.SKIP_VOTES_TYPE == 'exact' \
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
                skip_msg = await edit_or_send(ctx, skip_msg, embed=embedq(EmojiStr.skip + ' Skipping...'))
                self.voice_client.stop()
                await self.advance_queue(ctx, skipping=True)
                skip_msg = await skip_msg.delete()
        else:
            await ctx.send(embed=embedq('Nothing to skip.'))

    @commands.command(aliases=command_aliases('loop'))
    @commands.check(is_command_enabled)
    @commands.check(author_in_vc)
    async def loop(self, ctx: commands.Context, toggle: str=''):
        """Toggles looping the current track. If no argument is given, looping will be turned on if its currently off, and vice versa.
        Alternatively, you can use "loop on" or "loop off" to toggle it explicitly.

        Using `skip` while looping is enabled will skip to the next track in queue, and begin looping that."""
        if toggle in ['on', 'off']:
            self.media_queue.is_looping = {'on': True, 'off': False}[toggle]
            log.info('Looping changed to %s.', self.media_queue.is_looping)
        else:
            if toggle == '':
                self.media_queue.is_looping = not self.media_queue.is_looping
                log.info('Looping changed to %s.', self.media_queue.is_looping)
            else:
                await ctx.send(embed=embedq(EmojiStr.cancel + ' Invalid option; must be either "on" or "off"'))
                return
        await ctx.send(embed=embedq(f'Looping is {'ON' if self.media_queue.is_looping else 'OFF'}.'))

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
    async def stop(self, ctx: commands.Context): # pylint: disable=unused-argument
        """Stops audio and clears the remaining queue."""
        log.info('Stopping audio and clearing the queue...')
        self.voice_client.stop()
        self.media_queue.clear()
        self.current_item = None
        self.previous_item = None

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
            item_index = self.media_queue.enqueue(item)

            if isinstance(item, list):
                item_index = cast(tuple[int, int], item_index)
                self.queue_msg = await edit_or_send(ctx, self.queue_msg,
                    embed=embedq(f'{EmojiStr.inbox} Added {len(item)} items to the queue, from #{item_index[0] + 1} to #{item_index[1] + 1}.'))

            if (not self.voice_client.is_playing()) and (queue_was_empty):
                log.info('Voice client is not playing and the queue is empty, going to try playing...')
                starting_msg = await ctx.send(embed=embedq('Starting...'))
                await self.advance_queue(ctx)
                starting_msg = await starting_msg.delete()
            else:
                if isinstance(item, QueueItem):
                    self.queue_msg = await edit_or_send(ctx, self.queue_msg,
                        embed=embedq(f'{EmojiStr.inbox} Added {item.info.title} to the queue at spot #{cast(int, item_index) + 1}'))

        # Using -play alone with no args should resume the bot if we're paused
        if not queries:
            if self.voice_client.is_paused():
                log.debug('Player is paused; resuming...')
                self.voice_client.resume()
                await ctx.send(embed=embedq(f'{EmojiStr.play} Player is resuming.'))
                self.pause_duration = time.time() - self.paused_at
            elif (not self.voice_client.is_playing()) and (self.media_queue != []):
                await ctx.send(embed=embedq(f'{EmojiStr.play} Starting queue...'))
                await self.advance_queue(ctx, skipping=True)
            else:
                await ctx.send(embed=embedq(f'{EmojiStr.cancel} No URL or search terms given.'))
            return

        # If we have queries, start sorting them
        url_strings: list[str] = []
        plain_strings: list[str] = []

        for item in queries:
            (url_strings if item.startswith('https://') else plain_strings).append(item)
            if url_strings and plain_strings:
                log.debug('Both URLs and plain text detected; cancelling.')
                await ctx.send(f'{EmojiStr.cancel} URLs and plain-text search terms can\'t be used at the same time.')
                return

        # We now have only queries of either one text search, or one or more URLs
        async with ctx.typing():
            log.info('Searching...')
            if self.queue_msg:
                self.queue_msg = await self.queue_msg.delete()
            self.queue_msg = await ctx.send(embed=embedq('Searching...'))

            #region play: PLAIN TEXT
            if plain_strings:
                search_query: str = ' '.join(plain_strings)
                log.debug('Using plain-text search: %s', search_query)
                top = media.search_ytmusic_text(search_query)

                if cfg.USE_TOP_MATCH:
                    log.debug('USE_TOP_MATCH on.')
                    if top['songs']:
                        log.debug('Queueing top song...')
                        await play_or_enqueue(QueueItem(top['songs'][0], ctx.author)) # pylint: disable=unsubscriptable-object
                        return
                    elif top['videos']:
                        log.debug('Queueing top video...')
                        await play_or_enqueue(QueueItem(top['videos'][0], ctx.author)) # pylint: disable=unsubscriptable-object
                        return
                    else:
                        await ctx.send(embed=embedq(f'{EmojiStr.cancel} No close matches could be found.'))
                        return

                choice_embed = Embed(color=cfg.EMBED_COLOR, title='Please choose a search result to queue...')

                def assemble_choices(target_embed: Embed, info_list: list, name_list: list[str]) -> tuple[dict, Embed]:
                    options: dict = {}
                    position: int = 0
                    for item, name in zip(info_list, name_list):
                        if item:
                            position += 1
                            target_embed.add_field(name=f'Top {name} result:',
                                value=EmojiStr.num[position] + f' **{item[0].title}**, *{item[0].artist}*')
                            options[position] = item[0]
                    return options, target_embed

                choice_options, choice_embed = assemble_choices(choice_embed, [top['songs'], top['videos'], top['albums']], ['song', 'video', 'album'])

                choice_prompt = await ctx.send(embed=choice_embed)
                choice = await prompt_for_choice(self.bot, ctx, choice_prompt, choice_nums=len(choice_options), result_msg=self.queue_msg)
                self.queue_msg = None
                if choice == 0:
                    return

                choice = choice_options[choice]
                await play_or_enqueue(QueueItem(choice, ctx.author) if not choice.contents else QueueItem.from_list(choice.contents, ctx.author))
                return
            #endregion play: PLAIN TEXT

            #region play: FROM URL
            assert (not plain_strings) and (url_strings)

            if len(url_strings) > cfg.MAX_CONSECUTIVE_URLS:
                log.debug('Cancelling play command: too many consecutive URLs.')
                await ctx.send(embed=embedq(f'{EmojiStr.cancel} Too many URLs provided. (Max: {cfg.MAX_CONSECUTIVE_URLS})'))
                return

            # Does Spotify even use spotify.link URLs anymore? I can barely test this because I can't seem to get one now
            url_strings = [requests.get(u, timeout=1).url if u.startswith('https://spotify.link') else u for u in url_strings]

            if len(url_strings) > 1 and any(re.findall(r"(playlist|album|sets)", link) for link in url_strings):
                log.debug('Cancelling play command: album/playlist URL present in a set of URLs.')
                await ctx.send(embed=embedq(f'{EmojiStr.cancel} Albums or playlists must be queued on their own.',
                    'Multi-URL queueing is allowed only for single tracks.'))
                return

            # Handle playlists, albums
            if re.findall(r"(playlist|album|sets)", url_strings[0]):
                if not cfg.ALLOW_MEDIALISTS:
                    await ctx.send(embed=embedq(EmojiStr.cancel + ' Queueing playlists/albums is disabled.',
                        'This can be edited in the bot\'s configuration.'))
                    return
                log.debug('URL looks like a playlist or an album.')
                # Because of the previous checks we know this has to only be one URL, no need to keep the list
                url = url_strings[0]
                media_list: Optional[media.PlaylistInfo | media.AlbumInfo] = None

                if re.findall(r"https://(?:music\.|www\.|)youtube\.com/playlist\?list=", url):
                    # Convert to a normal YouTube playlist URL because dealing with YTMusic playlists/albums are a hassle
                    media_list = media.PlaylistInfo.from_ytdl(url.replace('music.', 'www.'))
                elif url.startswith('https://open.spotify.com/album/'):
                    if not media.sp:
                        await ctx.send(embed=CommonMsg.spotify_functions_unavailable())
                        return
                    media_list = media.AlbumInfo.from_spotify_url(url)
                elif url.startswith('https://open.spotify.com/playlist/'):
                    if not media.sp:
                        await ctx.send(embed=CommonMsg.spotify_functions_unavailable())
                        return
                    media_list = media.PlaylistInfo.from_spotify_url(url)
                elif re.findall(r"https://soundcloud\.com/\w+/sets/", url):
                    media_list = media.soundcloud_set(url)
                elif re.findall(r"https://\w+\.bandcamp\.com/album/", url):
                    media_list = media.AlbumInfo.from_other(url)
                else:
                    media_list = media.PlaylistInfo.from_other(url)

                # Final checks
                if isinstance(media_list, media.AlbumInfo) and (len(media_list.contents) > cfg.MAX_ALBUM_LENGTH):
                    await self.queue_msg.edit(embed=embedq(f'{EmojiStr.cancel} Album is too long.',
                        f'Current limit is set to {cfg.MAX_ALBUM_LENGTH}.'))
                    return
                if isinstance(media_list, media.PlaylistInfo) and (len(media_list.contents) > cfg.MAX_PLAYLIST_LENGTH):
                    await self.queue_msg.edit(embed=embedq(f'{EmojiStr.cancel} Playlist is too long.',
                        f'Current limit is set to {cfg.MAX_PLAYLIST_LENGTH}.'))
                    return

                if isinstance(media_list, media.AlbumInfo) and media_list.source == media.SPOTIFY:
                    # Find a YTMusic equivalent album if we have a Spotify album
                    log.debug('Trying to match Spotify album to YouTube Music...')
                    await self.queue_msg.edit(embed=embedq('Trying to match this Spotify album with a YouTube Music equivalent...',
                        'This can take a few seconds...'))
                    if match_result := media.match_ytmusic_album(media_list, threshold=50):
                        yt_album = match_result[0]
                        await self.queue_msg.edit(embed=embedq('A possible match was found. Queue this album?') \
                            .add_field(name=yt_album.album_name, value=yt_album.artist).set_thumbnail(url=yt_album.thumbnail))

                        if await prompt_for_choice(self.bot, ctx, prompt_msg=self.queue_msg, yesno=True, delete_prompt=False) == 1:
                            media_list = yt_album
                        else:
                            return
                    else:
                        await self.queue_msg.edit(embed=embedq(f'{EmojiStr.cancel} Couldn\'t find any close matches for this album.',
                            'Try using a source other than Spotify, if possible.'))
                        return

                # If we've reached here, something was successfully found and can be queued without issue
                await play_or_enqueue(QueueItem.from_list(media_list.contents, ctx.author))
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
                        if not media.sp:
                            await ctx.send(embed=CommonMsg.spotify_functions_unavailable())
                            return
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
        """Cancels the command if a voice connection wasn't found, and the command isn't allowed to auto connect."""
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
        return EmojiStr.repeat_one + ' ' if self.media_queue.is_looping else ''

    def embed_now_playing(self, show_elapsed: bool=True) -> Embed:
        """Constructs and returns the "Now playing" message embed.

        @show_elapsed: Show the elapsed time alongside the track length, i.e. "1:02 / 2:56"
        """
        item = cast(QueueItem, self.current_item)
        elapsed_hms: str = cast(str, seconds_to_hms(self.audio_time_elapsed))
        length_hms: Optional[str] = item.info.length_hms(format_zero=False)
        submitter_text: str = self.get_queued_by_text(cast(Member, item.queued_by))
        loop_icon: str = self.get_loop_icon()

        timestamp: str = f'[{elapsed_hms} / {length_hms or '?'}]' if show_elapsed else f'[{length_hms}]' if length_hms else ''

        embed = Embed(title=f'{loop_icon}{EmojiStr.play} Now playing: {item.info.title} {timestamp}',
            description=f'Link: {item.info.url}{submitter_text}', color=cfg.EMBED_COLOR).set_thumbnail(url=item.info.thumbnail)
        return embed

    async def advance_queue(self, ctx: commands.Context, skipping: bool=False):
        """Attempts to advance forward in the queue, if the bot is clear to do so.
        Set to run whenever the audio player finishes its current item."""
        if not self.voice_client.is_connected():
            return

        if (not self.advance_lock) and (skipping or not self.voice_client.is_playing()):
            log.debug('Locking...')
            self.advance_lock = True
            try:
                if self.player and ((not self.media_queue.is_looping) or (self.media_queue.is_looping and skipping)):
                    if self.player.filepath not in self.files_to_del:
                        self.files_to_del.append(self.player.filepath)
                        log.debug('File marked for deletion: %s', self.player.filepath)
                    for n, file in enumerate(self.files_to_del):
                        try:
                            os.remove(file)
                            self.files_to_del.pop(n)
                            log.debug('Removed file: %s', file)
                        except PermissionError:
                            log.debug('Permission error prevented removal of file: %s', file)
                        except FileNotFoundError:
                            log.debug('File not found: %s', file)
                self.player = None

                self.previous_item = self.current_item
                self.skip_votes_placed.clear()
                if self.media_queue.is_looping:
                    log.debug('Looping is enabled, and we %s skipping.', 'ARE' if skipping else 'are NOT')
                    await self.make_and_start_player(self.media_queue.pop(0) if skipping \
                        else (self.current_item or self.media_queue.pop(0)), ctx)
                elif not self.media_queue:
                    self.voice_client.stop()
                else:
                    item_index = 0 if not self.media_queue.roulette_mode else random.randint(0, len(self.media_queue) - 1)
                    await self.make_and_start_player(self.media_queue.pop(item_index), ctx)
            finally:
                # finally statement makes sure we still unlock if an error occurs
                log.debug('Tasks finished; unlocking...')
                self.advance_lock = False
            if self.after_advance_queue:
                self.after_advance_queue()
            self.after_advance_queue = None
        elif self.advance_lock:
            log.debug('Attempted call while locked; ignoring...')

    async def make_and_start_player(self, item: QueueItem, ctx: commands.Context):
        """Create a new player from the given `QueueItem` and starts playing audio.
        Handles matching individual Spotify tracks to YTMusic.

        Use `advance_queue()` to attempt moving the queue along, do not use this function directly."""
        log.info('Trying to start playing...')

        def skip_after_return() -> None:
            self.after_advance_queue = lambda: asyncio.run_coroutine_threadsafe(self.advance_queue(ctx, skipping=True), self.bot.loop)

        self.audio_time_elapsed = 0.0

        if item != self.previous_item:
            if self.previous_item:
                self.play_history.appendleft(self.previous_item)

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
                            '\n'.join([EmojiStr.num[n + 1] + f' **{track.title}**\n*{track.artist}*' for n, track in enumerate(matches)])))
                        choice = await prompt_for_choice(self.bot, ctx,
                            prompt_msg=prompt_msg, choice_nums=len(matches), result_msg=self.queue_msg)
                        if isinstance(choice, int) and choice != 0:
                            item.info = matches[choice - 1]
                        else:
                            await self.advance_queue(ctx)
                            return
                if isinstance(matches, media.TrackInfo):
                    item.info = matches

            if (item.info.length_seconds == 0) and (cfg.DURATION_LIMIT_SECONDS != 0):
                prompt_msg = await ctx.send(embed=embedq(f'The duration of "{item.info.title}" couldn\'t be retrieved, so ' +
                    'it can\'t be checked against the duration limit. Play anyway?'))
                if await prompt_for_choice(self.bot, ctx, prompt_msg=prompt_msg, yesno=True) == 0:
                    skip_after_return()
                    return

        try:
            log.debug('Creating YTDLSource...')
            self.player = await YTDLSource.from_url(item.info.url, loop=self.bot.loop, stream=False)
        except yt_dlp.utils.DownloadError:
            log.info('Download error occurred; skipping this item...')
            await ctx.send(embed=embedq('This video is unavailable.', f'URL: {item.info.url}'))
            skip_after_return()
            return

        if not self.player.filepath.is_file():
            log.info('Player filepath was not found, skipping...')
            await ctx.send(embed=embedq('File is missing, skipping this item.',
                'The video file likely went over the filesize limit. Check the logs for details.'))
            skip_after_return()
            return

        self.voice_client.stop()
        log.info('Starting audio playback...')
        self.voice_client.play(self.player, after=lambda e: asyncio.run_coroutine_threadsafe(self.handle_player_stop(ctx), self.bot.loop))
        self.current_item = item

        if item != self.previous_item:
            # Don't re-send a now playing message if we're just looping this track
            self.now_playing_msg = await ctx.send(embed=self.embed_now_playing(show_elapsed=False))

        if self.queue_msg:
            self.queue_msg = await self.queue_msg.delete(delay=1.0)

    async def handle_player_stop(self, ctx):
        """Normally just directs to `advance_queue()`, but handles some small additional logic
        specifically to be used as the `after` argument for a player source. Should not be used alone."""
        log.debug('Player has finished.')
        await self.advance_queue(ctx)
