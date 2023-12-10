print('Getting ready...')

# Import sys out of order to print the Python version, for troubleshooting
import sys

print('Python '+sys.version)

# Continue with remaining imports
import asyncio
import glob
import importlib
import logging
import math
import os
import random
import requests
import subprocess
import sys
import time
import traceback
import urllib.request
from inspect import currentframe
from pathlib import Path

import colorama
import discord
import pytube
import regex as re
import yaml
import yt_dlp
from benedict import benedict
from colorama import Back, Fore, Style
from discord.ext import commands
from pretty_help import PrettyHelp

print('Checking for config file...')

if not Path('config_default.yml').is_file():
    print('config_default.yml not found; downloading latest version from remote...')
    urllib.request.urlretrieve('https://raw.githubusercontent.com/svioletg/viMusBot/master/config_default.yml','config_default.yml')

if not Path('config.yml').is_file():
    print('config.yml does not exist; creating blank config.yml...')
    with open('config.yml', 'w') as f:
        f.write('')

with open('config_default.yml','r') as f:
    config_default = benedict(yaml.safe_load(f))

with open('config.yml','r') as f:
    config = benedict(yaml.safe_load(f))

print('Importing local packages...')
# Import local files after main packages, and after validating config
import customlog
import spoofy
import update
from palette import Palette

_here = Path(__file__).name

# Represents the version of the overall project, not just this file
with open('version.txt','r') as f:
    VERSION = f.read().strip()

# Setup discord logging
handler = logging.FileHandler(filename='discord.log', encoding='utf-8', mode='w')
discord.utils.setup_logging(handler=handler, level=logging.INFO, root=False)

# Setup bot logging
colorama.init(autoreset=True)
plt = Palette()

last_logtime = time.time()

def log(msg: str, verbose: bool=False):
    global last_logtime
    customlog.newlog(msg=msg, last_logtime=last_logtime, called_from=sys._getframe().f_back.f_code.co_name, verbose=verbose)
    last_logtime = time.time()

def log_traceback(error: BaseException):
    trace=traceback.format_exception(error)
    log(f'Full traceback below.\n\n{plt.error}{"".join(trace)}')

def log_line():
    cf = currentframe()
    print('@ LINE ', cf.f_back.f_lineno)

log(f'Running on version {VERSION}; checking for updates...')

update_check_result = update.check()

# Check for an outdated version.txt
if update_check_result[0] == False and update_check_result[1] == True:
    log(f'{plt.warn}There is a new release available.')
    current_tag = update_check_result[1]['current']
    latest_tag = update_check_result[1]['latest']['tag_name']
    log(f'Current: {plt.gold}{current_tag}{plt.reset} | Latest: {plt.lime}{latest_tag}')
    log('Use "update.py" to update.')
else:
    if VERSION.startswith('dev.'):
        log(f'{plt.yellow}NOTICE: You are running a development version.')
    else:
        log(f'{plt.lime}You are up to date.')

log('Changelog: https://github.com/svioletg/viMusBot/blob/master/changelog.md')

log('Parsing config...')

#region CONFIGURATION FROM YAML
PUBLIC             : bool = config.get('public', config_default['public'])
TOKEN_FILE_PATH    : str  = config.get('token-file', config_default['token-file'])
PUBLIC_PREFIX      : str  = config.get('prefixes.public', config_default['prefixes.public'])
DEV_PREFIX         : str  = config.get('prefixes.developer', config_default['prefixes.developer'])
EMBED_COLOR        : int  = int(config.get('embed-color', config_default['embed-color']), 16)
INACTIVITY_TIMEOUT : int  = config.get('inactivity-timeout', config_default['inactivity-timeout'])
CLEANUP_EXTENSIONS : list = config.get('auto-remove', config_default['auto-remove'])
DISABLED_COMMANDS  : list = config.get('command-blacklist', config_default['command-blacklist'])

SHOW_USERS_IN_QUEUE      : bool = config.get('show-users-in-queue', config_default['show-users-in-queue'])
ALLOW_SPOTIFY_PLAYLISTS  : bool = config.get('allow-spotify-playlists', config_default['allow-spotify-playlists'])
USE_TOP_MATCH            : bool = config.get('use-top-match', config_default['use-top-match'])
USE_URL_CACHE            : bool = config.get('use-url-cache', config_default['use-url-cache'])
SPOTIFY_PLAYLIST_LIMIT   : int  = config.get('spotify-playlist-limit', config_default['spotify-playlist-limit'])
DURATION_LIMIT           : int  = config.get('duration-limit', config_default['duration-limit'])
MAXIMUM_CONSECUTIVE_URLS : int  = config.get('maximum-urls', config_default['maximum-urls'])

VOTE_TO_SKIP          : bool = config.get('vote-to-skip.enabled', config_default['vote-to-skip.enabled'])
SKIP_VOTES_TYPE       : str  = config.get('vote-to-skip.threshold-type', config_default['vote-to-skip.threshold-type'])
SKIP_VOTES_EXACT      : int  = config.get('vote-to-skip.threshold-exact', config_default['vote-to-skip.threshold-exact'])
SKIP_VOTES_PERCENTAGE : int  = config.get('vote-to-skip.threshold-percentage', config_default['vote-to-skip.threshold-percentage'])
skip_votes_needed = 0
skip_votes = []
#endregion

def is_command_enabled(ctx: commands.Context):
    return not ctx.command.name in DISABLED_COMMANDS

def get_aliases(command: str):
    return config.get(f'aliases.{command}', config_default.get(f'aliases.{command}', []))

