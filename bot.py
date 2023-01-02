import asyncio
import colorama
from colorama import Fore, Back, Style
import discord
from discord.ext import commands
import glob
import importlib
import logging
import os
import pytube
import random
import subprocess
import sys
import time
import traceback
import urllib.request
import yaml
import yt_dlp

from datetime import datetime
from datetime import timedelta
from inspect import currentframe, getframeinfo
from pretty_help import DefaultMenu, PrettyHelp

# Validate config
if not os.path.isfile('config_default.yml'):
	urllib.request.urlretrieve('https://raw.githubusercontent.com/svioletg/viMusBot/master/config_default.yml','config_default.yml')

with open('config_default.yml','r') as f:
	config_default = yaml.safe_load(f)

with open('config.yml','r') as f:
	config = yaml.safe_load(f)

def keys_recursive(d):
	vals = []
	for k, v in d.items():
		vals.append(k)
		if isinstance(v, dict):
			vals=vals+keys_recursive(v)
	return vals

default_options = keys_recursive(config_default)
user_options = keys_recursive(config)

for i in user_options:
	if i not in default_options:
		print(f'{i} is no longer used; '+
			'it may have been renamed or removed in a recent update. '+
			'Check the changelog linked above for what might have moved.')

for i in default_options:
	if i not in user_options:
		if config.get('auto-update-config',False):
			print('config.yml is missing new options; merging...')
			new_config = {**config_default, **config}
			os.replace('config.yml','config_old.yml')
			with open('config.yml','w') as f:
				yaml.dump(new_config, f, default_flow_style=False, indent=4)
			print('config.yml has been updated with new options, '+
				'and your previous settings have been preserved. '+
				'\nconfig_old.yml has been created in case this process has gone wrong.')
			break
		else:
			print('config.yml is missing new options. '+
				'\nSet auto-update-config to true to update your config automatically, '+
				'or check the latest default config and add the missing options manually.')
			print('Most recent config template: https://github.com/svioletg/viMusBot/blob/master/config_default.yml')
			print('You are missing:\n')
			for i in list(set(config_default) - set(config)): print(i)
			print('\nThe auto-update-config option is either missing or set to false, '+
				'so the script will exit.')
			exit()

# Import local files after main packages, and after validating config
import customlog
import spoofy

from palette import Palette
import update

_here = os.path.basename(__file__)

# For personal reference
# Represents the version of the overall project, not just this file
with open('version.txt','r') as f:
	version = f.read()

### TODO
TODO = {
}

# Start discord logging
handler = logging.FileHandler(filename='discord.log', encoding='utf-8', mode='w')
discord.utils.setup_logging(handler=handler, level=logging.INFO, root=False)

# Personal debug logging
colorama.init(autoreset=True)
plt = Palette()

last_logtime = time.time()

def log(msg):
	global last_logtime
	customlog.newlog(msg=msg, last_logtime=last_logtime, called_from=sys._getframe().f_back.f_code.co_name)
	last_logtime = time.time()

def logln():
	cf = currentframe()
	if print_logs: print('@ LINE ', cf.f_back.f_lineno)

log(f'[{version}]')

update_check = update.check()

if not update_check[0]:
	log(f'{plt.warn}There is a new release available.')
	current_tag = update_check[1]['current']
	latest_tag = update_check[1]['latest']
	log(f'Current: {plt.gold}{current_tag}{plt.reset} | Latest: {plt.lime}{latest_tag}')

log('Changelog: https://github.com/svioletg/viMusBot/blob/master/changelog.md')

log('Starting...')

# Parse config from YAML
with open('config.yml','r') as f:
	config = yaml.safe_load(f)

allow_spotify_playlists = config['allow-spotify-playlists']
spotify_playlist_limit = config['spotify-playlist-limit']
use_top_match = config['use-top-match']
public_prefix = config['prefixes']['public']
dev_prefix = config['prefixes']['developer']
public = config['public']
inactivity_timeout = config['inactivity-timeout']

def command_enabled(ctx):
	return not ctx.command.name in config['command-blacklist']

def get_aliases(command: str):
	return config['aliases'].get(command,[])

# Clear out downloaded files
log('Removing previously downloaded files...')
toremove=[f for f_ in [glob.glob(e) for e in ('*.webm', '*.mp3')] for f in f_]
for i in toremove:
	log(i)
	os.remove(i)
