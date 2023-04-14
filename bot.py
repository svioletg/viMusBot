print('Getting ready...')

# Import sys out of order to print the Python version, for troubleshooting
import sys

print('python '+sys.version)

import asyncio
import glob
import importlib
import logging
import os
import pickle
import random
import shutil
import subprocess
import sys
import time
import traceback
import urllib.request
from datetime import datetime, timedelta
from inspect import currentframe, getframeinfo

import colorama
import discord
import pytube
import regex as re
import yaml
import yt_dlp
from colorama import Back, Fore, Style
from discord.ext import commands
from pretty_help import DefaultMenu, PrettyHelp

print('Checking for config...')

if not os.path.isfile('config_default.yml'):
	print('config_default.yml not found; downloading...')
	urllib.request.urlretrieve('https://raw.githubusercontent.com/svioletg/viMusBot/master/config_default.yml','config_default.yml')

if not os.path.isfile('config.yml'):
	print('config.yml does not exist. It will be created as a duplicate of config_default.yml')
	shutil.copyfile('config_default.yml', 'config.yml')

with open('config_default.yml','r') as f:
	config_default = yaml.safe_load(f)

with open('config.yml','r') as f:
	config = yaml.safe_load(f)

# Import local files after main packages, and after validating config
import customlog
import spoofy
import update
from palette import Palette

_here = os.path.basename(__file__)

# For personal reference
# Represents the version of the overall project, not just this file
with open('version.txt','r') as f:
	version = f.read().strip()

# Start discord logging
handler = logging.FileHandler(filename='discord.log', encoding='utf-8', mode='w')
discord.utils.setup_logging(handler=handler, level=logging.INFO, root=False)

# Start bot logging
colorama.init(autoreset=True)
plt = Palette()

last_logtime = time.time()

def log(msg: str, verbose=False):
	global last_logtime
	customlog.newlog(msg=msg, last_logtime=last_logtime, called_from=sys._getframe().f_back.f_code.co_name, verbose=verbose)
	last_logtime = time.time()

def log_traceback(error: BaseException):
	trace=traceback.format_exception(error)
	log(f'Full traceback below.\n\n{plt.error}'+''.join(trace[:trace.index('\nThe above exception was the direct cause of the following exception:\n\n')]))

def log_line():
	cf = currentframe()
	print('@ LINE ', cf.f_back.f_lineno)

log(f'Running on version {version}.')

update_check = update.check()

# Check for an outdated version.txt
if update_check[0] == False and update_check[1]:
	log(f'{plt.warn}There is a new release available.')
	current_tag = update_check[1]['current']
	latest_tag = update_check[1]['latest']['tag_name']
	log(f'Current: {plt.gold}{current_tag}{plt.reset} | Latest: {plt.lime}{latest_tag}')
	log('Use "update.py" to update.')
else:
	log(f'{plt.lime}You are up to date.')

log('Changelog: https://github.com/svioletg/viMusBot/blob/master/changelog.md')

log('Starting...')

# Parse config from YAML
with open('config.yml','r') as f:
	config = yaml.safe_load(f)

allow_spotify_playlists = config['allow-spotify-playlists']
spotify_playlist_limit = config['spotify-playlist-limit']
use_top_match = config['use-top-match']
duration_limit = config['duration-limit']

public = config['public']
token_file_path = config['token-file']
public_prefix = config['prefixes']['public']
dev_prefix = config['prefixes']['developer']
inactivity_timeout = config['inactivity-timeout']
cleanup_extensions = config['auto-remove']

vote_to_skip = config['vote-to-skip']['enabled']
skip_votes_type = config['vote-to-skip']['threshold-type']
skip_votes_exact = config['vote-to-skip']['threshold-exact']
skip_votes_percentage = config['vote-to-skip']['threshold-percentage']
skip_votes_needed = 0
skip_votes = []

show_users_in_queue = config['show-users-in-queue']

def is_command_enabled(ctx):
	return not ctx.command.name in config['command-blacklist']

def get_aliases(command: str):
	return config['aliases'].get(command,[])

# Clear out downloaded files
log('Removing previously downloaded files...')
files = glob.glob('*.*')
to_remove = [f for f in files if re.search(r'\.(\w+)(?!.*\.)',f)[0] in cleanup_extensions]
for i in to_remove:
	os.remove(i)
del files, to_remove