# Clear out downloaded files
log('Removing previously downloaded media files...')
files = glob.glob('*.*')
to_remove = [f for f in files if Path(f).suffix in CLEANUP_EXTENSIONS]
for t in to_remove:
    os.remove(t)
del files, to_remove

def embedq(*args: str) -> discord.Embed:
    """Shortcut for making new embeds"""
    if len(args) == 1:
        return discord.Embed(title=args[0], color=EMBED_COLOR)
    elif len(args) == 2:
        return discord.Embed(title=args[0], description=args[1], color=EMBED_COLOR)

# For easier emoji usage
emoji = {
    'cancel':'❌',
    'confirm':'✅',
    'repeat':'🔁',
    'info':'ℹ️',
    'num':[
    '0️⃣',
    '1️⃣',
    '2️⃣',
    '3️⃣',
    '4️⃣',
    '5️⃣',
    '6️⃣',
    '7️⃣',
    '8️⃣',
    '9️⃣',
    '🔟',
    ],
}

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
    'source_address': '0.0.0.0',  # bind to ipv4 since ipv6 addresses cause issues sometimes
}

ytdl = yt_dlp.YoutubeDL(ytdl_format_options)

ffmpeg_options = {
    'options': '-vn',
}

class YTDLSource(discord.PCMVolumeTransformer):
    def __init__(self, source, *, data, volume=0.5):
        super().__init__(source, volume)

        self.data = data

        self.title = data.get('title')
        self.url = data.get('url')
        self.ID = data.get('id')
        self.src = data.get('extractor')

    @classmethod
    async def from_url(cls, url, *, loop=None, stream=False):
        loop = loop or asyncio.get_event_loop()
        data = await loop.run_in_executor(None, lambda: ytdl.extract_info(url, download=not stream))

        try:
            if 'entries' in data:
                # take first item from a playlist
                data = data['entries'][0]
        except Exception as e:
            raise e

        filename = data['url'] if stream else ytdl.prepare_filename(data)
        src = filename.split('-#-')[0]
        ID = filename.split('-#-')[1]
        return cls(discord.FFmpegPCMAudio(filename, **ffmpeg_options), data=data)

# Start bot-related events

#
#
# Define cogs
#
#

voice: discord.voice_client.VoiceClient = None

