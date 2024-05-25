"""Cog file for voice chat operations."""

# Standard imports
import asyncio
import logging
import time
from typing import Optional, Self, TypeVar, cast

# External imports
from discord import (Embed, FFmpegPCMAudio, Member, Message,
                     PCMVolumeTransformer, User, VoiceClient, VoiceState)
from discord.errors import NotFound
from discord.ext import commands
from requests import delete
from yt_dlp import YoutubeDL
from yt_dlp.utils import DownloadError

# Local imports
from cogs.shared import (EMBED_COLOR, EMOJI, INACTIVITY_TIMEOUT, USE_TOP_MATCH, command_aliases,
                         embedq, is_command_enabled, prompt_for_choice)
from utils import media

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
    def __init__(self, source, *, data, volume=0.5):
        super().__init__(source, volume)

        self.data = data

        self.title = data.get('title')
        self.url = data.get('url')
        self.id = data.get('id')
        self.src = data.get('extractor')

    @classmethod
    async def from_url(cls, url, *, loop=None, stream=False):
        loop = loop or asyncio.get_event_loop()
        data = await loop.run_in_executor(None, lambda: ytdl.extract_info(url, download=not stream))

        try:
            if 'entries' in data: # type: ignore
                # take first item from a playlist
                data = data['entries'][0] # type: ignore
        except Exception as e:
            raise e

        filename = data['url'] if stream else ytdl.prepare_filename(data) # type: ignore
        src = filename.split('-#-')[0]
        id = filename.split('-#-')[1]
        return cls(FFmpegPCMAudio(filename, **ffmpeg_options), data=data) # type: ignore

class QueueItem:
    """Items which are to be placed inside of a `MediaQueue`, and nothing else. Holds a `TrackInfo` and the user that queued it."""
    def __init__(self, info: media.TrackInfo, queued_by: User | Member):
        self.info = info
        self.queued_by = queued_by

    @classmethod
    def from_list(cls, playlist: list[media.TrackInfo], queued_by: User | Member) -> list[Self]:
        """Creates a list of individual `QueueItem` instances from a valid playlist or album.

        @playlist: Either a URL to a SoundCloud or ytdl-compatible playlist, or a list of Spotify tracks
        @queued_by: A discord Member object of the user who queued the playlist
        """
        return [cls(item, queued_by) for item in playlist]

class MediaQueue(list):
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
        if not isinstance(item, QueueItem):
            raise ValueError('Attempt to append a non-QueueItem to a MediaQueue.')
        super().extend(item)

    def queue(self, to_queue: QueueItem | list[QueueItem]) -> int | tuple[int, int]:
        """Takes either a single `QueueItem` or a list of them, and queues them."""
        start: int = len(self)
        if isinstance(to_queue, list):
            self.extend(to_queue)
            end: int = len(self)
            return start, end
        else:
            self.append(to_queue)
            return start