def embedq(*args) -> discord.Embed:
	"""Shortcut for making new embeds"""
	if len(args) == 1:
		return discord.Embed(title=args[0], color=0xFFFF00)
	elif len(args) == 2:
		return discord.Embed(title=args[0], description=args[1], color=0xFFFF00)

# Based on and adapted from:
# https://github.com/Rapptz/discord.py/blob/v2.0.1/examples/basic_voice.py

# For easier emoji usage
emoji = {
	'cancel':'❌',
	'confirm':'✅',
	'repeat':'🔁',
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

ffmpeg_options = {
	'options': '-vn',
}

ytdl = yt_dlp.YoutubeDL(ytdl_format_options)

def length_from_url(url):
	log(f'Fetching length of \'{url}\'...', verbose=True)
	if 'youtube.com' in url:
		try:
			return pytube.YouTube(url).length
		except Exception as e:
			log(f'pytube encountered "{e}" during length retrieval. Falling back on yt-dlp.', verbose=True)
			info_dict = ytdl.extract_info(url, download=False)
			return info_dict.get('duration', None)
	elif 'soundcloud.com' in url:
		return round(spoofy.sc.resolve(url).duration / 1000)
	elif 'open.spotify.com' in url:
		return spoofy.spotify_track(url)['duration']
	else:
		# yt-dlp should handle most URLs
		info_dict = ytdl.extract_info(url, download=False)
		return info_dict.get('duration', None)

def title_from_url(url):
	log(f'Fetching title of \'{url}\'...', verbose=True)
	if 'youtube.com' in url:
		try:
			return pytube.YouTube(url).title
		except Exception as e:
			log(f'pytube encountered "{e}" during title retrieval. Falling back on yt-dlp.', verbose=True)
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

class YTDLSource(discord.PCMVolumeTransformer):
	def __init__(self, source, *, data, volume=0.5):
		super().__init__(source,volume)

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
			print('error in from_url')
			print(e)
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

voice = None

class General(commands.Cog):
	def __init__(self, bot):
		self.bot = bot

	# Adapted from: https://stackoverflow.com/a/68599108/8108924
	@commands.Cog.listener()
	async def on_voice_state_update(self, member, before, after):
		global voice
		if not member.id == self.bot.user.id:
			return
		elif before.channel is None:
			# Disconnect after set amount of inactivity
			if inactivity_timeout == 0:
				return
			timeout_counter = 0
			while True:
				await asyncio.sleep(1)
				timeout_counter += 1
				if voice.is_playing() and not voice.is_paused():
					timeout_counter = 0
					global audio_time_elapsed
					audio_time_elapsed += 1
				
				if timeout_counter == inactivity_timeout*60:
					log('Leaving voice due to inactivity.')
					await voice.disconnect()
				if not voice.is_connected():
					voice = None
					break

	@commands.command()
	@commands.check(is_command_enabled)
	async def reload(self, ctx):
		# Separated from the others for debug purposes
		global spoofy
		spoofy = importlib.reload(spoofy)
		log('Reloaded spoofy.py.')
	
	@commands.command()
	@commands.check(is_command_enabled)
	async def stream(self, ctx):
		print(voice.source)
		print(dir(voice.source))

	@commands.command(aliases=get_aliases('changelog'))
	@commands.check(is_command_enabled)
	async def changelog(self, ctx):
		"""Returns a link to the changelog, and displays most recent version."""
		embed=discord.Embed(title='Read the changelog here: https://github.com/svioletg/viMusBot/blob/master/changelog.md',description=f'Current version: {version}',color=0xFFFF00)
		await ctx.send(embed=embed)

	@commands.command(aliases=get_aliases('ping'))
	@commands.check(is_command_enabled)
	async def ping(self, ctx):
		"""Test command."""
		await ctx.send('Pong!')
		embed=discord.Embed(title='Pong!',description='Pong!',color=0xFFFF00)
		await ctx.send(embed=embed)
		await ctx.send(embed=embedq('this is a test for','the extended embed function'))

	@commands.command(aliases=get_aliases('repository'))
	@commands.check(is_command_enabled)
	async def repository(self, ctx):
		"""Returns the link to the viMusBot GitHub repository."""
		embed=discord.Embed(title='You can view the bot\'s code and submit bug reports or feature requests here.',description='https://github.com/svioletg/viMusBot\nA GitHub account is required to submit issues.',color=0xFFFF00)
		await ctx.send(embed=embed)


class Music(commands.Cog):
	def __init__(self, bot):
		self.bot = bot

	# Playing music / Voice-related
	@commands.command(aliases=get_aliases('analyze'))
	@commands.check(is_command_enabled)
	async def analyze(self, ctx, spotifyurl: str):
		"""Returns spotify API information regarding a track."""
		info = spoofy.spotify_track(spotifyurl)
		title = info['title']
		artist = info['artist']
		result = spoofy.analyze_track(spotifyurl)
		data = result[0]
		skip = result[1]
		# Assemble embed object
		embed = discord.Embed(title=f'Spotify data for {title} by {artist}', description='Things like key, tempo, and time signature are estimated, and therefore not necessarily accurate.', color=0xFFFF00)
		# Put key, time sig, and tempo at the top
		embed.add_field(name='Key',value=data['key']); data.pop('key')
		embed.add_field(name='Tempo',value=data['tempo']); data.pop('tempo')
		embed.add_field(name='Time Signature',value=data['time_signature']); data.pop('time_signature')

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
	async def clear(self, ctx):
		"""Clears the entire queue."""
		global player_queue
		player_queue.clear(ctx)
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
	async def leave(self, ctx):
		"""Disconnects the bot from voice."""
		global voice
		global player_queue
		player_queue.clear(ctx)
		log(f'Leaving voice channel: {ctx.author.voice.channel}')
		try:
			await voice.disconnect()
		except AttributeError:
			await ctx.send(embed=embedq('Not connected to voice.'))
		voice = None

	@commands.command(aliases=get_aliases('loop'))
	@commands.check(is_command_enabled)
	async def loop(self, ctx):
		"""Toggles looping for the current track."""
		global loop_this
		# Inverts the boolean
		loop_this = not loop_this
		await ctx.send(embed=embedq(f'{get_loop_icon()}Looping is set to {loop_this}.'))

	@commands.command(aliases=get_aliases('move'))
	@commands.check(is_command_enabled)
	async def move(self, ctx, old: int, new: int):
		"""Moves a queue item from <old> to <new>."""
		try:
			to_move = player_queue.get(ctx)[old-1].title
			player_queue.get(ctx).insert(new-1, player_queue.get(ctx).pop(old-1))
			await ctx.send(embed=embedq(f'Moved {to_move} to #{new}.'))
		except IndexError as e:
			await ctx.send(embed=embedq('The selected number is out of range.'))
			print(e)
			raise e
		except Exception as e:
			await ctx.send(embed=embedq('An unexpected error occurred.'))
			print(e)
			raise e

	@commands.command(aliases=get_aliases('nowplaying'))
	@commands.check(is_command_enabled)
	async def nowplaying(self, ctx):
		"""Displays the currently playing video."""
		if voice == None:
			await ctx.send(embed=embedq('Not connected to a voice channel.'))
			return

		if not voice.is_playing() and not voice.is_paused():
			embed = discord.Embed(title=f'Nothing is playing.',color=0xFFFF00)
		else:
			nowtime = time.time()
			# global paused_for
			# if voice.is_paused():
			# 	paused_for = (nowtime - paused_at) if paused_at > 0 else 0

			elapsed = time.strftime('%M:%S', time.gmtime(audio_time_elapsed))
			submitter_text = f'\nQueued by {now_playing.user}' if show_users_in_queue else ''
			embed = discord.Embed(title=f'{get_loop_icon()}Now playing: {now_playing.title} [{elapsed} / {now_playing.length}]',description=f'Link: {now_playing.weburl}{submitter_text}\nElapsed time may not be precisely accurate, due to minor network hiccups.',color=0xFFFF00)

		await ctx.send(embed=embed)

	@commands.command(aliases=get_aliases('pause'))
	@commands.check(is_command_enabled)
	async def pause(self, ctx):
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
	async def play(self, ctx, *, url: str):
		"""Adds a link to the queue. Plays immediately if the queue is empty."""
		# Will resume if paused, this is handled in on_command_error()
		global playctx
		playctx = ctx
		global qmessage
		if 'soundcloud.com' in url:
			qmessage = await ctx.send(
				embed=embedq(
				'Trying to queue...',
				'Note: It is a known issue that SoundCloud links will sometimes fail to queue.'+
				'\nIf you receive an error, try it again.'+
				'\nDetails: https://github.com/svioletg/viMusBot/issues/16'
				)
			)
		else:
			qmessage = await ctx.send(embed=embedq('Trying to queue...'))

		url = url.split('&list=')[0]
		async with ctx.typing():
			# Locate youtube equivalent if spotify link given
			if 'open.spotify.com' in url:
				log('Spotify URL was received from play command.', verbose=True)
				log('Checking for playlist...', verbose=True)
				if '/playlist/' in url and allow_spotify_playlists:
					log('Spotify playlist detected.', verbose=True)
					await qmessage.edit(embed=embedq('Trying to queue Spotify playlist...'))

					objlist = generate_QueueItems(spoofy.spotify_playlist(url), ctx.author)
					if len(objlist) > spotify_playlist_limit:
						await qmessage.edit(embed=embedq('Spotify playlist limit exceeded.'))
						return
					
					queue_batch(ctx, objlist)
					list_name = spoofy.sp.playlist(url)['name']
					await qmessage.edit(embed=embedq(f'Queued {len(objlist)} items from {list_name}.'))

					if not voice.is_playing():
						log('Voice client is not playing; starting...')
						await advance_queue(ctx)
					return
				elif not allow_spotify_playlists:
					await ctx.send(embed=embedq(
						'Spotify playlists are currently disabled in this bot\'s configuration.',
						'Contact whoever is hosting your bot if you believe this is a mistake.'
						)
					)
					return

				log('Checking for album...', verbose=True)
				if '/album/' in url:
					log('Spotify album detected.', verbose=True)
					album_info = spoofy.spotify_album(url)
					url = spoofy.search_ytmusic_album(album_info['title'], album_info['artist'], album_info['year'])
					if url == None:
						await ctx.send(embed=embedq('No match could be found.'))
						return
			
			# Search with text if no url is provided
			if 'https://' not in ctx.message.content:
				log('Link not detected, searching by text', verbose=True)
				log(f'Searching: "{url}"')

				options = spoofy.search_ytmusic_text(url)

				top_song_title = options[0]['title']
				top_song_url = 'https://www.youtube.com/watch?v='+options[0]['videoId']

				top_video_title = options[1]['title']
				top_video_url = 'https://www.youtube.com/watch?v='+options[1]['videoId']

				if top_song_url == top_video_url:
					url = top_song_url
				else:
					embed=discord.Embed(title='Please choose an option:',color=0xFFFF00)
					embed.add_field(name=f'Top song result: {top_song_title}', value=top_song_url, inline=False)
					embed.add_field(name=f'Top video result: {top_video_title}', value=top_video_url, inline=False)

					prompt = await ctx.send(embed=embed)
					choice = await prompt_for_choice(ctx, qmessage, prompt, 2)
					if choice == None:
						return
					url = 'https://www.youtube.com/watch?v='+options[choice-1]['videoId']

			# Determines if the input was a playlist
			valid = ['playlist?list=', '/sets/', '/album/']
			if any(i in url for i in valid):
				log('URL is a playlist.', verbose=True)
				objlist = generate_QueueItems(url, ctx.author)
				queue_batch(ctx, objlist)
				await ctx.send(embed=embedq(f'Queued {len(objlist)} items.'))
				if not voice.is_playing() and len(player_queue.get(ctx)) == 0:
					await advance_queue(ctx)
				return
			else:
				# Runs if the input given was not a playlist
				log('URL is not a playlist.', verbose=True)
				log('Checking duration...', verbose=True)
				# Try pytube first as it's faster
				if 'https://www.youtube.com' in url:
					try:
						yt_length = pytube.YouTube(url).length
					except TypeError:
						yt_length = ytdl.extract_info(url, download=False)['duration']
					if yt_length > duration_limit*60*60:
						log('Item over duration limit; not queueing.')
						await qmessage.edit(embed=embedq(f'Cannot queue items longer than {duration_limit} hours.'))
						return
				else:
					if 'open.spotify.com' in url:
						duration = spoofy.sp.track(url)['duration_ms']/1000
					else:
						ytdl_extracted = ytdl.extract_info(url,download=False)
						try:
							duration = ytdl_extracted['duration']
						# 'duration' is not retrieved from the generic extractor used for direct links
						except KeyError as e:
							# I'd like to avoid executing something outside of the script here,
							# but I couldn't find any library for ffprobe
							ffprobe = f'ffprobe {url} -v quiet -show_entries format=duration -of csv=p=0'.split(' ')
							duration = float(subprocess.check_output(ffprobe).decode('utf-8').split('.')[0])

					if duration > duration_limit*60*60:
						log('Item over duration limit; not queueing.')
						await qmessage.edit(embed=embedq(f'Cannot queue items longer than {duration_limit} hours.'))
						return

			# Start the player if we can use the url itself
			try:
				log('Trying to start playing or queueing.', verbose=True)
				if not voice.is_playing() and len(player_queue.get(ctx)) == 0:
					log('Voice client is not playing; starting...')
					await play_url(url, ctx, ctx.author)
				else:
					player_queue.get(ctx).append(QueueItem(url, ctx.author))
					title = player_queue.get(ctx)[-1].title
					await qmessage.edit(embed=embedq(f'Added {title} to the queue at spot #{len(player_queue.get(ctx))}'))
					log('Appened to queue.')
			except Exception as e:
				raise e

	# @commands.command(aliases=get_aliases('playlist'))
	# @commands.check(is_command_enabled)
	# async def playlist(self, ctx, mode):
	# 	"""Saves or loads a playlist queue."""
	# 	if mode not in ['save', 'load']:
	# 		await ctx.send(embed=embedq('Command structure must be `playlist [save|load] [name]`'))

	# @commands.command(aliases=get_aliases('qstore'))
	# @commands.check(is_command_enabled)
	# async def qstore(self, ctx):
	# 	"""Stores a playlist object as a file."""
	# 	try:
	# 		with open('queue.pickle', 'wb') as f:
	# 			pickle.dump(player_queue, f)
			
	# 		await ctx.send('Current queue saved. Use `-qload` to restore it.')
	# 	except Exception as e:
	# 		log_traceback(e)
	# 		await ctx.send(embed=embedq('Queue could not be saved.', e))

	# @commands.command(aliases=get_aliases('qload'))
	# @commands.check(is_command_enabled)
	# async def qload(self, ctx, clear_existing=False):
	# 	"""Loads a playlist object from the file."""
	# 	try:
	# 		msg = await ctx.send(embed=embedq('This will clear and overwrite the current queue. Continue?', '1 for no, 2 for yes'))
	# 		choice = await prompt_for_choice(ctx, msg, msg, 2)
	# 		if choice == 2:
	# 			with open('queue.pickle', 'rb') as f:
	# 				global player_queue
	# 				player_queue = pickle.load(f)
			
	# 		await ctx.send('Queue has been loaded and restored.')
	# 	except Exception as e:
	# 		log_traceback(e)
	# 		await ctx.send(embed=embedq('Queue could not be restored.', e))

	@commands.command(aliases=get_aliases('queue'))
	@commands.check(is_command_enabled)
	async def queue(self, ctx, page: int=1):
		"""Displays the current queue, up to #10."""
		if player_queue.get(ctx) == []:
			await ctx.send(embed=embedq('The queue is empty.'))
			return

		queue_time = 0
		for i in player_queue.get(ctx):
			queue_time += i.length
		
		queue_time = readable_time(queue_time)

		embed = discord.Embed(title=f'Current queue:\n*Approx. time remaining: {queue_time}*',color=0xFFFF00)
		start = (10*page)-10
		end = (10*page)
		if 10*page>len(player_queue.get(ctx)):
			end = len(player_queue.get(ctx))
		
		for num, i in enumerate(player_queue.get(ctx)[start:end]):
			submitter_text = f'\nQueued by {i.user}' if show_users_in_queue else ''
			embed.add_field(name=f'#{num+1+start}. {i.title} [{readable_time(i.length)}]', value=f'Link: {i.url}{submitter_text}', inline=False)

		try:
			embed.description = (f'Showing {start+1} to {end} of {len(player_queue.get(ctx))} items. Use -queue [page] to see more.')
		except Exception as e:
			print(e)
			raise e
		await ctx.send(embed=embed)

	@commands.command(aliases=get_aliases('remove'))
	@commands.check(is_command_enabled)
	async def remove(self, ctx, spot: int):
		"""Removes an item from the queue. Use -q to get its number."""
		await ctx.send(embed=embedq(f'Removed {player_queue.get(ctx).pop(spot-1).title} from the queue.'))

	@commands.command(aliases=get_aliases('shuffle'))
	@commands.check(is_command_enabled)
	async def shuffle(self, ctx):
		"""Randomizes the order of the queue."""
		random.shuffle(player_queue.get(ctx))
		await ctx.send(embed=embedq('Queue has been shuffled.'))

	@commands.command(aliases=get_aliases('skip'))
	@commands.check(is_command_enabled)
	async def skip(self, ctx):
		"""Skips the currently playing media."""
		if voice == None:
			await ctx.send(embed=embedq('Not connected to a voice channel.'))
			return
		elif not voice.is_playing() and len(player_queue.get(ctx)) == 0:
			await ctx.send(embed=embedq('Nothing to skip.'))
			return

		# Update number skip votes required based on members joined in voice channel
		global skip_votes
		global skip_votes_needed
		skip_votes_needed = int((len(voice.channel.members)) * (skip_votes_percentage/100)) if skip_votes_type == "percentage" else skip_votes_exact

		if not vote_to_skip:
			await ctx.send(embed=embedq('Skipping...'))
			await advance_queue(ctx, skip=True)
		else:
			if ctx.author not in skip_votes:
				skip_votes.append(ctx.author)
			else:
				await ctx.send(embed=embedq('You have already voted to skip.'))
				return

			await ctx.send(embed=embedq(f'Voted to skip. {len(skip_votes)}/{skip_votes_needed} needed.'))
			if len(skip_votes) >= skip_votes_needed:
				await ctx.send(embed=embedq('Skipping...'))
				voice.pause()
				await advance_queue(ctx, skip=True)

	@commands.command(aliases=get_aliases('stop'))
	@commands.check(is_command_enabled)
	async def stop(self, ctx):
		"""Stops the player and clears the queue."""
		global player_queue
		player_queue.clear(ctx)
		if voice.is_playing() or voice.is_paused():
			voice.stop()
			await ctx.send(embed=embedq('Player has been stopped.'))
		else:
			await ctx.send(embed=embedq('Nothing is playing.'))

	@join.before_invoke
	@play.before_invoke
	@pause.before_invoke
	@stop.before_invoke
	async def ensure_voice(self, ctx):
		if ctx.voice_client is None:
			if ctx.author.voice:
				log(f'Joining voice channel: {ctx.author.voice.channel}')
				global voice
				voice = await ctx.author.voice.channel.connect()
			else:
				await ctx.send(embed=embedq("You are not connected to a voice channel."))

# 
# 
# End of cog definitions.
# 
# 

# Misc. helper functions
def readable_time(seconds: int|float) -> str:
	return time.strftime('%M:%S', time.gmtime(seconds))

async def prompt_for_choice(ctx, status_msg: discord.Message, prompt_msg: discord.Message, choices: int, timeout=30) -> int:
	"""Adds reactions to a given Message (prompt_msg) and returns the outcome
	
	msg -- Message to be edited based on the outcome

	prompt -- Message to add the reaction choices to
	"""
	# Get reaction menu ready
	log('Adding reactions.', verbose=True)

	if choices > len(emoji['num']): log('Choices out of range for emoji number list.'); return

	for i in list(range(0, choices)):
		await prompt_msg.add_reaction(emoji['num'][i+1])

	await prompt_msg.add_reaction(emoji['cancel'])

	def check(reaction, user):
		log('Reaction check is being called.', verbose=True)
		return user == ctx.message.author and (str(reaction.emoji) in emoji['num'] or str(reaction.emoji)==emoji['cancel'])

	log('Checking for reaction...', verbose=True)

	try:
		reaction, user = await bot.wait_for('reaction_add', timeout=timeout, check=check)
	except asyncio.TimeoutError as e:
		log('Choice prompt timeout reached.')
		embed=discord.Embed(title='Timed out; cancelling.',color=0xFFFF00)
		await status_msg.edit(embed=embed)
		await prompt_msg.delete()
		return
	except Exception as e:
		log_traceback(e)
		embed=discord.Embed(title='An unexpected error occurred; cancelling.',color=0xFFFF00)
		await status_msg.edit(embed=embed)
		await prompt_msg.delete()
		return
	else:
		# If a valid reaction was received.
		log('Received a valid reaction.', verbose=True)

		if str(reaction)==emoji['cancel']:
			log('Selection cancelled.', verbose=True)
			embed=discord.Embed(title='Cancelling.',color=0xFFFF00)
			await status_msg.edit(embed=embed)
			await prompt_msg.delete()
			return
		else:
			choice = emoji['num'].index(str(reaction))
			log(f'{choice} selected.', verbose=True)
			embed=discord.Embed(title=f'#{choice} chosen.',color=0xFFFF00)
			await status_msg.edit(embed=embed)
			await prompt_msg.delete()
			return choice

# Queue system

class MediaQueue(object):
	def __init__(self):
		self.queues = {}

	# Run in every function to automatically determine
	# which queue we're working with
	def ensure_queue_exists(self, ctx):
		if ctx.author.guild.id not in self.queues:
			self.queues[ctx.author.guild.id] = []

	def get(self, ctx):
		self.ensure_queue_exists(ctx)
		return self.queues[ctx.author.guild.id]

	def set(self, ctx, new_list: list):
		self.ensure_queue_exists(ctx)
		self.queues[ctx.author.guild.id] = new_list

	def clear(self, ctx):
		self.ensure_queue_exists(ctx)
		self.queues[ctx.author.guild.id] = []

player_queue = MediaQueue()

class QueueItem(object):
	def __init__(self, url, user, length=None, title=None):
		self.url = url
		self.user = user
		self.length = length if length is not None else length_from_url(url)
		self.title = title if title is not None else title_from_url(url)

def generate_QueueItems(playlist: str|list, user) -> list:
	objlist = []
	# Will be a list if origin is Spotify
	if type(playlist) == list:
		objlist = [QueueItem(i['url'], user, title=i['title'], length=i['duration']) for i in playlist]
		return objlist
	else:
		# Anything youtube-dl natively supports is probably a link
		if 'soundcloud.com' in playlist:
			# SoundCloud playlists have to be processed differently
			playlist_entries = spoofy.soundcloud_playlist(playlist)
			objlist = [QueueItem(i.permalink_url, user, title=i.title, length=round(i.duration/1000)) for i in playlist_entries]
		else:
			playlist_entries = ytdl.extract_info(playlist, download=False)
			objlist = [QueueItem(i['url'], user, title=i['title'], length=i['duration']) for i in playlist_entries['entries']]
		return objlist

def queue_batch(ctx, batch: list[QueueItem]):
	# batch must be a list of QueueItem objects
	global player_queue
	for i in batch:
		player_queue.get(ctx).append(i)

now_playing = None
last_played = None

npmessage = None

audio_start_time = 0
audio_time_elapsed = 0
paused_at = 0
paused_for = 0

loop_this = False

async def play_url(url: str, ctx, user):
	global audio_start_time, audio_time_elapsed, paused_at, paused_for
	global last_played
	global now_playing
	global npmessage
	global skip_votes

	skip_votes = []

	audio_time_elapsed, paused_at, paused_for = 0, 0, 0
	last_played = now_playing

	log('Trying to start playing...')
	# Check if we need to match a Spotify link
	if 'open.spotify.com' in url:
		log('Trying to match Spotify track...')
		qmessage = await ctx.send(embed=embedq(f'Spotify link detected, searching YouTube...','Please wait; this may take a while!\nIf this has been stuck for a while, use the skip command.'))
		spyt = spoofy.spyt(url)

		log('Checking if unsure...', verbose=True)
		if type(spyt) == tuple and spyt[0] == 'unsure':
			# This indicates no match was found
			log('spyt returned unsure.', verbose=True)
			# Remove the warning, no longer needed
			spyt = spyt[1]
			# Shorten to {limit} results
			limit = 5
			spyt = dict(list(spyt.items())[:limit])
			if use_top_match:
				# Use first result if that's set in config
				spyt = spyt[0]
			else:
				# Otherwise, prompt the user with choice
				embed = discord.Embed(title='No exact match found; please choose an option.',description=f'Select the number with reactions or use {emoji["cancel"]} to cancel.',color=0xFFFF00)
				
				for i in spyt:
					title = spyt[i]['title']
					url = spyt[i]['url']
					artist = spyt[i]['artist']
					album = spyt[i]['album']
					if artist=='': embed.add_field(name=f'{i+1}. {title}',value=url,inline=False)
					else: embed.add_field(name=f'{i+1}. {title}\nby {artist} - {album}',value=url,inline=False)

				prompt = await ctx.send(embed=embed)
				choice = await prompt_for_choice(ctx, qmessage, prompt, len(spyt))
				if choice == None:
					await advance_queue(ctx)
					return
				spyt = spyt[choice-1]
		url = spyt['url']

	# Start the player
	try:
		player = await YTDLSource.from_url(url, loop=bot.loop, stream=False)
	except yt_dlp.utils.DownloadError as e:
		await ctx.send(embed=embedq('This video is unavailable.',url))
		await advance_queue(ctx)
		return

	now_playing = player
	now_playing.weburl = url
	now_playing.user = user
	try:
		now_playing.length = time.strftime('%M:%S', time.gmtime(pytube.YouTube(now_playing.weburl).length))
	except Exception as e:
		log(f'Falling back on yt-dlp. (Cause: {e})', verbose=True)
		now_playing.length = time.strftime('%M:%S', time.gmtime(ytdl.extract_info(now_playing.weburl, download=False)['duration']))
	
	voice.stop()
	voice.play(player, after=lambda e: asyncio.run_coroutine_threadsafe(advance_queue(ctx), bot.loop))
	audio_start_time = time.time()

	if npmessage != None:
		await npmessage.delete()

	try:
		await qmessage.delete()
	except UnboundLocalError:
		pass
	
	submitter_text = f'\nQueued by {user}' if show_users_in_queue else ''
	embed = discord.Embed(title=f'{get_loop_icon()}Now playing: {player.title} [{now_playing.length}]',description=f'Link: {url}{submitter_text}',color=0xFFFF00)
	npmessage = await ctx.send(embed=embed)
	if last_played != None:
		for i in glob.glob(f'*-#-{last_played.ID}-#-*'):
			# Delete last played file
			log(f'Removing file: {i}')
			try:
				os.remove(i)
			except PermissionError as e:
				# Will be raised if we're looping, or if 
				# another server is playing something; safe to ignore
				pass

async def advance_queue(ctx, skip=False):
	if skip or not voice.is_playing():
		if player_queue.get(ctx) == [] and not loop_this:
			voice.stop()
		else:
			if loop_this and not skip:
				url = now_playing.weburl
			else:
				next_item = player_queue.get(ctx).pop(0)
				url = next_item.url
				user = next_item.user
			await play_url(url, ctx, user)

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
if public: command_prefix = public_prefix
else: command_prefix = dev_prefix

bot = commands.Bot(
	command_prefix=commands.when_mentioned_or(command_prefix),
	description='',
	intents=intents,
)

menu = DefaultMenu('◀️', '▶️', '❌')
bot.help_command = PrettyHelp(navigation=menu, color=0xFFFF00)

# Command error handling
@bot.event
async def on_command_error(ctx, error):
	if isinstance(error, discord.ext.commands.errors.MissingRequiredArgument):
		if ctx.command.name == 'play':
			# Resuming while paused
			if voice.is_paused():
				voice.resume()
				await ctx.send(embed=embedq('Player is resuming.'))
				global paused_for
				paused_for = time.time() - paused_at
			else:
				await ctx.send(embed=embedq('No URL given.'))
		elif ctx.command.name == 'volume':
			await ctx.send(embed=embedq('An integer between 0 and 100 must be given for volume.'))
		elif ctx.command.name == 'analyze':
			await ctx.send(embed=embedq('A spotify track URL is required.'))
	elif isinstance(error, discord.ext.commands.CheckFailure):
		await ctx.send(embed=embedq('This command is disabled for this instance.', 'If you run this bot, check your `config.yml`.'))
	else:
		log(f'Error encountered in command `{ctx.command}`.')
		log(error)
		trace=traceback.format_exception(error)
		await ctx.send(embed=embedq(error, 'If this issue persists, please check https://github.com/svioletg/viMusBot/issues and submit a new issue if your problem is not listed.'))
		# A second traceback is created from this command itself, usually not useful
		log(f'Full traceback below.\n\n{plt.error}'+''.join(trace[:trace.index('\nThe above exception was the direct cause of the following exception:\n\n')]))

@bot.event
async def on_ready():
	log(f'Logged in as {bot.user} (ID: {bot.user.id})')
	print('-----')
	log('Ready!')

# Retrieve bot token
log(f'Retrieving token from {plt.blue}{token_file_path}')

if not public:
	log(f'{plt.warn}NOTICE: Starting in dev mode.')

try:
	with open(token_file_path, 'r') as f:
		token = f.read()
except FileNotFoundError:
	print(f'{f} does not exist; exiting.')
	exit()

# Begin main thread
async def main():
	async with bot:
		await bot.add_cog(General(bot))
		await bot.add_cog(Music(bot))
		await bot.start(token)

if __name__ == '__main__':
	asyncio.run(main())