class General(commands.Cog):
    def __init__(self, bot: commands.bot.Bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_voice_state_update(self, member: discord.Member, before: discord.member.VoiceState, after):
        global voice
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
                if voice.is_playing() and not voice.is_paused():
                    timeout_counter = 0
                    global audio_time_elapsed
                    audio_time_elapsed += 1
                
                if timeout_counter == INACTIVITY_TIMEOUT*60:
                    log('Leaving voice due to inactivity.')
                    await voice.disconnect()
                if not voice.is_connected():
                    log('Voice doesn\'t look connected, waiting three seconds...', verbose=True)
                    # TODO: this seemed to work well in a live test! maybe adjust the timing a bit before release
                    await asyncio.sleep(3)
                    if not voice.is_connected():
                        log('Still disconnected. Setting `voice` to None...', verbose=True)
                        voice = None
                        break
                    else:
                        log('Voice looks connected again. Continuing as normal.', verbose=True)

    @commands.command()
    @commands.check(is_command_enabled)
    async def reloadspoofy(self, ctx):
        # Separated from the others for debug purposes
        global spoofy
        spoofy = importlib.reload(spoofy)
        log('Reloaded spoofy.py.')

    @commands.command()
    @commands.check(is_command_enabled)
    async def stream(self, ctx):
        log(voice.source)
        log(dir(voice.source))

    @commands.command(aliases=get_aliases('changelog'))
    @commands.check(is_command_enabled)
    async def changelog(self, ctx: commands.Context):
        """Returns a link to the changelog, and displays most recent version."""
        embed=discord.Embed(title='Read the changelog here: https://github.com/svioletg/viMusBot/blob/master/changelog.md',description=f'Current version: {VERSION}',color=EMBED_COLOR)
        await ctx.send(embed=embed)

    @commands.command(aliases=get_aliases('ping'))
    @commands.check(is_command_enabled)
    async def ping(self, ctx: commands.Context):
        """Test command."""
        await ctx.send('Pong!')
        embed=discord.Embed(title='Pong!',description='Pong!',color=EMBED_COLOR)
        await ctx.send(embed=embed)
        await ctx.send(embed=embedq('this is a test for', 'the extended embed function'))

    @commands.command(aliases=get_aliases('repository'))
    @commands.check(is_command_enabled)
    async def repository(self, ctx: commands.Context):
        """Returns the link to the viMusBot GitHub repository."""
        embed=discord.Embed(title='You can view the bot\'s code and submit bug reports or feature requests here.',description='https://github.com/svioletg/viMusBot\nA GitHub account is required to submit issues.',color=EMBED_COLOR)
        await ctx.send(embed=embed)


class Music(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # Playing music / Voice-related
    @commands.command(aliases=get_aliases('analyze'))
    @commands.check(is_command_enabled)
    async def analyze(self, ctx: commands.Context, spotifyurl: str):
        """Returns spotify API information regarding a track."""
        info = spoofy.spotify_track(spotifyurl)
        title = info['title']
        artist = info['artist']
        result = spoofy.analyze_track(spotifyurl)
        data = result[0]
        skip = result[1]
        # Assemble embed object
        embed = discord.Embed(title=f'Spotify data for {title} by {artist}', description='Things like key, tempo, and time signature are estimated, and therefore not necessarily accurate.', color=EMBED_COLOR)
        # Put key, time sig, and tempo at the top
        embed.add_field(name='Key',value=data['key'])
        data.pop('key')
        embed.add_field(name='Tempo',value=data['tempo'])
        data.pop('tempo')
        embed.add_field(name='Time Signature',value=data['time_signature'])
        data.pop('time_signature')

        # Add the rest
        for i in data:
            if i in skip:
                continue

            value=data[i]
            # Change decimals to percentages
            # Exclude loudness
            if type(data[i])==int or type(data[i])==float:
                if data[i]<1 and i!='loudness':
                    value=str(round(data[i]*100,2))+'%'

            value=str(value)
            embed.add_field(name=i.title(),value=value)
        await ctx.send(embed=embed)

    @commands.command(aliases=get_aliases('clear'))
    @commands.check(is_command_enabled)
    async def clear(self, ctx: commands.Context):
        """Clears the entire queue."""
        global media_queue
        media_queue.clear(ctx)
        await ctx.send(embed=embedq('Queue cleared.'))

    @commands.command(aliases=get_aliases('join'))
    @commands.check(is_command_enabled)
    async def join(self, ctx):
        """Joins the voice channel of the user."""
        # This actually just calls ensure_voice below,
        # this is only defined so that there's a command in Discord for it
        pass

    @commands.command(aliases=get_aliases('leave'))
    @commands.check(is_command_enabled)
    async def leave(self, ctx: commands.Context):
        """Disconnects the bot from voice."""
        global voice
        global media_queue
        media_queue.clear(ctx)
        log(f'Leaving voice channel: {ctx.author.voice.channel}')
        try:
            await voice.disconnect()
        except AttributeError:
            await ctx.send(embed=embedq('Not connected to voice.'))
        voice = None

    @commands.command(aliases=get_aliases('loop'))
    @commands.check(is_command_enabled)
    async def loop(self, ctx: commands.Context):
        """Toggles looping for the current track."""
        global loop_this
        # Inverts the boolean
        loop_this = not loop_this
        log(f'Looping {["disabled", "enabled"][loop_this]}.', verbose=True)
        await ctx.send(embed=embedq(f'{get_loop_icon()}Looping {["disabled", "enabled"][loop_this]}.'))

    @commands.command(aliases=get_aliases('move'))
    @commands.check(is_command_enabled)
    async def move(self, ctx: commands.Context, old: int, new: int):
        """Moves a queue item from <old> to <new>."""
        try:
            to_move = media_queue.get(ctx)[old-1].title
            media_queue.get(ctx).insert(new-1, media_queue.get(ctx).pop(old-1))
            await ctx.send(embed=embedq(f'Moved {to_move} to #{new}.'))
        except IndexError as e:
            await ctx.send(embed=embedq('The selected number is out of range.'))
        except Exception as e:
            await ctx.send(embed=embedq('An unexpected error occurred.'))
            log_traceback(e)

    @commands.command(aliases=get_aliases('nowplaying'))
    @commands.check(is_command_enabled)
    async def nowplaying(self, ctx: commands.Context):
        """Displays the currently playing video."""
        if voice is None:
            await ctx.send(embed=embedq('Not connected to a voice channel.'))
            return

        if not voice.is_playing() and not voice.is_paused():
            embed = discord.Embed(title=f'Nothing is playing.',color=EMBED_COLOR)
        else:
            elapsed = timestamp_from_seconds(audio_time_elapsed)
            submitter_text = get_queued_by_text(now_playing.user)
            embed = discord.Embed(title=f'{get_loop_icon()}Now playing: {now_playing.title} [{elapsed} / {now_playing.duration}]',description=f'Link: {now_playing.weburl}{submitter_text}\nElapsed time may not be precisely accurate, due to minor network hiccups.',color=EMBED_COLOR)

        await ctx.send(embed=embed)

    @commands.command(aliases=get_aliases('pause'))
    @commands.check(is_command_enabled)
    async def pause(self, ctx: commands.Context):
        """Pauses the player."""
        # Developer note: See on_command_error for how this gets resumed
        global paused_at
        if voice.is_playing():
            paused_at = time.time()
            voice.pause()
            await ctx.send(embed=embedq('Player has been paused.'))
        elif voice.is_paused():
            await ctx.send(embed=embedq('Player is already paused.'))
        else:
            await ctx.send(embed=embedq('Nothing to pause.'))
    
    @commands.command(aliases=get_aliases('play'))
    @commands.check(is_command_enabled)
    async def play(self, ctx: commands.Context, *queries):
        """Adds a link to the queue. Plays immediately if the queue is empty."""
        # Will resume if paused, this is handled in on_command_error()
        global playctx
        playctx = ctx
        global qmessage
        qmessage = await ctx.send(embed=embedq('Trying to queue...'))

        multiple_urls = False

        url_count = text_count = 0
        for q in queries:
            if q.startswith('https://'):
                url_count += 1
                if url_count > 1 and re.search(r'(/sets/|playlist\?list=|/album/|/playlist/)', q) is not None:
                    await qmessage.edit(embed=embedq('Cannot multiple albums or playlists at once.'))
                    return
            else:
                text_count += 1
        
        if url_count > 0 and text_count > 0:
            await qmessage.edit(embed=embedq('Queries must be either all URLs or a single text query.'))
            return
        
        query_type = 'link' if url_count > 0 else 'text'

        if query_type == 'text':
            query = ' '.join(queries)
        elif query_type == 'link':
            multiple_urls = len(queries) > 1
            if not multiple_urls:
                # Prevent yt-dlp from grabbing the playlist the track is from
                url = queries[0].split('&list=')[0]
        
        log(f'multiple? {multiple_urls}')

        async with ctx.typing():
            if multiple_urls:
                if len(queries) > MAXIMUM_CONSECUTIVE_URLS:
                    await qmessage.edit(embed=embedq('Too many URLs were given.', f'Current limit is {MAXIMUM_CONSECUTIVE_URLS}.'+
                        'Edit `maximum-urls` in `config.yml` to change this.'))
                    return
                try:
                    objlist = QueueItem.generate_from_list(queries, ctx.author)
                    queue_batch(ctx, objlist)
                    await qmessage.edit(embed=embedq(f'Queued {len(objlist)} items.'))
                    if not voice.is_playing():
                        log('Voice client is not playing; starting...')
                        await advance_queue(ctx)
                    return
                except Exception as e:
                    log_traceback(e)
            
            # Search with text if no url is provided
            if query_type == 'text':
                await qmessage.edit(embed=embedq('Searching by text...'))
                log('Link not detected, searching by text', verbose=True)
                log(f'Searching: "{query}"')

                top_song, top_video = spoofy.search_ytmusic_text(query)

                if top_song == top_video is None:
                    await qmessage.edit(embed=embedq('No song or video match could be found for your query.'))
                    return

                if top_song is not None:
                    top_song['url'] = 'https://www.youtube.com/watch?v='+top_song['videoId']
                if top_video is not None:
                    top_video['url'] = 'https://www.youtube.com/watch?v='+top_video['videoId']
                
                if top_song is None:
                    log(f'No song result found; using video result...', verbose=True)
                    url = top_video['url']
                elif top_video is None:
                    log(f'No video result found; using song result...', verbose=True)
                    url = top_song['url']
                elif top_song['url'] == top_video['url']:
                    log(f'Song and video results were identical; using song result...', verbose=True)
                    url = top_song['url']
                else:
                    log(f'Prompting user for song/video choice.', verbose=True)
                    embed = discord.Embed(title='Please choose an option:', color=EMBED_COLOR)
                    embed.add_field(name=f'Top song result: {top_song["title"]}', value=top_song['url'], inline=False)
                    embed.add_field(name=f'Top video result: {top_video["title"]}', value=top_video['url'], inline=False)

                    prompt = await ctx.send(embed=embed)
                    choice = await prompt_for_choice(ctx, prompt, 2)
                    if choice is None:
                        await qmessage.delete()
                        return
                    else:
                        await qmessage.edit(embed=embedq('Queueing choice...'))
                    url = (top_song['url'], top_video['url'])[choice-1]

            # Locate youtube equivalent if spotify link given
            if 'https://spotify.link/' in url:
                # Resolve mobile share link to the usable URL
                log(f'Resolve spotify.link URL... ({url})')
                try:
                    url = requests.get(url).url
                    log(f'Success! ({url})')
                except Exception as e:
                    log(f'Failed; aborting play command and showing traceback...')
                    log_traceback(e)
                    await qmessage.edit(embed=embedq('Failed to resolve Spotify link. Please use an "open.spotify.com" link instead of "spotify.link" if possible.'))
                    return

            if 'https://open.spotify.com' in url:
                log('Spotify URL received from play command.', verbose=True)
                log('Checking for playlist...', verbose=True)
                if '/playlist/' in url and ALLOW_SPOTIFY_PLAYLISTS:
                    log('Spotify playlist detected.', verbose=True)
                    await qmessage.edit(embed=embedq('Trying to queue Spotify playlist...'))

                    objlist = QueueItem.generate_from_list(spoofy.spotify_playlist(url), ctx.author)
                    if len(objlist) > SPOTIFY_PLAYLIST_LIMIT:
                        await qmessage.edit(embed=embedq('Spotify playlist limit exceeded.'))
                        return
                    
                    queue_batch(ctx, objlist)
                    list_name = spoofy.sp.playlist(url)['name']
                    await qmessage.edit(embed=embedq(f'Queued {len(objlist)} items from {list_name}.'))
                    if not voice.is_playing():
                        log('Voice client is not playing; starting...')
                        await advance_queue(ctx)
                    return
                elif not ALLOW_SPOTIFY_PLAYLISTS:
                    await ctx.send(embed=embedq(
                        'Spotify playlists are currently disabled in this bot\'s configuration.',
                        'Contact whoever is hosting your bot if you believe this is a mistake.'
                        )
                    )
                    return

                log('Checking for album...', verbose=True)
                if 'open.spotify.com/album/' in url:
                    log('Spotify album detected.', verbose=True)
                    album_info = spoofy.spotify_album(url)
                    url = spoofy.search_ytmusic_album(album_info['title'], album_info['artist'], album_info['year'])
                    if url is None:
                        await qmessage.edit(embed=embedq('No match could be found.'))
                        return
            
            # Determines if the input was a playlist
            valid = ['playlist?list=', '/sets/', '/album/']
            if any(i in url for i in valid):
                log('URL is a playlist.', verbose=True)
                objlist = QueueItem.generate_from_list(url, ctx.author)
                queue_batch(ctx, objlist)
                await ctx.send(embed=embedq(f'Queued {len(objlist)} items.'))
                if not voice.is_playing():
                    await advance_queue(ctx)
                return
            else:
                # Runs if the input given was not a playlist
                log('URL is not a playlist.', verbose=True)
                log('Checking duration...', verbose=True)
                duration = duration_from_url(url)

                if duration > DURATION_LIMIT*60*60:
                    log('Item over duration limit; not queueing.')
                    await qmessage.edit(embed=embedq(f'Cannot queue items longer than {DURATION_LIMIT} hours.'))
                    return

            # Queue or start the player
            try:
                log('Appending to queue...', verbose=True)
                if not voice.is_playing() and media_queue.get(ctx) == []:
                    media_queue.get(ctx).append(QueueItem(url, ctx.author))
                    log('Voice client is not playing; starting...')
                    await advance_queue(ctx)
                else:
                    media_queue.get(ctx).append(QueueItem(url, ctx.author))
                    title = media_queue.get(ctx)[-1].title
                    await qmessage.edit(embed=embedq(f'Added {title} to the queue at spot #{len(media_queue.get(ctx))}'))
            except Exception as e:
                log_traceback(e)

    @commands.command(aliases=get_aliases('queue'))
    @commands.check(is_command_enabled)
    async def queue(self, ctx: commands.Context, page: int=1):
        """Displays the current queue, up to 10 items per page."""
        if media_queue.get(ctx) == []:
            await ctx.send(embed=embedq('The queue is empty.'))
            return

        total_pages = math.ceil(len(media_queue.get(ctx)) / 10)

        if page > total_pages:
            await ctx.send(embed=embedq(f'Out of range; the current queue has {total_pages} pages.', f'{len(media_queue.get(ctx))} items in total.'))
            return

        queue_time = 0
        for item in media_queue.get(ctx):
            queue_time += item.duration
        
        queue_time = timestamp_from_seconds(queue_time)

        embed = discord.Embed(title=f'Current queue:\n*Approx. time remaining: {queue_time}*',color=EMBED_COLOR)
        start = (10*page)-10
        end = (10*page)
        if 10*page > len(media_queue.get(ctx)):
            end = len(media_queue.get(ctx))
        
        for num, item in enumerate(media_queue.get(ctx)[start:end]):
            submitter_text = get_queued_by_text(item.user)
            length_text = f'[{timestamp_from_seconds(item.duration)}]' if timestamp_from_seconds(item.duration) != '00:00' else ''
            embed.add_field(name=f'#{num+1+start}. {item.title} {length_text}', value=f'Link: {item.url}{submitter_text}', inline=False)

        try:
            embed.description = (f'Showing {start+1} to {end} of {len(media_queue.get(ctx))} items. Use -queue [page] to see more.')
        except Exception as e:
            log_traceback(e)
        await ctx.send(embed=embed)

    @commands.command(aliases=get_aliases('remove'))
    @commands.check(is_command_enabled)
    async def remove(self, ctx: commands.Context, spot: int):
        """Removes an item from the queue. Use -q to get its number."""
        await ctx.send(embed=embedq(f'Removed {media_queue.get(ctx).pop(spot-1).title} from the queue.'))

    @commands.command(aliases=get_aliases('shuffle'))
    @commands.check(is_command_enabled)
    async def shuffle(self, ctx: commands.Context):
        """Randomizes the order of the queue."""
        random.shuffle(media_queue.get(ctx))
        await ctx.send(embed=embedq('Queue has been shuffled.'))

    @commands.command(aliases=get_aliases('skip'))
    @commands.check(is_command_enabled)
    async def skip(self, ctx: commands.Context):
        """Skips the currently playing media."""
        log('Trying to skip...', verbose=True)
        if voice is None:
            await ctx.send(embed=embedq('Not connected to a voice channel.'))
            return
        elif not voice.is_playing() and len(media_queue.get(ctx)) == 0:
            await ctx.send(embed=embedq('Nothing to skip.'))
            return

        # Update number skip votes required based on members joined in voice channel
        global skip_votes
        global skip_votes_needed
        skip_votes_needed = int((len(voice.channel.members)) * (SKIP_VOTES_PERCENTAGE/100)) if SKIP_VOTES_TYPE == "percentage" else SKIP_VOTES_EXACT

        if VOTE_TO_SKIP:
            if ctx.author not in skip_votes:
                skip_votes.append(ctx.author)
            else:
                await ctx.send(embed=embedq('You have already voted to skip.'))
                return

            voteskip_message = await ctx.send(embed=embedq(f'Voted to skip. {len(skip_votes)}/{skip_votes_needed} needed.'))
            if len(skip_votes) >= skip_votes_needed:
                await voteskip_message.delete()
            else:
                return
        
        voice.pause()
        await ctx.send(embed=embedq('Skipping...'))
        await advance_queue(ctx, skip=True)

    @commands.command(aliases=get_aliases('stop'))
    @commands.check(is_command_enabled)
    async def stop(self, ctx: commands.Context):
        """Stops the player and clears the queue."""
        global media_queue
        media_queue.clear(ctx)
        if voice.is_playing() or voice.is_paused():
            voice.stop()
            await ctx.send(embed=embedq('Player has been stopped.'))
        else:
            await ctx.send(embed=embedq('Nothing is playing.'))
    
    @commands.command(aliases=get_aliases('clearcache'))
    @commands.check(is_command_enabled)
    async def clearcache(self, ctx: commands.Context):
        """Removes all information from the current URL cache"""
        global url_info_cache
        url_info_cache = {}
        log(f'URL cache was cleared: {url_info_cache}', verbose=True)
        await ctx.send(embed=embedq('URL cache has been emptied.', '' if USE_URL_CACHE else f'{emoji["info"]} URL cache is currently disabled.'))

    @join.before_invoke
    @play.before_invoke
    @pause.before_invoke
    @stop.before_invoke
    async def ensure_voice(self, ctx: commands.Context):
        if ctx.voice_client is None:
            if ctx.author.voice:
                log(f'Joining voice channel: {ctx.author.voice.channel}')
                global voice
                voice = await ctx.author.voice.channel.connect()
            else:
                await ctx.send(embed=embedq("You are not connected to a voice channel."))

# ############################################
# 
# End of cog definitions.
# 
# ############################################

url_info_cache = {}

def get_queued_by_text(user_object: discord.Member) -> str:
    username = user_object.nick if user_object.nick else user_object.name
    return f'\nQueued by {username}' if SHOW_USERS_IN_QUEUE else ''

def cache_if_succeeded(key: str):
    """
    Stores result into cache dictionary if retrieval succeeded, or returns result if one already exists

    key (str): The dictionary key to check and/or store results
    """
    def decorator(func):
        def cache_check(*args, **kwargs):
            # Just run functions normally if caching is disabled
            if USE_URL_CACHE == False:
                result = func(*args, **kwargs)
                return result
            # Otherwise, check the cache for an existing key to return, or create a new one if none is found (or the value is invalid)
            try:
                url = args[0]
                if url not in url_info_cache:
                    url_info_cache[url] = {}
            
                if url_info_cache[url].get(key, None) not in ['', None]:
                    # Return stored info
                    result = url_info_cache[url][key]
                    log(f'{key} of \'{url}\' already stored: {result}', verbose=True)
                    return result
                else:
                    # Retrieve info normally
                    result = func(*args, **kwargs)
                    url_info_cache[url][key] = result
                    return result
            except Exception as e:
                log_traceback(e)
        return cache_check
    return decorator

@cache_if_succeeded(key='duration')
def duration_from_url(url: str) -> int|float:
    """Automatically detects the source of a given URL, and returns its extracted duration."""
    log(f'Getting length of \'{url}\'...', verbose=True)
    if 'youtube.com' in url:
        try:
            return pytube.YouTube(url).length
        except Exception as e:
            log(f'pytube encountered "{traceback.format_exception(e)[-1]}" during length retrieval. Falling back on yt-dlp.', verbose=True)
            info_dict = ytdl.extract_info(url, download=False)
            return info_dict.get('duration', 0)
    elif 'soundcloud.com' in url:
        return round(spoofy.sc.resolve(url).duration / 1000)
    elif 'open.spotify.com' in url:
        return spoofy.spotify_track(url)['duration']
    else:
        # yt-dlp should handle most other URLs
        info_dict = ytdl.extract_info(url, download=False)
        return info_dict.get('duration', 0)

@cache_if_succeeded(key='title')
def title_from_url(url: str) -> str:
    """Automatically detects the source of a given URL, and returns its extracted title."""
    log(f'Getting title of \'{url}\'...', verbose=True)
    if 'youtube.com' in url:
        try:
            return pytube.YouTube(url).title
        except Exception as e:
            log(f'pytube encountered "{traceback.format_exception(e)[-1]}" during title retrieval. Falling back on yt-dlp.', verbose=True)
            info_dict = ytdl.extract_info(url, download=False)
            return info_dict.get('title', None)
    elif 'soundcloud.com' in url:
        return spoofy.sc.resolve(url).title
    elif 'open.spotify.com' in url:
        return spoofy.spotify_track(url)['title']
    else:
        # yt-dlp should handle most URLs
        info_dict = ytdl.extract_info(url, download=False)
        return info_dict.get('title', None)

def timestamp_from_seconds(seconds: int|float) -> str:
    """Returns a formatted string in either MM:SS or HH:MM:SS from the given time in seconds."""
    # Omit the hour place if not >=60 minutes
    return time.strftime('%M:%S', time.gmtime(seconds)) if seconds < 3600 else time.strftime('%H:%M:%S', time.gmtime(seconds))

async def prompt_for_choice(ctx: commands.Context, prompt_msg: discord.Message, choices: int, timeout: int=30) -> int|None:
    """Adds reactions to a given Message (prompt_msg) and returns the outcome
    
    msg -- Message to be edited based on the outcome

    prompt -- Message to add the reaction choices to

    Returns None if the prompt failed in some way or was cancelled, returns an integer if a choice was made successfully
    """
    # Get reaction menu ready
    log('Adding reactions...', verbose=True)

    if choices > len(emoji['num']):
        log('Choices out of range for emoji number list.'); return

    for i in list(range(0, choices)):
        await prompt_msg.add_reaction(emoji['num'][i+1])

    await prompt_msg.add_reaction(emoji['cancel'])

    def check(reaction: discord.Reaction, user: discord.Member) -> bool:
        log('Reaction check is being called...', verbose=True)
        return user == ctx.message.author and (str(reaction.emoji) in emoji['num'] or str(reaction.emoji) == emoji['cancel'])

    log('Waiting for reaction...', verbose=True)

    try:
        reaction, user = await bot.wait_for('reaction_add', timeout=timeout, check=check)
    except asyncio.TimeoutError as e:
        log('Choice prompt timeout reached.')
        await prompt_msg.delete()
        return
    except Exception as e:
        log_traceback(e)
        await prompt_msg.edit(embed=embedq('An unexpected error occurred.'))
        return
    else:
        # If a valid reaction was received.
        log('Received a valid reaction.', verbose=True)

        if str(reaction) == emoji['cancel']:
            log('Selection cancelled.', verbose=True)
            await prompt_msg.delete()
            return
        else:
            choice = emoji['num'].index(str(reaction))
            log(f'{choice} selected.', verbose=True)
            await prompt_msg.delete()
            return choice

# Queue system

class MediaQueue:
    def __init__(self):
        self.queues = {}

    # Run in every function to automatically determine
    # which queue we're working with
    def ensure_queue_exists(self, ctx: commands.Context):
        if ctx.author.guild.id not in self.queues:
            self.queues[ctx.author.guild.id] = []

    def get(self, ctx: commands.Context) -> list:
        self.ensure_queue_exists(ctx)
        return self.queues[ctx.author.guild.id]

    def set(self, ctx: commands.Context, new_list: list):
        self.ensure_queue_exists(ctx)
        self.queues[ctx.author.guild.id] = new_list

    def clear(self, ctx: commands.Context):
        self.ensure_queue_exists(ctx)
        self.queues[ctx.author.guild.id] = []

class QueueItem:
    def __init__(self, url: str, user: discord.Member, title: str=None, duration: int|float=None):
        self.url = url
        self.user = user
        self.duration = duration if duration is not None else duration_from_url(url)
        self.title = title if title is not None else title_from_url(url)

    @staticmethod
    def generate_from_list(playlist: str|list|tuple, user: discord.Member) -> list:
        """Creates a list of QueueItem instances from a valid playlist

        - `playlist` (str, list): Either a URL to a SoundCloud or ytdl-compatible playlist, or a list of Spotify tracks
        - `user`: A discord Member object of the user who queued the playlist
        """
        objlist = []
        # Will be a list if origin is Spotify, or if multiple URLs were sent with the command
        if isinstance(playlist, (list, tuple)):
            print(playlist)
            for item in playlist:
                if isinstance(item, str) and 'open.spotify.com' in item:
                    item = spoofy.spotify_track(item)
                
                if isinstance(item, dict) and 'open.spotify.com' in item['url']:
                    objlist.append(QueueItem(item['url'], user, title=item['title'], duration=item.get('duration', 0)))
                else:
                    info = ytdl.extract_info(item, download=False)
                    objlist.append(QueueItem(info['webpage_url'], user, title=info['title'], duration=info.get('duration', 0)))
            return objlist
        else:
            # Anything youtube-dl natively supports is probably a link
            if 'soundcloud.com' in playlist:
                # SoundCloud playlists have to be processed differently
                playlist_entries = spoofy.soundcloud_playlist(playlist)
                objlist = [QueueItem(item.permalink_url, user, title=item.title, duration=round(item.duration/1000)) for item in playlist_entries]
            else:
                playlist_entries = ytdl.extract_info(playlist, download=False)
                objlist = [QueueItem(item['url'], user, title=item['title'], duration=item.get('duration', 0)) for item in playlist_entries['entries']]
            return objlist

media_queue = MediaQueue()

def queue_batch(ctx: commands.Context, batch: list[QueueItem]):
    global media_queue
    for item in batch:
        media_queue.get(ctx).append(item)

now_playing: YTDLSource = None
last_played: YTDLSource = None

current_item: QueueItem = None

npmessage: discord.Message = None
qmessage: discord.Message = None

audio_start_time = 0
audio_time_elapsed = 0
paused_at = 0
paused_for = 0

loop_this = False

async def play_item(item: QueueItem, ctx: commands.Context):
    global audio_start_time, audio_time_elapsed, paused_at, paused_for
    global now_playing
    global last_played
    global current_item
    global npmessage
    global qmessage
    global skip_votes

    skip_votes = []

    audio_time_elapsed = paused_at = paused_for = 0

    last_played = now_playing

    try:
        if npmessage is not None:
            await npmessage.delete()
    except discord.errors.NotFound:
        log('Now-playing message wasn\'t found, ignoring and continuing...', verbose=True)
    
    log('Trying to start playing...')

    # Check if we need to match a Spotify link
    if 'open.spotify.com' not in item.url:
        url = item.url
    else:
        log('Trying to match Spotify track...')
        npmessage = await ctx.send(embed=embedq(f'Spotify link detected, searching YouTube...','Please wait, this may take a while!\nIf you think the bot\'s become stuck, use the skip command.'))
        spyt = spoofy.spyt(item.url)

        log('Checking if unsure...', verbose=True)
        if type(spyt) == tuple and spyt[0] == 'unsure':
            # This indicates no match was found
            log('spyt returned unsure.', verbose=True)
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
                embed = discord.Embed(title='No exact match found; please choose an option.',description=f'Select the number with reactions or use {emoji["cancel"]} to cancel.',color=EMBED_COLOR)
                
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
        log(f'Failed to download video: {e}')
        await ctx.send(embed=embedq('This video is unavailable.', url))
        await advance_queue(ctx)
        return

    now_playing = player
    now_playing.weburl = url
    now_playing.user = item.user

    if item.duration is not None:
        if item.duration == 0:
            item.duration = duration_from_url(item.url)
        now_playing.duration = timestamp_from_seconds(item.duration)
    else:
        try:
            now_playing.duration = timestamp_from_seconds(pytube.YouTube(now_playing.weburl).length)
        except Exception as e:
            log(f'Falling back on yt-dlp. (Cause: {traceback.format_exception(e)[-1]})', verbose=True)
            try:
                now_playing.duration = timestamp_from_seconds(ytdl.extract_info(now_playing.weburl, download=False)['duration'])
            except Exception as e:
                log(f'ytdl duration extraction failed, likely a direct file link. (Cause: {traceback.format_exception(e)[-1]})', verbose=True)
                log(f'Attempting to retrieve URL through FFprobe...', verbose=True)
                ffprobe = f'ffprobe {url} -v quiet -show_entries format=duration -of csv=p=0'.split(' ')
                now_playing.duration = float(subprocess.check_output(ffprobe).decode('utf-8').split('.')[0])
    
    voice.stop()
    voice.play(now_playing, after=lambda e: asyncio.run_coroutine_threadsafe(advance_queue(ctx), bot.loop))
    audio_start_time = time.time()

    if npmessage is not None:
        await npmessage.delete()

    try:
        await qmessage.delete()
    except Exception as e:
        pass

    submitter_text = get_queued_by_text(item.user)
    embed = discord.Embed(title=f'{get_loop_icon()}Now playing: {now_playing.title} [{now_playing.duration}]',description=f'Link: {url}{submitter_text}',color=EMBED_COLOR)
    npmessage = await ctx.send(embed=embed)

    if last_played is not None:
        for i in glob.glob(f'*-#-{last_played.ID}-#-*'):
            # Delete last played file
            try:
                log(f'Removing file: {i}', verbose=True)
                os.remove(i)
            except PermissionError as e:
                log(f'Cannot remove; the file is likely in use.', verbose=True)
                pass

advance_lock = False

async def advance_queue(ctx: commands.Context, skip: bool=False):
    """Attempts to advance forward in the queue, if the bot is clear to do so."""
    # Triggers every time the player finishes
    global advance_lock
    if not advance_lock and (skip or not voice.is_playing()):
        log('Locking...', verbose=True)
        advance_lock = True

        try:
            if not skip and loop_this and current_item is not None:
                media_queue.get(ctx).insert(0, current_item)

            if media_queue.get(ctx) == []:
                voice.stop()
            else:
                next_item = media_queue.get(ctx).pop(0)
                await play_item(next_item, ctx)
            
            log('Tasks finished; unlocking...', verbose=True)
            advance_lock = False
        except Exception as e:
            log_traceback(e)
            log('Error encountered; unlocking...', verbose=True)
            advance_lock = False
    elif advance_lock:
        log('Attempted call while locked; ignoring...', verbose=True)

# TODO: This could have a better name
def get_loop_icon() -> str:
    if loop_this: return emoji['repeat']+' '
    else: return ''

# Establish bot user
intents = discord.Intents.default()
intents.messages = True
intents.message_content = True
intents.voice_states = True
intents.reactions = True
intents.guilds = True
intents.members = True

# Use separate dev and public mode prefixes
command_prefix = PUBLIC_PREFIX if PUBLIC else DEV_PREFIX

bot = commands.Bot(
    command_prefix=commands.when_mentioned_or(command_prefix),
    description='',
    intents=intents,
    help_command = PrettyHelp(False, color=EMBED_COLOR)
)

# Command error handling
@bot.event
async def on_command_error(ctx: commands.Context, error):
    if isinstance(error, commands.errors.MissingRequiredArgument):
        match ctx.command.name:
            case 'play':
                # Resuming while paused
                if voice.is_paused():
                    voice.resume()
                    await ctx.send(embed=embedq('Player is resuming.'))
                    global paused_for
                    paused_for = time.time() - paused_at
                else:
                    await ctx.send(embed=embedq('No URL given.'))
            case 'volume':
                await ctx.send(embed=embedq('An integer between 0 and 100 must be given for volume.'))
            case 'analyze':
                await ctx.send(embed=embedq('A spotify track URL is required.'))
    elif isinstance(error, commands.CheckFailure):
        await ctx.send(embed=embedq('This command is disabled for this instance.', 'If you run this bot, check your `config.yml`.'))
    elif isinstance(error, commands.CommandNotFound):
        # Just ignore these
        pass
    elif isinstance(error, yt_dlp.utils.DownloadError):
        await ctx.send(embed=embedq('Could not queue; this video may be private or otherwise unavailable.', error))
    # TODO: add custom message for yt_dlp errors like private videos
    else:
        log(f'Error encountered in command `{ctx.command}`.')
        log(error)
        trace = traceback.format_exception(error)
        await ctx.send(embed=embedq(error, 'If this issue persists, please check https://github.com/svioletg/viMusBot/issues and submit a new issue if your problem is not listed.'))
        # A second traceback is created from this command itself, usually not useful
        log(f'Full traceback below.\n\n{plt.error}'+''.join(trace[:trace.index('\nThe above exception was the direct cause of the following exception:\n\n')]))

@bot.event
async def on_ready():
    log(f'Logged in as {bot.user} (ID: {bot.user.id})')
    print('-----')
    log('Ready!')

# Retrieve bot token
log(f'Retrieving token from {plt.blue}{TOKEN_FILE_PATH}')

if not PUBLIC:
    log(f'{plt.warn}NOTICE: Starting in dev mode.')

try:
    with open(TOKEN_FILE_PATH, 'r') as f:
        token = f.read()
except FileNotFoundError:
    log(f'{plt.error}{f} does not exist; exiting.')
    raise SystemExit(0)

# Begin main thread
async def main():
    async with bot:
        await bot.add_cog(General(bot))
        await bot.add_cog(Music(bot))
        await bot.start(token)

if __name__ == '__main__':
    asyncio.run(main())