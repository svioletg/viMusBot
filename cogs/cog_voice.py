"""Cog file for voice chat operations."""

# Standard imports
import asyncio
from logging import Logger
from typing import Any, Optional

# External imports
from discord import Embed, Member, VoiceClient, VoiceState, PCMVolumeTransformer, Message, FFmpegPCMAudio
from discord.errors import NotFound
from discord.ext import commands
from yt_dlp import YoutubeDL
from yt_dlp.utils import DownloadError

# Local imports
from utils import media
from cogs.shared import INACTIVITY_TIMEOUT, USE_TOP_MATCH, embedq

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
    def __init__(self, info: media.TrackInfo, queued_by: Member):
        self.info = info
        self.queued_by = queued_by

    @staticmethod
    def generate_from_list(playlist: list[media.TrackInfo] | media.PlaylistInfo, user: Member) -> list | tuple[None, Exception]:
        """Creates a list of QueueItem instances from a valid playlist

        @playlist: Either a URL to a SoundCloud or ytdl-compatible playlist, or a list of Spotify tracks
        @user: A discord Member object of the user who queued the playlist
        """
        objlist = []
        # Will be a list if origin is Spotify, or if multiple URLs were sent with the command
        if isinstance(playlist, (list, tuple)):
            failures = []
            for item in playlist:
                if isinstance(item, str) and 'open.spotify.com' in item:
                    url = item
                    item = media.spotify_track(item)
                    if isinstance(item, tuple):
                        log.info(f'Failed to download video: {item[1]}')
                        failures.append(url)
                        continue
                
                if isinstance(item, dict) and 'open.spotify.com' in item['url']:
                    objlist.append(QueueItem(item['url'], user, title=item['title'], duration=item.get('duration', 0)))
                else:
                    # Having the list part of the URL causes issues with getting info back
                    item = item.split('&list=')[0]
                    
                    try:
                        info = ytdl.extract_info(item, download=False)
                    except yt_dlp.utils.DownloadError as e:
                        log.info(f'Failed to download video: {e}')
                        failures.append(item)
                        continue
                    objlist.append(QueueItem(info['webpage_url'], user, title=info['title'], duration=info.get('duration', 0)))
            return objlist, failures
        else:
            # Anything youtube-dl natively supports is probably a link
            if 'soundcloud.com' in playlist:
                # SoundCloud playlists have to be processed differently
                try:
                    playlist_entries = media.soundcloud_set(playlist)
                except TypeError as e:
                    log.info(f'Failed to retrieve SoundCloud playlist: {e}')
                    return None, e
                objlist = [QueueItem(item.permalink_url, user, title=item.title, duration=round(item.duration/1000)) for item in playlist_entries]
            else:
                try:
                    playlist_entries = ytdl.extract_info(playlist, download=False)
                except yt_dlp.utils.DownloadError as e:
                    log.info(f'Failed to download playlist: {e}')
                    return None, e
                objlist = [QueueItem(item['url'], user, title=item['title'], duration=item.get('duration', 0)) for item in playlist_entries['entries']]
            return objlist

class MediaQueue:
    """Manages a media queue, keeping track of what's currently playing, what has previously played, whether looping is on, etc."""
    def __init__(self):
        self.__queue_list: list[QueueItem] = []
        self.is_looping: bool = False
        self.now_playing: Optional[YTDLSource] = None
        self.last_played: Optional[YTDLSource] = None
        self.current_item: Optional[QueueItem] = None
        self.now_playing_msg: Optional[Message] = None
        self.queue_msg: Optional[Message] = None

    def clear(self):
        """Clears the queue list."""
        self.__queue_list.clear()
    
    def queue(self, to_queue: QueueItem | list[QueueItem]):
        """Takes either a single `QueueItem` or a list of them, and queues them."""
        if not isinstance(to_queue, list):
            self.__queue_list.append(to_queue)
            return

        for item in to_queue:
            self.__queue_list.append(item)

