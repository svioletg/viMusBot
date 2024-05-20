"""The main bot script. Running this will start viMusBot."""

# Standard imports
import asyncio
import glob
import itertools
import logging
import math
import os
import random
import subprocess
import time
import traceback
from pathlib import Path
from typing import Optional

# External imports
import aioconsole
import colorama
import discord
import pytube
import regex as re
import requests
import yt_dlp
from discord.ext import commands
from pretty_help import PrettyHelp

# Local imports
import update
import utils.configuration as config
from utils import media, miscutil
from utils.palette import Palette
from version import VERSION

colorama.init(autoreset=True)
plt = Palette()

# Setup discord logging
discordpy_logfile_handler = logging.FileHandler(filename='discord.log', encoding='utf-8', mode='w')
discord.utils.setup_logging(handler=discordpy_logfile_handler, level=logging.INFO, root=False)

# Setup bot logging
log = miscutil.create_logger(__name__, Path('vimusbot.log'))
# Assign local modules the same logger
media.log = log

log.info('Logging for bot.py is now active.')

# Check for updates
if __name__ == '__main__':
    log.info(f'Running on version {VERSION}; checking for updates...')

    update_check_result = update.get_latest_tag()

    # Check for an outdated version
    if update_check_result['current'] != update_check_result['latest']:
        log.info(f'{plt.lime}There is a new release available.')
        current_tag = update_check_result['current']
        latest_tag = update_check_result['latest']
        log.info(f'Current: {plt.gold}{current_tag}{plt.reset} | Latest: {plt.lime}{latest_tag}')
        log.info('Use "update.py" or "update.bat" to update.')
    else:
        if VERSION.startswith('dev.'):
            log.info(f'{plt.yellow}NOTICE: You are running a development version.')
        else:
            log.info(f'{plt.lime}You are up to date.')

    log.info('Changelog: https://github.com/svioletg/viMusBot/blob/master/docs/changelog.md')

skip_votes_remaining: int = 0
skip_votes = [] # TODO: Typing; What does this list contain?

# Clear out downloaded files
log.info('Removing previously downloaded media files...')
files = glob.glob('*.*')
to_remove = [f for f in files if Path(f).suffix in CLEANUP_EXTENSIONS]
for t in to_remove:
    os.remove(t)
del files, to_remove

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