class Voice(commands.Cog):
    """Handles voice and music-related tasks."""

    def __init__(self, bot: commands.bot.Bot):
        self.bot = bot
        self.voice_client: Optional[VoiceClient] = None
        self.media_queue = MediaQueue()
        self.advance_lock: bool = False
        self.paused_at: float = 0.0
        self.pause_duration: float = 0.0
        self.audio_time_elapsed: float = 0.0
    
    @commands.command(aliases=command_aliases('leave'))
    @commands.check(is_command_enabled)
    async def leave(self, ctx: commands.Context):
        """Leaves the currently connected to voice channel."""
        if self.voice_client.is_connected:
            await ctx.send(embed=embedq('Leaving voice...'))
            await self.voice_client.disconnect()
    
    @commands.command(aliases=command_aliases('play'))
    @commands.check(is_command_enabled)
    async def play(self, ctx: commands.Context, *queries: str):
        """Adds a link to the queue. Plays immediately if the queue is empty.
        
        @queries: Can either be a single URL string, a list of URL strings, or a non-URL string for text searching
        """
        async def play_or_enqueue(item: QueueItem | list[QueueItem], queue_msg: Message):
            """Adds the given `QueueItem` to the media queue. If the queue is empty, the item will attempt to play immediately. Otherwise, the item is appended to the queue.

            @item: Either a single `QueueItem` or a list of `QueueItem`s to queue up.
            """
            log.info('Adding to queue...')
            item_index = self.media_queue.queue(item)
            if not self.voice_client.is_playing() and not self.media_queue:
                log.info('Voice client is not playing and the queue is empty, going to try playing...')
                await self.advance_queue(ctx)
            else:
                if isinstance(item, list):
                    item_index = cast(tuple[int, int], item_index)
                    await queue_msg.edit(embed=embedq(f'Added {len(item)} items to the queue, from #{item_index[0]} to #{item_index[1]}.'))
                else:
                    await queue_msg.edit(embed=embedq(f'Added {item.info.title} to the queue at spot #{item_index}'))
        
        # Using -play alone with no args should resume the bot if we're paused
        if not queries:
            if self.voice_client.is_paused():
                self.voice_client.resume()
                await ctx.send(embed=embedq('Player is resuming.'))
                self.pause_duration = time.time() - self.paused_at
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
            await ctx.send('URLs and plain search terms can\'t be used at the same time.')
            return

        # We now have only queries of either one text search, or one or more URLs
        async with ctx.typing():
            queue_msg = await ctx.send(embed=embedq('Searching...'))
            #region play: PLAIN TEXT
            if plain_strings:
                text_search: str = ' '.join(plain_strings)
                top_songs, top_videos, top_albums = map(media.search_ytmusic_text(text_search).get, ('songs', 'videos', 'albums'))

                if USE_TOP_MATCH:
                    if top_songs:
                        await play_or_enqueue(QueueItem(top_songs[0], ctx.author), queue_msg)
                        return
                    if top_videos:
                        await play_or_enqueue(QueueItem(top_videos[0], ctx.author), queue_msg)
                        return

                    await ctx.send(embed=embedq('No close matches could be found.'))
                    return

                choice_embed = Embed(color=EMBED_COLOR, title='Please choose a search result to queue...')
                choice_options = []
                position: int = 1
                # TODO: Probably can be condensed
                if top_songs:
                    choice_embed.add_field(name='Top song result:',
                        value=EMOJI['num'][position] + f'**{top_songs[0].title}** | *{top_songs[0].artist}*')
                    choice_options[position] = top_songs[0]
                    position += 1
                if top_videos:
                    choice_embed.add_field(name='Top video result:',
                        value=EMOJI['num'][position] + f'**{top_videos[0].title}** | *{top_videos[0].artist}*')
                    choice_options[position] = top_videos[0]
                    position += 1
                if top_albums:
                    choice_embed.add_field(name='Top album result:',
                        value=EMOJI['num'][position] + f'**{top_albums[0].title}** | *{top_albums[0].artist}*')
                    choice_options[position] = top_albums[0]
                    position += 1

                choice_prompt = await ctx.send(embed=choice_embed)
                choice = await prompt_for_choice(self.bot, ctx, choice_prompt, choice_nums=position)

                if isinstance(choice, TimeoutError):
                    await queue_msg.edit(embed=embedq(f'{EMOJI['cancel']} Choice prompt timed out, nothing queued.'))
                    return
                if isinstance(choice, ValueError):
                    await queue_msg.edit(embed=embedq(f'{EMOJI['cancel']} Too many options were provided to the prompt.',
                        'If you\'re seeing this message, this is probably a bug!'))
                    return

                choice = choice_options[choice]

                await play_or_enqueue(QueueItem(choice, ctx.author) if not choice.contents else QueueItem.from_list(choice.contents, ctx.author),
                    queue_msg)
                return
            #endregion play: PLAIN TEXT
            if url_strings:
                # TODO: Implement! This needs to handle...
                # [ ] Spotify track links
                # [ ] Spotify album links
                # [ ] Spotify playlist links
                # [ ] SoundCloud track links
                # [ ] SoundCloud set links
                # [ ] YouTube video links
                # [ ] YouTube playlist links
                # [ ] YouTube Music song links
                # [ ] YouTube Music album links
                pass

    async def play_item(self, item: QueueItem, ctx: commands.Context):
        # skip_votes = []

        last_played = now_playing

        try:
            if npmessage is not None:
                await npmessage.delete()
        except discord.errors.NotFound:
            log.debug('Now-playing message wasn\'t found, ignoring and continuing...')
        
        log.info('Trying to start playing...')

        # Start the player with retrieved URL
        try:
            player = await YTDLSource.from_url(item.url, loop=bot.loop, stream=False)
        except yt_dlp.utils.DownloadError as e:
            log.info(f'Failed to download video: {e}')
            await ctx.send(embed=embedq('This video is unavailable.', url))
            await advance_queue(ctx)
            return

        now_playing = player
        now_playing.weburl = url
        now_playing.user = item.queued_by

        now_playing.duration_stamp = timestamp_from_seconds(now_playing.duration)

        self.voice_client.stop()
        self.voice_client.play(now_playing, after=lambda e: asyncio.run_coroutine_threadsafe(advance_queue(ctx), bot.loop))
        audio_start_time = time.time()
        if npmessage is not None:
            try:
                await npmessage.delete()
            except:
                # Sometimes this causes a 404 error and prevents a new "Now playing" message to show
                # Just ignoring the error sends a message properly so, sure
                pass

        try:
            await qmessage.delete()
        except Exception as e:
            pass

        submitter_text = get_queued_by_text(item.queued_by)
        embed = discord.Embed(title=f'{get_loop_icon()}Now playing: {now_playing.title} [{now_playing.duration_stamp}]',description=f'Link: {url}{submitter_text}',color=EMBED_COLOR)
        npmessage = await ctx.send(embed=embed)

        if last_played is not None:
            for i in glob.glob(f'*-#-{last_played.ID}-#-*'):
                # Delete last played file
                try:
                    log.debug(f'Removing file: {i}')
                    os.remove(i)
                except PermissionError as e:
                    log.debug(f'Cannot remove; the file is likely in use.')

    async def advance_queue(self, ctx: commands.Context, skip: bool=False):
        """Attempts to advance forward in the queue, if the bot is clear to do so. Set to run whenever the audio player finishes its current item."""
        if not self.advance_lock and (skip or not self.voice_client.is_playing()):
            log.debug('Locking...')
            advance_lock = True

            try:
                if not skip and self.media_queue.is_looping and current_item is not None:
                    media_queue.get(ctx).insert(0, current_item)

                if media_queue.get(ctx) == []:
                    self.voice_client.stop()
                else:
                    next_item = media_queue.get(ctx).pop(0)
                    await play_item(next_item, ctx)
                
                log.debug('Tasks finished; unlocking...')
                advance_lock = False
            except Exception as e:
                log.error(e)
                log.debug('Error encountered; unlocking...')
                advance_lock = False
        elif advance_lock:
            log.debug('Attempted call while locked; ignoring...')

    # TODO: This could have a better name
    def get_loop_icon() -> str:
        return emoji['repeat']+' ' if loop_this else ''

    @commands.Cog.listener()
    async def on_voice_state_update(self, member: Member, before: VoiceState):
        """Listener for the voice state update event. Currently handles inactivity timeouts and tracks how long audio has been playing."""
        if not member.id == self.bot.user.id:
            return
        elif before.channel is None:
            # Disconnect after set amount of inactivity
            if INACTIVITY_TIMEOUT == 0:
                return
            timeout_counter = 0
            while True:
                await asyncio.sleep(1)
                timeout_counter += 1
                if self.voice_client.is_playing() and not self.voice_client.is_paused():
                    timeout_counter = 0
                    # global audio_time_elapsed
                    audio_time_elapsed += 1

                if timeout_counter == INACTIVITY_TIMEOUT*60:
                    self.logger.info('Leaving voice due to inactivity.')
                    await self.voice_client.disconnect()
                if not self.voice_client.is_connected():
                    self.logger.debug('Voice doesn\'t look connected, waiting three seconds...')
                    await asyncio.sleep(3)
                    if not self.voice_client.is_connected():
                        self.logger.debug('Still disconnected. Setting `voice` to None...')
                        self.voice_client = None
                        break
                    else:
                        self.logger.debug('Voice looks connected again. Continuing as normal.')