class Voice(commands.Cog):
    """Handles voice and music-related tasks."""

    def __init__(self, bot: commands.bot.Bot, logger: Logger):
        self.bot = bot
        self.logger = logger
        self.voice_client: Optional[VoiceClient] = None
        self.media_queue = MediaQueue()
    
    async def play_item(self, item: QueueItem, ctx: commands.Context):
        # skip_votes = []

        audio_time_elapsed = paused_at = paused_for = 0

        last_played = now_playing

        try:
            if npmessage is not None:
                await npmessage.delete()
        except discord.errors.NotFound:
            log.debug('Now-playing message wasn\'t found, ignoring and continuing...')
        
        log.info('Trying to start playing...')

        # Check if we need to match a Spotify link
        if 'open.spotify.com' not in item.url:
            url = item.url
        else:
            log.info('Trying to match Spotify track...')
            npmessage = await ctx.send(embed=embedq(f'Spotify link detected, searching YouTube...','Please wait, this may take a while!\nIf you think the bot\'s become stuck, use the skip command.'))
            spyt = media.spyt(item.url)
            # TODO: unsure isn't a thing anymore, this all need redoing
            log.info('Checking if unsure...')
            if isinstance(spyt, tuple) and spyt[0] == 'unsure':
                # This indicates no match was found
                log.info('spyt returned unsure.')
                # Remove the warning, no longer needed
                spyt = spyt[1]
                # Shorten to {limit} results
                limit = 5
                spyt = dict(list(spyt.items())[:limit])
                if USE_TOP_MATCH:
                    # Use first result if that's set in config
                    spyt = spyt[0]
                else:
                    # Otherwise, prompt the user with choice
                    embed = Embed(title='No exact match found; please choose an option.',description=f'Select the number with reactions or use {emoji["cancel"]} to cancel.',color=EMBED_COLOR)
                    
                    for i in spyt:
                        title = spyt[i]['title']
                        url = spyt[i]['url']
                        artist = spyt[i]['artist']
                        album = spyt[i]['album']
                        if artist=='': embed.add_field(name=f'{i+1}. {title}',value=url,inline=False)
                        else: embed.add_field(name=f'{i+1}. {title}\nby {artist} - {album}',value=url,inline=False)

                    prompt = await ctx.send(embed=embed)
                    choice = await prompt_for_choice(ctx, prompt, len(spyt))
                    if choice is None:
                        await advance_queue(ctx)
                        return
                    spyt = spyt[choice-1]
            url = spyt['url']
            item.url = url
            await npmessage.edit(embed=embedq('Match found! Playing...'))

        current_item = item

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

        if item.duration is not None:
            if item.duration == 0:
                item.duration = duration_from_url(item.url)
            now_playing.duration = item.duration
        else:
            try:
                now_playing.duration = pytube.YouTube(now_playing.weburl).length
            except Exception as e:
                log.info(f'Falling back on yt-dlp. (Cause: {traceback.format_exception(e)[-1]})')
                try:
                    now_playing.duration = ytdl.extract_info(now_playing.weburl, download=False)['duration']
                except Exception as e:
                    log.info(f'ytdl duration extraction failed, likely a direct file link. (Cause: {traceback.format_exception(e)[-1]})')
                    log.info(f'Attempting to retrieve URL through FFprobe...')
                    ffprobe_command = f'ffprobe {url} -v quiet -show_entries format=duration -of csv=p=0'.split(' ')
                    now_playing.duration = float(subprocess.check_output(ffprobe_command).decode('utf-8').split('.')[0])

        now_playing.duration_stamp = timestamp_from_seconds(now_playing.duration)

        voice.stop()
        voice.play(now_playing, after=lambda e: asyncio.run_coroutine_threadsafe(advance_queue(ctx), bot.loop))
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

    advance_lock = False

    async def advance_queue(ctx: commands.Context, skip: bool=False):
        """Attempts to advance forward in the queue, if the bot is clear to do so."""
        # Triggers every time the player finishes
        global advance_lock
        if not advance_lock and (skip or not voice.is_playing()):
            log.debug('Locking...')
            advance_lock = True

            try:
                if not skip and loop_this and current_item is not None:
                    media_queue.get(ctx).insert(0, current_item)

                if media_queue.get(ctx) == []:
                    voice.stop()
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