# Start bot-related events
class Music(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    audio_start_time: int = 0
    audio_time_elapsed: int = 0
    paused_at: int = 0
    paused_for: int = 0

    # Playing music / Voice-related
    @commands.command(aliases=command_aliases('analyze'))
    @commands.check(is_command_enabled)
    async def analyze(self, ctx: commands.Context, spotifyurl: str):
        """Returns spotify API information regarding a track."""
        info = media.spotify_track(spotifyurl)
        title = info['title']
        artist = info['artist']
        result = media.analyze_spotify_track(spotifyurl)
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
            if isinstance(data[i], (int, float)):
                if data[i]<1 and i!='loudness':
                    value=str(round(data[i]*100,2))+'%'

            value=str(value)
            embed.add_field(name=i.title(),value=value)
        await ctx.send(embed=embed)

    @commands.command(aliases=command_aliases('clear'))
    @commands.check(is_command_enabled)
    async def clear(self, ctx: commands.Context):
        """Clears the entire queue."""
        global media_queue
        media_queue.clear(ctx)
        await ctx.send(embed=embedq('Queue cleared.'))

    @commands.command(aliases=command_aliases('join'))
    @commands.check(is_command_enabled)
    async def join(self, ctx):
        """Joins the voice channel of the user."""
        # This actually just calls ensure_voice below,
        # this is only defined so that there's a command in Discord for it
        pass

    @commands.command(aliases=command_aliases('leave'))
    @commands.check(is_command_enabled)
    async def leave(self, ctx: commands.Context):
        """Disconnects the bot from voice."""
        global voice
        global media_queue
        media_queue.clear(ctx)
        log.info(f'Leaving voice channel: {ctx.author.voice.channel}')
        try:
            await voice.disconnect()
        except AttributeError:
            await ctx.send(embed=embedq('Not connected to voice.'))
        voice = None

    @commands.command(aliases=command_aliases('loop'))
    @commands.check(is_command_enabled)
    async def loop(self, ctx: commands.Context):
        """Toggles looping for the current track."""
        global loop_this
        # Inverts the boolean
        loop_this = not loop_this
        log.info(f'Looping {["disabled", "enabled"][loop_this]}.')
        await ctx.send(embed=embedq(f'{get_loop_icon()}Looping {["disabled", "enabled"][loop_this]}.'))

    @commands.command(aliases=command_aliases('move'))
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
            log.error(e)

    @commands.command(aliases=command_aliases('nowplaying'))
    @commands.check(is_command_enabled)
    async def nowplaying(self, ctx: commands.Context):
        """Shows the currently playing track."""
        if voice is None:
            await ctx.send(embed=embedq('Not connected to a voice channel.'))
            return

        if not voice.is_playing() and not voice.is_paused():
            embed = discord.Embed(title=f'Nothing is playing.',color=EMBED_COLOR)
        else:
            elapsed = timestamp_from_seconds(audio_time_elapsed)
            submitter_text = get_queued_by_text(now_playing.user)
            embed = discord.Embed(title=f'{get_loop_icon()}Now playing: {now_playing.title} [{elapsed} / {now_playing.duration_stamp}]',description=f'Link: {now_playing.weburl}{submitter_text}\nElapsed time may not be precisely accurate, due to minor network hiccups.',color=EMBED_COLOR)

        await ctx.send(embed=embed)

    @commands.command(aliases=command_aliases('pause'))
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
    
    @commands.command(aliases=command_aliases('play'))
    @commands.check(is_command_enabled)
    async def play(self, ctx: commands.Context, *queries: str):
        """Adds a link to the queue. Plays immediately if the queue is empty."""
        if len(queries) == 0:
            if voice.is_paused():
                voice.resume()
                await ctx.send(embed=embedq('Player is resuming.'))
                global paused_for
                paused_for = time.time() - paused_at
            else:
                await ctx.send(embed=embedq('No URL or search terms given.'))
            return

        global qmessage
        qmessage = await ctx.send(embed=embedq('Trying to queue...'))

        multiple_urls = False

        url_count = text_count = 0
        for q in queries:
            if q.startswith('https://'):
                url_count += 1
                if url_count > 1 and re.search(r'(/sets/|playlist\?list=|/album/|/playlist/)', q) is not None:
                    await qmessage.edit(embed=embedq('Cannot queue multiple albums or playlists at once.'))
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

        log.info('Found multiple URLs.' if multiple_urls else 'Found a single URL or query.')

        async with ctx.typing():
            if multiple_urls:
                if len(queries) > MAXIMUM_CONSECUTIVE_URLS:
                    await qmessage.edit(embed=embedq('Too many URLs were given.', f'Current limit is {MAXIMUM_CONSECUTIVE_URLS}.'+
                        'Edit `maximum-urls` in `config.yml` to change this.'))
                    return
                try:
                    objlist = QueueItem.generate_from_list(queries, ctx.author)
                    if objlist[0] != []:
                        queue_batch(ctx, objlist[0])
                        await qmessage.edit(embed=embedq(f'Queued {len(objlist[0])} items.'))
                        if objlist[1] != []:
                            await qmessage.edit(embed=embedq(f'Failed to retrieve {len(objlist[1])} URL{'s' if len(objlist[1]) > 1 else ''}:', f'{'\n'.join(objlist[1])}'))
                        if not voice.is_playing():
                            log.info('Voice client is not playing; starting...')
                            await advance_queue(ctx)
                    else:
                        await qmessage.edit(embed=embedq('Failed to retrieve all URLs; nothing added to the queue.'))
                    return
                except Exception as e:
                    log.error(e)
            
            # Search with text if no url is provided
            if query_type == 'text':
                await qmessage.edit(embed=embedq('Searching by text...'))
                log.debug('Link not detected, searching by text.')
                log.info(f'Searching: "{query}"')

                top_song, top_video = media.search_ytmusic_text(query)

                if (top_song is None) and (top_video is None):
                    await qmessage.edit(embed=embedq('No song or video match could be found for your query.'))
                    return

                if top_song is not None:
                    top_song['url'] = 'https://www.youtube.com/watch?v=' + top_song['videoId']
                if top_video is not None:
                    top_video['url'] = 'https://www.youtube.com/watch?v=' + top_video['videoId']
                
                if top_song is None:
                    log.info('No song result found; using video result...')
                    url = top_video['url']
                elif top_video is None:
                    log.info('No video result found; using song result...')
                    url = top_song['url']
                elif top_song['url'] == top_video['url']:
                    log.info('Song and video results were identical; using song result...')
                    url = top_song['url']
                else:
                    log.info(f'Prompting user for song/video choice.')
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
                # Resolve mobile share link to a usable URL
                log.info(f'Resolving spotify.link URL... ({url})')
                try:
                    url = requests.get(url).url
                    log.info(f'Resolved to {url}')
                except Exception as e:
                    log.info(f'Failed; aborting play command and showing traceback...')
                    log.error(e)
                    await qmessage.edit(embed=embedq('Failed to resolve Spotify link. Please use an "open.spotify.com" link instead of "spotify.link" if possible.'))
                    return

            if 'https://open.spotify.com' in url:
                log.debug('Spotify URL received from play command.')
                log.info('Checking for playlist...')
                if '/playlist/' in url and ALLOW_SPOTIFY_PLAYLISTS:
                    log.info('Spotify playlist detected.')
                    await qmessage.edit(embed=embedq('Trying to queue Spotify playlist...'))
                    playlist_result = media.spotify_playlist(url)

                    if isinstance(playlist_result, tuple):
                        code = playlist_result[1].http_status
                        match code:
                            case 400:
                                log.info('Could not retrieve playlist; the URL seems invalid.')
                                await qmessage.edit(embed=embedq('Could not retrieve playlist; the URL seems invalid. (HTTP 400)'))
                                return
                            case 404:
                                log.info('Could not retrieve playlist; the playlist is likely private.')
                                await qmessage.edit(embed=embedq('Could not retrieve playlist; the playlist is likely private. (HTTP 404)'))
                                return
                            case _:
                                log.info(f'Could not retrieve playlist; an unknown error occurred: HTTP {code}')
                                await qmessage.edit(embed=embedq(f'Could not retrieve playlist; HTTP {code}'))
                                return

                    objlist = QueueItem.generate_from_list(playlist_result, ctx.author)[0]
                    if len(objlist) > SPOTIFY_PLAYLIST_LIMIT:
                        await qmessage.edit(embed=embedq('Spotify playlist limit exceeded.'))
                        return
                    
                    queue_batch(ctx, objlist)
                    list_name = media.sp.playlist(url)['name']
                    await qmessage.edit(embed=embedq(f'Queued {len(objlist)} items from {list_name}.'))
                    if not voice.is_playing():
                        log.info('Voice client is not playing; starting...')
                        await advance_queue(ctx)
                    return
                elif not ALLOW_SPOTIFY_PLAYLISTS:
                    await ctx.send(embed=embedq(
                        'Spotify playlists are currently disabled in this bot\'s configuration.',
                        'Contact whoever is hosting your bot if you believe this is a mistake.'
                        )
                    )
                    return

                log.info('Checking for album...')
                if 'https://open.spotify.com/album/' in url:
                    log.info('Spotify album detected.')
                    album_info = media.spotify_album(url)

                    if isinstance(album_info, tuple):
                        await qmessage.edit(embed=embedq('Could not retrieve album; the URL seems invalid.'))
                        return

                    url = media.match_ytmusic_album(album_info['title'], album_info['artist'], album_info['year'])
                    if url is None:
                        await qmessage.edit(embed=embedq('No match could be found.'))
                        return
            
            # Determines if the input was a playlist or album; any Spotify links should have already been handled
            valid = ['playlist?list=', '/sets/', '/album/']
            if any(item in url for item in valid):
                log.info('URL is a non-Spotify playlist.')
                objlist = QueueItem.generate_from_list(url, ctx.author)
                if isinstance(objlist, tuple):
                    await qmessage.edit(embed=embedq('Could not retrieve playlist.'))
                    return
                queue_batch(ctx, objlist)
                await ctx.send(embed=embedq(f'Queued {len(objlist)} items.'))
                if not voice.is_playing():
                    await advance_queue(ctx)
                return
            else:
                # Runs if the input given was not a playlist
                log.info('URL is not a playlist.')
                log.info('Checking duration...')
                duration = duration_from_url(url)

                if isinstance(duration, tuple):
                    log.info(f'Couldn\'t retrieve duration; aborting play command: {duration[1]}')
                    await qmessage.edit(embed=embedq('Could not retrieve URL; the content may be unavailable, or the URL may be invalid.'))
                    return

                if duration > DURATION_LIMIT*60*60:
                    log.info('Item over duration limit; not queueing.')
                    await qmessage.edit(embed=embedq(f'Cannot queue items longer than {DURATION_LIMIT} hours.'))
                    return

            # Queue or start the player
            try:
                log.info('Adding to queue...')
                if not voice.is_playing() and media_queue.get(ctx) == []:
                    media_queue.get(ctx).append(QueueItem(url, ctx.author))
                    log.info('Voice client is not playing; starting...')
                    await advance_queue(ctx)
                else:
                    media_queue.get(ctx).append(QueueItem(url, ctx.author))
                    title = media_queue.get(ctx)[-1].title
                    await qmessage.edit(embed=embedq(f'Added {title} to the queue at spot #{len(media_queue.get(ctx))}'))
            except Exception as e:
                log.error(e)

    @commands.command(aliases=command_aliases('queue'))
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
        
        queue_time += now_playing.duration - audio_time_elapsed
        
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
            log.error(e)
        await ctx.send(embed=embed)

    @commands.command(aliases=command_aliases('remove'))
    @commands.check(is_command_enabled)
    async def remove(self, ctx: commands.Context, spot: int):
        """Removes an item from the queue. Use -q to get its number."""
        await ctx.send(embed=embedq(f'Removed {media_queue.get(ctx).pop(spot-1).title} from the queue.'))

    @commands.command(aliases=command_aliases('shuffle'))
    @commands.check(is_command_enabled)
    async def shuffle(self, ctx: commands.Context):
        """Randomizes the order of the queue."""
        random.shuffle(media_queue.get(ctx))
        await ctx.send(embed=embedq('Queue has been shuffled.'))

    @commands.command(aliases=command_aliases('skip'))
    @commands.check(is_command_enabled)
    async def skip(self, ctx: commands.Context):
        """Skips the currently playing media."""
        log.info('Skipping track...')
        if voice is None:
            await ctx.send(embed=embedq('Not connected to a voice channel.'))
            return
        elif not voice.is_playing() and len(media_queue.get(ctx)) == 0:
            await ctx.send(embed=embedq('Nothing to skip.'))
            return

        # Update number of skip votes required based on members joined in voice channel
        global skip_votes
        global skip_votes_remaining
        skip_votes_remaining = int((len(voice.channel.members)) * (SKIP_VOTES_PERCENTAGE/100)) if SKIP_VOTES_TYPE == "percentage" else SKIP_VOTES_EXACT

        if VOTE_TO_SKIP:
            if ctx.author not in skip_votes:
                skip_votes.append(ctx.author)
            else:
                await ctx.send(embed=embedq('You have already voted to skip.'))
                return

            voteskip_message = await ctx.send(embed=embedq(f'Voted to skip. {len(skip_votes)}/{skip_votes_remaining} needed.'))
            if len(skip_votes) >= skip_votes_remaining:
                await voteskip_message.delete()
            else:
                return
        
        voice.pause()
        await ctx.send(embed=embedq('Skipping...'))
        await advance_queue(ctx, skip=True)

    @commands.command(aliases=command_aliases('stop'))
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
    
    @commands.command(aliases=command_aliases('clearcache'))
    @commands.check(is_command_enabled)
    async def clearcache(self, ctx: commands.Context):
        """Removes all information from the current URL cache"""
        global url_info_cache
        url_info_cache = {}
        log.debug(f'URL cache was cleared: {url_info_cache}')
        await ctx.send(embed=embedq('URL cache has been emptied.', '' if USE_URL_CACHE else f'{emoji["info"]} URL cache is currently disabled.'))

    @join.before_invoke
    @play.before_invoke
    @pause.before_invoke
    @stop.before_invoke
    async def ensure_voice(self, ctx: commands.Context):
        if ctx.voice_client is None:
            if ctx.author.voice:
                log.info(f'Joining voice channel: {ctx.author.voice.channel}')
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
                    log.debug(f'{key} of \'{url}\' already stored: {result}')
                    return result
                else:
                    # Retrieve info normally
                    result = func(*args, **kwargs)
                    url_info_cache[url][key] = result
                    return result
            except Exception as e:
                log.error(e)
        return cache_check
    return decorator

# TODO: Maybe try and make duration and title from URL into a single function, lot of copied code

@cache_if_succeeded(key='duration')
def duration_from_url(url: str) -> int|float:
    """Automatically detects the source of a given URL, and returns its extracted duration."""
    log.debug(f'Getting length of \'{url}\'...')
    if 'youtube.com' in url:
        try:
            return pytube.YouTube(url).length
        except Exception as e:
            log.info(f'pytube couldn\'t retrieve video length: "{traceback.format_exception(e)[-1]}"; Trying yt-dlp...')
            # Continues after this block so this isn't duplicated
    elif 'soundcloud.com' in url:
        try:
            result = media.sc.resolve(url).duration
        except TypeError as e:
            log.error('Failed to retrieve Soundcloud track.')
        return round(result / 1000)
    elif 'open.spotify.com' in url:
        result = media.spotify_track(url)
        return result.length_seconds
    
    # yt-dlp should handle most other URLs
    try:
        info_dict = ytdl.extract_info(url, download=False)
    except yt_dlp.utils.DownloadError as e:
        log.info(f'Failed to retrieve video length: {e}')
        return None, e
    return info_dict.get('duration', 0)

@cache_if_succeeded(key='title')
def title_from_url(url: str) -> str:
    """Automatically detects the source of a given URL, and returns its extracted title."""
    log.debug(f'Getting title of \'{url}\'...')
    if 'youtube.com' in url:
        try:
            return pytube.YouTube(url).title
        except Exception as e:
            log.info(f'pytube encountered "{traceback.format_exception(e)[-1]}" during title retrieval. Falling back on yt-dlp.')
            # Continues after this block so this isn't duplicated
    elif 'soundcloud.com' in url:
        return media.sc.resolve(url).title
    elif 'open.spotify.com' in url:
        return media.spotify_track(url)['title']
    
    # yt-dlp should handle most other URLs
    try:
        info_dict = ytdl.extract_info(url, download=False)
    except yt_dlp.utils.DownloadError as e:
        log.info(f'Failed to retrieve title: {e}')
        return None, e
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
    log.debug('Adding reactions...')

    if choices > len(emoji['num']):
        log.debug('Choices out of range for emoji number list.')
        return

    for i in list(range(0, choices)):
        await prompt_msg.add_reaction(emoji['num'][i+1])

    await prompt_msg.add_reaction(emoji['cancel'])

    def check(reaction: discord.Reaction, user: discord.Member) -> bool:
        log.debug('Reaction check is being called...')
        return user == ctx.message.author and (str(reaction.emoji) in emoji['num'] or str(reaction.emoji) == emoji['cancel'])

    log.debug('Waiting for reaction...')

    try:
        reaction, user = await bot.wait_for('reaction_add', timeout=timeout, check=check)
    except asyncio.TimeoutError as e:
        log.info('Choice prompt timeout reached.')
        await prompt_msg.delete()
        return
    except Exception as e:
        log.error(e)
        await prompt_msg.edit(embed=embedq('An unexpected error occurred.'))
        return
    else:
        # If a valid reaction was received.
        log.debug('Received a valid reaction.')

        if str(reaction) == emoji['cancel']:
            log.info('Selection cancelled.')
            await prompt_msg.delete()
            return
        else:
            choice = emoji['num'].index(str(reaction))
            log.info(f'{choice} selected.')
            await prompt_msg.delete()
            return choice

# Establish bot user
intents = discord.Intents.default()
intents.messages = True
intents.message_content = True
intents.voice_states = True
intents.reactions = True
intents.guilds = True
intents.members = True

# Set prefix
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
    else:
        log.info(f'Error encountered in command `{ctx.command}`.')
        log.info(error)
        trace = traceback.format_exception(error)
        await ctx.send(embed=embedq(error, 'If this issue persists, please check https://github.com/svioletg/viMusBot/issues and submit a new issue if your problem is not listed.'))
        # A second traceback is created from this command itself, usually not useful
        log.info(f'Full traceback below.\n\n{plt.error}'+''.join(trace[:trace.index('\nThe above exception was the direct cause of the following exception:\n\n')]))

@bot.event
async def on_ready():
    log.info(f'Logged in as {bot.user} (ID: {bot.user.id})')
    print('-----')
    log.info('Ready!')

# Retrieve bot token
log.info(f'Retrieving token from {plt.blue}{TOKEN_FILE_PATH}')

if not PUBLIC:
    log.info(f'{plt.warn}NOTICE: Starting in dev mode.')

try:
    with open(TOKEN_FILE_PATH, 'r') as f:
        token = f.read()
except FileNotFoundError:
    log.info(f'{plt.error}{f} does not exist; exiting.')
    raise SystemExit(0)

class Tests:
    test_sources = ['youtube', 'spotify', 'bandcamp', 'soundcloud']
    test_urls = {
            'single': {
                'valid': {
                    'youtube':    ['https://www.youtube.com/watch?v=bNpEUbWOBiM', 'https://www.youtube.com/watch?v=3XAhEUHt3zY', 'https://www.youtube.com/watch?v=Q-i1XZc8ZwA'],
                    'spotify':    ['https://open.spotify.com/track/1E2WTcYLP1dFe1tiGDwRmT?si=e83bb1fcb80640ad', 'https://open.spotify.com/track/0WHtcCpZnoyFlQg3Mf2cdN?si=73230e1b24084038', 'https://open.spotify.com/track/56k2ztFw7hQRzDeoe80pJo?si=90310e0adbf0472a'],
                    'bandcamp':   ['https://jeffrosenstock.bandcamp.com/track/graveyard-song', 'https://jeffrosenstock.bandcamp.com/track/9-10', 'https://jeffrosenstock.bandcamp.com/track/leave-it-in-the-sun'],
                    'soundcloud': ['https://soundcloud.com/sethgibbsmusic/rain', 'https://soundcloud.com/weeppiko/like-a-thunder', 'https://soundcloud.com/griffinmcelroy/the-adventure-zone-ethersea-theme']
                },
                'invalid': {
                    'youtube':    ['https://www.youtube.com/watch?v=THISISANINVALIDURLANDDOESNTEXIST'],
                    'spotify':    ['https://open.spotify.com/track/THISISANINVALIDURLANDDOESNTEXIST'],
                    'bandcamp':   ['https://THISISANINVALIDURLANDDOESNTEXIST.bandcamp.com/track/THISISANINVALIDURLANDDOESNTEXIST'],
                    'soundcloud': ['https://soundcloud.com/THISISANINVALIDURLANDDOESNTEXIST/THISISANINVALIDURLANDDOESNTEXIST']
                }
            },
            'playlist': {
                'valid': {
                    'youtube':    ['https://www.youtube.com/playlist?list=PL0uKqjIajhzGshCt76OeXLspFh5MmM-Vu', 'https://www.youtube.com/playlist?list=PL67cMGyeB5sEh3ZjGgo8oXzIrbDggG1gs', 'https://www.youtube.com/playlist?list=OLAK5uy_m-FE5IenHYY2Fd1M2RX-k11yKohFrvZi0'],
                    'spotify':    ['https://open.spotify.com/playlist/7IjLgeYeUkFzNvBirgfsAf?si=c55c2848887249da', 'https://open.spotify.com/playlist/1FkZjVP9O80Chh37YhyKaU?si=d12241575b444d45', 'https://open.spotify.com/playlist/3jlpvgHatDehrSrR72DYVq?si=932b79272c7c4a30'],
                    'bandcamp':   ['https://jeffrosenstock.bandcamp.com/album/hellmode', 'https://jeffrosenstock.bandcamp.com/album/post', 'https://jeffrosenstock.bandcamp.com/album/no-dream'],
                    'soundcloud': ['https://soundcloud.com/sethgibbsmusic/sets/2019-releases', 'https://soundcloud.com/sethgibbsmusic/sets/original-tracks-2020', 'https://soundcloud.com/sethgibbsmusic/sets/remixes']
                },
                'invalid': {
                    'youtube':    ['https://www.youtube.com/playlist?list=THISISANINVALIDURLANDDOESNTEXIST'],
                    'spotify':    ['https://open.spotify.com/playlist/THISISANINVALIDURLANDDOESNTEXIST'],
                    'bandcamp':   ['https://THISISANINVALIDURLANDDOESNTEXIST.bandcamp.com/album/THISISANINVALIDURLANDDOESNTEXIST'],
                    'soundcloud': ['https://soundcloud.com/THISISANINVALIDURLANDDOESNTEXIST/sets/THISISANINVALIDURLANDDOESNTEXIST']
                }
            },
            'album': {
                'valid': {
                    'youtube':    ['https://music.youtube.com/playlist?list=OLAK5uy_lQT8aLCDHiFu4_NkoxHt1VSfUBpjSIwHY', 'https://music.youtube.com/playlist?list=OLAK5uy_kb8kfsyt08s2Z29752CH_lelHdl_JDwgg', 'https://music.youtube.com/playlist?list=OLAK5uy_mp-RVdXLFGSC62WMsBlrqlF3RlZatyowA'],
                    'spotify':    ['https://open.spotify.com/album/1KMfjy6MmPorahRjxhTnxm?si=CS0F1ZFsQqSsn0xH_ahDiA', 'https://open.spotify.com/album/74QTwjBLo1eLqpjL320rXX?si=1ehOqrxBR8WjHftNReHAtw', 'https://open.spotify.com/album/3fn4HfVz5dhmE0PG24rh6h?si=tFUiBS7iSq6QGg-rNNgXkg'],
                    'bandcamp':   ['https://jeffrosenstock.bandcamp.com/album/hellmode', 'https://jeffrosenstock.bandcamp.com/album/post', 'https://jeffrosenstock.bandcamp.com/album/no-dream'],
                    'soundcloud': ['https://soundcloud.com/sethgibbsmusic/sets/2019-releases', 'https://soundcloud.com/sethgibbsmusic/sets/original-tracks-2020', 'https://soundcloud.com/sethgibbsmusic/sets/remixes']
                },
                'invalid': {
                    'youtube':    ['https://music.youtube.com/playlist?list=WROOOOOOOOONGLIIIIIIIIIIIINK'],
                    'spotify':    ['https://open.spotify.com/album/THISISALSOINCORRECTNOTAREALALBUM'],
                    'bandcamp':   ['https://THISISANINVALIDURLANDDOESNTEXIST.bandcamp.com/album/THISISANINVALIDURLANDDOESNTEXIST'],
                    'soundcloud': ['https://soundcloud.com/THISISANINVALIDURLANDDOESNTEXIST/sets/THISISANINVALIDURLANDDOESNTEXIST']
                }
            }
        }

    @classmethod
    async def test_play(self, source: str, bypass_ctx: bool=False, flags: list[str]=[]) -> dict:
        """NOT a completely comprehensive test, but covers most common bases
        
        Valid flags:
        - `invalid` = Use an intentionally invalid URL
        - `multiple` = Use multiple URLs
        - `playlist` = Use a playlist URL
        - `album` = Use an album URL

        "playlist" and "album" can't be used together
        """
        if (not bypass_ctx) and (debugctx is None):
            log.info(f'{plt.warn}Debug context is not set; aborting test. Use the "dctx" bot command while in a voice channel to grab one.')
            return
        
        if source not in self.test_sources + ['any', 'mixed']:
            log.info(f'{plt.warn}Invalid source; aborting test. Valid sources are: {', '.join(self.test_sources)}')
            return

        valid: str|bool = 'invalid' if 'invalid' in flags else 'valid'
        playlist_or_album: str|bool = 'playlist' if 'playlist' in flags else 'album' if 'album' in flags else False
        multiple_urls: bool = 'multiple' in flags

        passed: bool = False
        conclusion: str = ''
        arguments: str = f'SOURCE? {source} | VALID? {valid} | MULTIPLE? {multiple_urls} | PLAYLIST/ALBUM? {playlist_or_album}'

        log.info(f'{plt.gold}### START TEST! play command; {arguments}')

        if 'playlist' in flags and 'album' in flags:
            log.info(f'{plt.warn}Invalid flags; aborting test. The "playlist" and "album" flags cannot be used together.')
            return

        src = random.choice(self.test_sources) if source in ['any', 'mixed'] else source
        url_type = playlist_or_album if playlist_or_album else 'single'

        await Music.ensure_voice(Music, debugctx)
        if not multiple_urls:
            await Music.play(Music, debugctx, random.choice(self.test_urls[url_type][valid][src]))
            if voice.is_playing():
                conclusion = f'voice client is playing. Test likely {plt.green}passed.'
                log.info(conclusion); passed = True
            else:
                if valid == 'invalid':
                    conclusion = f'voice client is not playing, and an intentionally invalid URL was used. Test likely {plt.green}passed.'
                    log.info(conclusion); passed = True
                else:
                    conclusion = f'voice client is not playing, but a valid URL was used. Test likely {plt.red}failed.'
                    log.info(conclusion)
        else:
            urls = []
            if source == 'mixed':
                for s in self.test_sources:
                    urls.append(random.choice(self.test_urls[url_type][valid][s]))
            else:
                urls = self.test_urls[url_type][valid][src]
            
            await Music.play(Music, debugctx, *urls)
            if voice.is_playing() and media_queue.get(debugctx) != []:
                conclusion = f'Voice client is playing and the queue is not empty. Test likely {plt.green}passed.'
                log.info(conclusion); passed = True
            else:
                if valid == 'invalid':
                    conclusion = f'Voice client is not playing, and an intentionally invalid URL was used. Test likely {plt.green}passed.'
                    log.info(conclusion); passed = True
                elif playlist_or_album:
                    conclusion = f'Voice client is not playing, all URLs were valid, but multiple {playlist_or_album} URLs were used. Test likely {plt.green}passed.'
                    log.info(conclusion); passed = True
                elif media_queue.get(debugctx) != []:
                    conclusion = f'Voice client is not playing, but the queue is not empty. Test likely {plt.red}failed.'
                    log.info(conclusion)
                else:
                    conclusion = f'Voice client is not playing, but all valid URLs were used. Test likely {plt.red}failed.'
                    log.info(conclusion)
        
        log.info(f'Waiting 2 seconds...')
        time.sleep(2)
        log.info(f'Clearing media queue and stopping voice client...')
        media_queue.clear(debugctx)
        voice.stop()
        log.info(f'Waiting 2 seconds...')
        time.sleep(2)
        log.info(f'{plt.gold}### END TEST!')
        return {'passed': passed, 'arguments': arguments, 'conclusion': conclusion}

# Begin main thread

async def console():
    log.info('Console is active.')
    while True:
        try:
            user_input: str = await aioconsole.ainput('')
            user_input = user_input.lower().strip()
            if user_input == '':
                continue

            # Console debugging commands
            if user_input.startswith('test'):
                if PUBLIC:
                    print('Debugging commands are disabled in public mode.')
                    continue
                
                # TODO: Some sort of help command would be good
                params = user_input.split()

                if params[1] == 'play':
                    if len(params) < 3:
                        print('Not enough arguments. Usage: test play <source> [flags] (available flags: invalid, multiple, playlist, album)')
                        print('You can also use "test play all" to run every combination of this test. This can take several minutes.')
                        continue
                    if params[2] != 'all':
                        test_start = time.time()
                        result = await Tests.test_play(params[2], flags=params[3:])
                        if result is None:
                            # Returns None if the test was aborted
                            continue
                        print(f'{plt.gold}ARGS: {result["arguments"]} {plt.reset}\n{result["conclusion"]}')
                        test_end = time.time()
                        print(f'Test finished in {plt.magenta}{test_end - test_start}s')
                    elif params[2] == 'all':
                        # Run full test suite of all combinations
                        confirmation = await aioconsole.ainput('> About to run every combination of -play test. This could take several minutes. Continue? (y/n) ')
                        if confirmation.lower() != 'y':
                            print('> Aborted.')
                            continue

                        test_results: dict[str, list] = {'pass': [], 'fail': []}
                        test_result_string: str = ''
                        def add_test_result(result: tuple[bool, dict]):
                            nonlocal test_results, test_result_string
                            test_result_string += f'{f'{plt.green}PASS' if result['passed'] else f'{plt.red}FAIL'} | ARGS: {result['arguments']}\n'
                            if result['passed']:
                                test_results['pass'].append((result['arguments'], result['conclusion']))
                            else: 
                                test_results['fail'].append((result['arguments'], result['conclusion']))
                        
                        test_sources: list[str] = Tests.test_sources + ['any', 'mixed']
                        test_start: float = time.time()
                        tests_run: int = 0
                        # Go through all test combinations
                        try:
                            # 'invalid', 'single', and 'no-list' will be skipped over by the test function
                            # They're just here to make generating the combinations easier
                            test_conditions = itertools.product(
                                test_sources, 
                                ['valid', 'invalid'], 
                                ['single', 'multiple'], 
                                ['no-list', 'playlist', 'album']
                                )
                            for src, valid, multiple_urls, playlist_or_album in test_conditions:
                                add_test_result(await Tests.test_play(src, flags=[valid, multiple_urls, playlist_or_album]))
                                tests_run += 1
                                log.info(f'{plt.blue}{tests_run}{plt.reset} tests run, of which '+
                                    f'{plt.green}{len(test_results['pass'])} have passed, and '+
                                    f'{plt.red}{len(test_results['fail'])} have failed.'
                                    )
                        except Exception as e:
                            log.error(e)
                            log.info(f'{plt.red}Traceback encountered, tests aborted.')

                        test_end: float = time.time()
                        test_duration: float = math.floor(test_end - test_start)

                        print(f'Finished {plt.blue}{tests_run}{plt.reset} tests.')
                        # print(test_result_string)
                        print(f'FINISHED IN {plt.magenta}{timestamp_from_seconds(test_duration)} or {test_duration}s{plt.reset} | PASS/FAIL: {plt.green}{len(test_results['pass'])}{plt.reset}/{plt.red}{len(test_results['fail'])}')
                        if test_results['fail'] != []:
                            print('FAILED TESTS:')
                            for arguments, conclusion in test_results['fail']:
                                print(f'ARGS: {plt.gold}{arguments}\n{plt.reset}{conclusion}')
                        else:
                            print(f'{plt.green}ALL TESTS PASSED')
            else:
                match user_input:
                    case 'colors':
                        plt.preview(); print()
                    case 'stop':
                        log.info('Leaving voice if connected...')
                        try:
                            await voice.disconnect()
                        except:
                            pass
                        log.info('Cancelling bot task...')
                        bot_task.cancel()
                        log.info('Cancelling console task...')
                        console_task.cancel()
                    case _:
                        log.info(f'Unrecognized command "{user_input}"')
        except Exception as e:
            log.info('Error encountered in console thread!')
            log.error(e)

async def bot_thread():
    log.info('Starting bot thread...')
    async with bot:
        await bot.add_cog(General(bot))
        await bot.add_cog(Music(bot))
        log.info('Logging in with token...')
        await bot.start(token)

async def main():
    global bot_task, console_task

    bot_task = asyncio.create_task(bot_thread())
    console_task = asyncio.create_task(console())
    await asyncio.gather(bot_task, console_task)

if __name__ == '__main__':
    asyncio.run(main())