del toremove
log('Done.')

# Shortcut for title-only embeds; "embed quick"
def embedq(*args):
	if len(args)==1:
		return discord.Embed(title=args[0],color=0xFFFF00)
	if len(args)==2:
		return discord.Embed(title=args[0],description=args[1],color=0xFFFF00)
	else:
		log('Invalid number of arguments passed to embedq()')
		return None

# Based on and adapted from:
# https://github.com/Rapptz/discord.py/blob/v2.0.1/examples/basic_voice.py

# For easier emoji usage
emoji={
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

duration_limit = 5 # in hours

ytdl = yt_dlp.YoutubeDL(ytdl_format_options)

def title_from_url(url):
	log(f'Fetching title of \'{url}\'...')
	if 'youtube.com' in url:
		return pytube.YouTube(url).title
	elif 'soundcloud.com' in url:
		return spoofy.sc.resolve(url).title
	elif 'open.spotify.com' in url:
		return spoofy.spotify_track(url)['title']
	else:
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

class General(commands.Cog):
	def __init__(self, bot):
		self.bot = bot

	# Adapted from: https://stackoverflow.com/a/68599108/8108924
	@commands.Cog.listener()
	# Disconnect after set amount of inactivity
	async def on_voice_state_update(self, member, before, after):
		global voice
		if not member.id == self.bot.user.id:
			return

		elif before.channel is None:
			if inactivity_timeout == 0:
				return
			elapsed = 0
			while True:
				await asyncio.sleep(1)
				elapsed = elapsed + 1
				if voice.is_playing() and not voice.is_paused():
					elapsed = 0
				if elapsed == inactivity_timeout*60:
					log('Leaving voice due to inactivity.')
					await voice.disconnect()
				if not voice.is_connected():
					voice = None
					break

	@commands.command()
	@commands.check(command_enabled)
	async def reload(self, ctx):
		# Separated from the others for debug purposes
		global spoofy
		if not public:
			spoofy = importlib.reload(spoofy)
			log('Reloaded spoofy.py.')

	@commands.command(aliases=get_aliases('changelog'))
	@commands.check(command_enabled)
	async def changelog(self, ctx):
		"""Returns a link to the changelog, and displays most recent version."""
		embed=discord.Embed(title='Read the changelog here: https://github.com/svioletg/viMusBot/blob/master/changelog.md',description=f'Current version: {version}',color=0xFFFF00)
		await ctx.send(embed=embed)

	@commands.command(aliases=get_aliases('ping'))
	@commands.check(command_enabled)
	async def ping(self, ctx):
		"""Test command."""
		await ctx.send('Pong!')
		embed=discord.Embed(title='Pong!',description='Pong!',color=0xFFFF00)
		await ctx.send(embed=embed)
		await ctx.send(embed=embedq('this is a test for','the extended embed function'))

	@commands.command(aliases=get_aliases('repository'))
	@commands.check(command_enabled)
	async def repository(self, ctx):
		"""Returns the link to the viMusBot GitHub repository."""
		embed=discord.Embed(title='You can view the bot\'s code and submit bug reports or feature requests here.',description='https://github.com/svioletg/viMusBot\nA GitHub account is required to submit issues.',color=0xFFFF00)
		await ctx.send(embed=embed)

	@commands.command(aliases=get_aliases('todo'))
	@commands.check(command_enabled)
	async def todo(self, ctx):
		"""Returns a list of planned features or bugs to be fixed."""
		embed=discord.Embed(title='Here is the current to-do list for viMusBot.',description='Feel free to suggest anything, no matter how minor!\nFEATURE = A new command or new functionality.\nQOL = Improvements to either the user experience or programming workflow.\nBUG = Incorrect or unexpected behavior.\nISSUE = Not a major issue, but something that could be improved.',color=0xFFFF00)
		for i in TODO:
			embed.add_field(name=i,value=TODO[i])

		await ctx.send(embed=embed)


class Music(commands.Cog):
	def __init__(self, bot):
		self.bot = bot

	# Playing music / Voice-related
	@commands.command(aliases=get_aliases('analyze'))
	@commands.check(command_enabled)
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
	@commands.check(command_enabled)
	async def clear(self, ctx):
		"""Clears the entire queue."""
		global player_queue
		player_queue.clear(ctx)
		await ctx.send(embed=embedq('Queue cleared.'))

	@commands.command(aliases=get_aliases('join'))
	@commands.check(command_enabled)
	async def join(self, ctx):
		"""Joins the voice channel of the user."""
		# This actually just calls ensure_voice below,
		# this is only defined so that there's a command in Discord for it
		pass

	@commands.command(aliases=get_aliases('leave'))
	@commands.check(command_enabled)
	async def leave(self, ctx):
		"""Disconnects the bot from voice."""
		global voice
		global player_queue
		player_queue.clear(ctx)
		log(f'Leaving voice channel: {ctx.author.voice.channel}')
		await voice.disconnect()
		voice = None

	@commands.command(aliases=get_aliases('loop'))
	@commands.check(command_enabled)
	async def loop(self, ctx):
		"""Toggles looping for the current track."""
		global loop_this
		# Inverts the boolean
		loop_this = not loop_this
		await ctx.send(embed=embedq(f'{get_loop_icon()}Looping is set to {loop_this}.'))

	@commands.command(aliases=get_aliases('move'))
	@commands.check(command_enabled)
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
	@commands.check(command_enabled)
	async def nowplaying(self, ctx):
		"""Displays the currently playing video."""
		try:
			if not voice.is_playing() and not voice.is_paused():
				embed = discord.Embed(title=f'Nothing is playing.',color=0xFFFF00)
			else:
				embed = discord.Embed(title=f'{get_loop_icon()}Now playing: {now_playing.title}',description=f'Link: {now_playing.weburl}',color=0xFFFF00)
		except AttributeError:
			embed = discord.Embed(title=f'Nothing is playing.',color=0xFFFF00)

		await ctx.send(embed=embed)

	@commands.command(aliases=get_aliases('pause'))
	@commands.check(command_enabled)
	async def pause(self, ctx):
		"""Pauses the player. Can be resumed with -play."""
		global paused_at
		"""Pauses the player."""
		if voice.is_playing():
			voice.pause()
			await ctx.send(embed=embedq('Player has been paused.'))
			paused_at=time.time()
		elif voice.is_paused():
			await ctx.send(embed=embedq('Player is already paused.'))
		else:
			await ctx.send(embed=embedq('Nothing to pause.'))
	
	@commands.command(aliases=get_aliases('play'))
	@commands.check(command_enabled)
	async def play(self, ctx, *, url: str):
		"""Adds a link to the queue. Plays immediately if the queue is empty."""
		global playctx
		playctx = ctx
		global qmessage
		if 'soundcloud.com' in url:
			qmessage = await ctx.send(embed=embedq('Trying to queue...',
				'Note: It is a known issue that SoundCloud links will sometimes fail to queue.'+
				'\nIf you receive an error, try it again.'+
				'\nDetails: https://github.com/svioletg/viMusBot/issues/16'))
		else:
			qmessage = await ctx.send(embed=embedq('Trying to queue...'))


		# Will resume if paused, this is handled in on_command_error()

		url = url.split('&list=')[0]
		async with ctx.typing():
			# Locate youtube equivalent if spotify link given
			if 'open.spotify.com' in url:
				log('Spotify URL was received from play command.')
				log('Checking for playlist...')
				if '/playlist/' in url:
					log('Spotify playlist detected.')
					if allow_spotify_playlists:
						await qmessage.edit(embed=embedq(
							'Trying to queue Spotify playlist; '+
							'this will take a long time, please wait before trying another command.',
							'This feature is experimental!'))
						objlist = generate_QueueItems(spoofy.spotify_playlist(url))
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
					else:
						await ctx.send(embed=embedq(
							'Spotify playlist support is disabled.',
							'Contact whoever is hosting your bot if you believe this is a mistake.'))
						return

				log('Checking for album...')
				if '/album/' in url:
					log('Spotify album detected.')
					album_info = spoofy.spotify_album(url)
					url = spoofy.search_youtube_album(album_info['title'], album_info['artist'])
					if url==None:
						await ctx.send(embed=embedq('No match could be found.'))
						return
			
			# Search with text if no url is provided
			if 'https://' not in ctx.message.content:
				# TODO: Change this to use prompt_for_choice()
				log('Link not detected, searching with query')
				log(url)
				options = spoofy.search_youtube_text(url)
				top_song_title = options[0]['title']
				top_song_url = 'https://www.youtube.com/watch?v='+options[0]['videoId']
				top_video_title = options[1]['title']
				top_video_url = 'https://www.youtube.com/watch?v='+options[1]['videoId']
				if top_song_url == top_video_url:
					url = top_song_url
				else:
					embed=discord.Embed(title='Please choose an option:',color=0xFFFF00)
					embed.add_field(name=f'Top song result: {top_song_title}',value=top_song_url,inline=False)
					embed.add_field(name=f'Top video result: {top_video_title}',value=top_video_url,inline=False)
					prompt = await ctx.send(embed=embed)
					log('Adding reactions.')
					await prompt.add_reaction(emoji['num'][1])
					await prompt.add_reaction(emoji['num'][2])
					await prompt.add_reaction(emoji['cancel'])
					def check(reaction, user):
						log('Reaction check is being called.')
						return user == ctx.message.author and (str(reaction.emoji) in emoji['num'] or str(reaction.emoji)==emoji['cancel'])
	
					log('Checking for reaction...')
					# 
					try:
						reaction, user = await bot.wait_for('reaction_add', timeout=30.0, check=check)
					except asyncio.TimeoutError as e:
						log('Timeout reached.')
						embed=discord.Embed(title='Timed out; cancelling.',color=0xFFFF00)
						await qmessage.edit(embed=embed)
						return
					except Exception as e:
						log('An error occurred.')
						print(e)
						embed=discord.Embed(title='An unexpected error occurred; cancelling.',color=0xFFFF00)
						await qmessage.edit(embed=embed)
						return
					else:
						# If a valid reaction was received.
						log('Received a valid reaction.')
						if str(reaction)==emoji['cancel']:
							embed=discord.Embed(title='Cancelling.',color=0xFFFF00)
							await qmessage.edit(embed=embed)
							await prompt.delete()
							return
						else:
							choice=emoji['num'].index(str(reaction))
							log(choice)
							embed=discord.Embed(title=f'#{choice} chosen.',color=0xFFFF00)
							await qmessage.edit(embed=embed)
					url='https://www.youtube.com/watch?v='+options[choice-1]['videoId']

			# Determines if the input was a playlist
			valid = ['playlist?list=','/sets/','/album/']
			if any(i in url for i in valid):
				log('URL is a playlist.')
				objlist = generate_QueueItems(url)
				queue_batch(ctx, objlist)
				await ctx.send(embed=embedq(f'Queued {len(objlist)} items.'))
				if not voice.is_playing():
					await advance_queue(ctx)
					return
			else:
				# Runs if the input given was not a playlist
				log('URL is not a playlist.')
				log('Checking duration...')
				# Try pytube first as it's faster
				if 'https://www.youtube.com' in url:
					if pytube.YouTube(url).length > duration_limit*60*60:
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
				log('Trying to start playing or queueing.')
				if not voice.is_playing():
					log('Voice client is not playing; starting...')
					await play_url(url, ctx)
				else:
					player_queue.get(ctx).append(QueueItem(url))
					title=player_queue.get(ctx)[-1].title
					await qmessage.edit(embed=embedq(f'Added {title} to the queue at spot #{len(player_queue.get(ctx))}'))
					log('Appened to queue.')
			except Exception as e:
				raise e

	@commands.command(aliases=get_aliases('queue'))
	@commands.check(command_enabled)
	async def queue(self, ctx, page: int=1):
		"""Displays the current queue, up to #10."""
		if player_queue.get(ctx) == []:
			await ctx.send(embed=embedq('The queue is empty.'))
			return

		embed=discord.Embed(title='Current queue:',color=0xFFFF00)
		n=1
		start=(10*page)-10
		end=(10*page)
		if 10*page>len(player_queue.get(ctx)): end=len(player_queue.get(ctx))
		for i in player_queue.get(ctx)[start:end]:
			embed.add_field(name=f'#{n+start}. {i.title}',value=i.url,inline=False)
			n+=1

		try:
			embed.description = (f'Showing {start+1} to {end} of {len(player_queue.get(ctx))} items. Use -queue [page] to see more.')
		except Exception as e:
			print(e)
			raise e
		await ctx.send(embed=embed)

	@commands.command(aliases=get_aliases('remove'))
	@commands.check(command_enabled)
	async def remove(self, ctx, spot: int):
		"""Removes an item from the queue. Use -q to get its number."""
		await ctx.send(embed=embedq(f'Removed {player_queue.get(ctx).pop(spot-1).title} from the queue.'))

	@commands.command(aliases=get_aliases('shuffle'))
	@commands.check(command_enabled)
	async def shuffle(self, ctx):
		"""Randomizes the order of the queue."""
		random.shuffle(player_queue.get(ctx))
		await ctx.send(embed=embedq('Queue has been shuffled.'))

	@commands.command(aliases=get_aliases('skip'))
	@commands.check(command_enabled)
	async def skip(self, ctx):
		"""Skips the currently playing video."""
		await ctx.send(embed=embedq('Skipping...'))
		await advance_queue(ctx, skip=True)

	@commands.command(aliases=get_aliases('stop'))
	@commands.check(command_enabled)
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
				raise commands.CommandError("Author not connected to a voice channel.")

# 
# 
# End of cog definitions.
# 
# 

# Misc. helper functions
async def prompt_for_choice(ctx, msg, prompt, choices: int, timeout=30):
	# msg = The message *before* the choice menu (prompt) to be edited based on the outcome
	# Get reaction menu ready
	log('Adding reactions.')

	if choices > len(emoji['num']): log('Choices out of range for emoji number list.'); return

	for i in list(range(0,choices)):
		await prompt.add_reaction(emoji['num'][i+1])

	await prompt.add_reaction(emoji['cancel'])

	def check(reaction, user):
		log('Reaction check is being called.')
		return user == ctx.message.author and (str(reaction.emoji) in emoji['num'] or str(reaction.emoji)==emoji['cancel'])

	log('Checking for reaction...')

	try:
		reaction, user = await bot.wait_for('reaction_add', timeout=timeout, check=check)
	except asyncio.TimeoutError as e:
		log('Timeout reached.')
		embed=discord.Embed(title='Timed out; cancelling.',color=0xFFFF00)
		await msg.edit(embed=embed)
		await prompt.delete()
		return None
	except Exception as e:
		log('An error occurred.')
		print(e)
		embed=discord.Embed(title='An unexpected error occurred; cancelling.',color=0xFFFF00)
		await msg.edit(embed=embed)
		await prompt.delete()
		return None
	else:
		# If a valid reaction was received.
		log('Received a valid reaction.')

		if str(reaction)==emoji['cancel']:
			log('Selection cancelled.')
			embed=discord.Embed(title='Cancelling.',color=0xFFFF00)
			await msg.edit(embed=embed)
			await prompt.delete()
			return None
		else:
			choice=emoji['num'].index(str(reaction))
			log(f'{choice} selected.')
			embed=discord.Embed(title=f'#{choice} chosen.',color=0xFFFF00)
			await msg.edit(embed=embed)
			await prompt.delete()
			return choice
	# Theoretically the code shouldn't reach this point
	log(f'{plt.warn}NOTICE: Unexpected behavior; prompt returned outside try/except/else')
	await prompt.delete()

# Queue system

class MediaQueue(object):
	def __init__(self):
		self.queues = {}

	# Run in every function to automatically determin
	# which queue we're working with
	def ensure_queue_exists(self, ctx):
		if ctx.author.guild.id not in self.queues:
			self.queues[ctx.author.guild.id] = []

	def get(self, ctx):
		self.ensure_queue_exists(ctx)
		return self.queues[ctx.author.guild.id]

	def clear(self, ctx):
		self.ensure_queue_exists(ctx)
		self.queues[ctx.author.guild.id] = []

player_queue = MediaQueue()

class QueueItem(object):
	def __init__(self, url, title=None):
		self.url = url
		# Saves time on downloading if we've already got the title
		if title is not None: self.title = title
		else: self.title = title_from_url(url)

def generate_QueueItems(playlist):
	objlist = []
	if type(playlist) == list:
		objlist = [QueueItem(i['url'],title=i['title']) for i in playlist]
		return objlist
	else:
		# Anything youtube-dl natively supports is probably a link
		if 'soundcloud.com' in playlist:
			# SoundCloud playlists have to be processed differently
			playlist_entries = spoofy.soundcloud_playlist(playlist)
			objlist = [QueueItem(i.permalink_url,title=i.title) for i in playlist_entries]
		else:
			playlist_entries = ytdl.extract_info(playlist,download=False)
			objlist = [QueueItem(i['url'],title=i['title']) for i in playlist_entries['entries']]
		return objlist

def queue_batch(ctx, batch):
	# batch must be a list of QueueItem objects
	global player_queue
	for i in batch:
		player_queue.get(ctx).append(i)

now_playing = None
last_played = None

npmessage = None

audio_started = 0
paused_at = 0
paused_for = 0

loop_this = False

async def play_url(url, ctx):
	global now_playing
	global npmessage
	global last_played
	global audio_started, paused_at, paused_for

	paused_at, paused_for = 0, 0
	last_played = now_playing

	log('Trying to start playing...')
	# Check if we need to match a Spotify link
	if 'open.spotify.com' in url:
		log('Trying to match Spotify track...')
		qmessage = await ctx.send(embed=embedq(f'Spotify link detected, searching YouTube...','Please wait; this may take a while!'))
		spyt=spoofy.spyt(url)

		log('Checking if unsure...')
		if type(spyt)==tuple and spyt[0]=='unsure':
			# This indicates no match was found
			log('spyt returned unsure.')
			# Remove the warning, no longer needed
			spyt=spyt[1]
			# Shorten to {limit} results
			limit=5
			spyt=dict(list(spyt.items())[:limit])
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
	now_playing.weburl = 'https://www.youtube.com/watch?v='+now_playing.ID
	voice.stop()
	voice.play(player, after=lambda e: asyncio.run_coroutine_threadsafe(advance_queue(ctx), bot.loop))
	audio_started = time.time()

	if npmessage != None: await npmessage.delete()

	try:
		await qmessage.delete()
	except UnboundLocalError:
		pass

	embed = discord.Embed(title=f'{get_loop_icon()}Now playing: {player.title}',description=f'Link: {url}',color=0xFFFF00)
	npmessage = await ctx.send(embed=embed)
	if last_played != None:
		for i in glob.glob(f'*-#-{last_played.ID}-#-*'):
			# Delete last played file
			log(f'Removing: {i}')
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
			if loop_this and not skip: url = now_playing.weburl
			else: url = player_queue.get(ctx).pop(0).url
			await play_url(url, ctx)

# TODO: This could have a better name
def get_loop_icon():
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

@bot.event
async def on_command_error(ctx, error):
	if isinstance(error, discord.ext.commands.errors.MissingRequiredArgument):
		if ctx.command.name == 'play':
			if voice.is_paused():
				voice.resume()
				await ctx.send(embed=embedq('Player is resuming.'))
				global paused_for
				paused_for=time.time()-paused_at
			else:
				await ctx.send(embed=embedq('No URL given.'))
		elif ctx.command.name == 'volume':
			await ctx.send(embed=embedq('An integer between 0 and 100 must be given for volume.'))
		elif ctx.command.name == 'analyze':
			await ctx.send(embed=embedq('A spotify track URL is required.'))
	elif isinstance(error, discord.ext.commands.CheckFailure):
		await ctx.send(embed=embedq('This command is disabled for this instance.'))
	else:
		log(f'Error encountered in command `{ctx.command}`.')
		log(error)
		trace=traceback.format_exception(error)
		await ctx.send(embed=embedq(error))
		# A second traceback is created from this command itself, usually not useful
		log(f'Full traceback below.\n\n{plt.error}'+''.join(trace[:trace.index('\nThe above exception was the direct cause of the following exception:\n\n')]))

@bot.event
async def on_ready():
	print(f'Logged in as {bot.user} (ID: {bot.user.id})')
	print('------')

# Retrieve bot token
if public: f='token.txt'
else: f='devtoken.txt'; log(f'{plt.warn}NOTICE: Starting in dev mode.')

try:
	token = open(f).read()
except FileNotFoundError:
	print(f'{f} does not exist; exiting.')
	exit()

async def main():
	async with bot:
		await bot.add_cog(General(bot))
		await bot.add_cog(Music(bot))
		await bot.start(token)

asyncio.run(main())