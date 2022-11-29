import sys
import os
import subprocess
import glob
import yt_dlp
import pytube
import asyncio
import discord
from discord.ext import commands
import spoofy
import time
import traceback
import logging
import customlog
import random
import yaml
import colorama
from colorama import Fore, Back, Style
from palette import Palette
from inspect import currentframe, getframeinfo
from pretty_help import DefaultMenu, PrettyHelp
from datetime import timedelta
from datetime import datetime

_here = os.path.basename(__file__)

# For personal reference
# Represents the version of the overall project, not just this file
version = '1.6.0'

### TODO
TODO = {
}

# Start discord logging
handler = logging.FileHandler(filename='discord.log', encoding='utf-8', mode='w')
discord.utils.setup_logging(handler=handler, level=logging.INFO, root=False)

# Get options
with open('config.yml','r') as f:
	config = yaml.safe_load(f)

allow_spotify_playlists = config['allow-spotify-playlists']
spotify_playlist_limit = config['spotify-playlist-limit']
public_prefix = config['prefixes']['public']
dev_prefix = config['prefixes']['developer']
public = config['public']

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

log('Starting...')

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

# Commands here

class General(commands.Cog):
	def __init__(self, bot):
		self.bot = bot

	# Taken from: https://stackoverflow.com/a/73819537/8108924
	@commands.Cog.listener()
	async def on_voice_state_update(self, ctx, member, before, after):
		
		# Ignore if change from voice channels not from bot
		if not member.id == self.bot.user.id:
			return
		
		# Ignore if change from voice channels was triggered by disconnect()
		elif before.channel is not None:
			return
		
		# Check if playing when in voice channel, every 180 seconds
		else:
			while True:
				await asyncio.sleep(600)				
				# If not playing and not paused, disconnect
				if not voice.is_playing() and not voice.is_paused():
					log('Disconnecting from voice due to inactivity.')
					await voice.disconnect()
					break

	@commands.command()
	async def changelog(self, ctx):
		"""Returns a link to the changelog, and displays most recent version."""
		embed=discord.Embed(title='Read the changelog here: https://github.com/svioletg/viMusBot/blob/master/changelog.md',description=f'Current version: {version}',color=0xFFFF00)
		await ctx.send(embed=embed)

	@commands.command()
	async def ping(self, ctx):
		"""Test command."""
		await ctx.send('Pong!')
		embed=discord.Embed(title='Pong!',description='Pong!',color=0xFFFF00)
		await ctx.send(embed=embed)
		await ctx.send(embed=embedq('this is a test for','the extended embed function'))

	@commands.command(aliases=['repo', 'github', 'gh'])
	async def repository(self, ctx):
		"""Returns the link to the viMusBot GitHub repository."""
		embed=discord.Embed(title='You can view the bot\'s code and submit bug reports or feature requests here.',description='https://github.com/svioletg/viMusBot\nA GitHub account is required to submit issues.',color=0xFFFF00)
		await ctx.send(embed=embed)

	@commands.command(aliases=['bugs'])
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
	@commands.command(aliases=['analyse'])
	async def analyze(self, ctx, spotifyurl: str):
		"""Returns spotify API information regarding a track."""
		info=spoofy.spotify_track(spotifyurl)
		title=info['title']
		artist=info['artist']
		result=spoofy.analyze_track(spotifyurl)
		data=result[0]
		skip=result[1]
		# Assemble embed object
		embed=discord.Embed(title=f'Spotify data for {title} by {artist}', description='Things like key, tempo, and time signature are estimated, and therefore not necessarily accurate.', color=0xFFFF00)
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

	@commands.command()
	async def clear(self, ctx):
		"""Clears the entire queue."""
		global player_queue
		player_queue=[]
		await ctx.send(embed=embedq('Queue cleared.'))

	@commands.command()
	async def join(self, ctx):
		"""Joins the voice channel of the user."""
		if ctx.author.voice == None:
			await ctx.send('You are not connected to a voice channel.')
		else:
			channel = ctx.author.voice.channel

		if voice is not None:
			return await voice.move_to(channel)

		await channel.connect()

	@commands.command()
	async def leave(self, ctx):
		"""Disconnects the bot from voice."""
		global player_queue
		player_queue=[]
		log('Leaving voice channel.')
		await voice.disconnect()

	@commands.command()
	async def move(self, ctx, old: int, new: int):
		"""Moves a queue item from <old> to <new>."""
		try:
			to_move = player_queue[old-1].title
			player_queue.insert(new-1, player_queue.pop(old-1))
			await ctx.send(embed=embedq(f'Moved {to_move} to #{new}.'))
		except IndexError as e:
			await ctx.send(embed=embedq('The selected number is out of range.'))
			print(e)
			raise e
		except Exception as e:
			await ctx.send(embed=embedq('An unexpected error occurred.'))
			print(e)
			raise e

	@commands.command(aliases=['np'])
	async def nowplaying(self, ctx):
		"""Displays the currently playing video."""
		embed=discord.Embed(title=f'Now playing: {nowplaying.title}',description=f'Link: {npurl}',color=0xFFFF00)
		# Attempt at displaying the current timestamp; shelved for now
		
		# timestamp=str(timedelta(seconds=round(time.time()-audio_started-paused_for,0)))
		# # Remove the hours spot if hours is 0
		# if timestamp.split(':')[0]=='0': timestamp=timestamp[2:]
		# length=nowplaying.data['duration_string']
		# # embed.add_field(f'Duration: {timestamp} / {length}')
		# embed.add_field(name=f'Duration: {timestamp} / {length}',value='Duration may not be accurate if the bot is experiencing connection issues.')
		await ctx.send(embed=embed)

	@commands.command()
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
	
	@commands.command(aliases=['p'])
	async def play(self, ctx, *, url: str):
		"""Adds a link to the queue. Plays immediately if the queue is empty."""
		global playctx
		playctx = ctx
		global qmessage
		qmessage = await ctx.send(embed=embedq('Trying to queue...'))

		# Will resume if paused
		# This is handled in on_command_error()

		url = url.split('&list=')[0]
		async with ctx.typing():
			# Locate youtube equivalent if spotify link given
			if 'open.spotify.com' in url:
				log('Spotify URL was received from play command.')
				log('Checking for playlist...')
				if '/playlist/' in url:
					log('Spotify playlist detected.')
					if allow_spotify_playlists:
						await qmessage.edit(embed=embedq('Trying to queue Spotify playlist; this will take a long time, please wait before trying another command.','This feature is experimental!'))
						objlist = generate_QueueItems(spoofy.spotify_playlist(url))
						if len(objlist) > spotify_playlist_limit:
							await qmessage.edit(embed=embedq('Spotify playlist limit exceeded.'))
							return
						queue_multiple(objlist)
						list_name = spoofy.sp.playlist(url)['name']
						await qmessage.edit(embed=embedq(f'Queued {len(objlist)} items from {list_name}.'))
						if not voice.is_playing():
							log('Voice client is not playing; starting...')
							await next_in_queue(ctx)
						return
						### Old, much slower method
						# spytout = spoofy.spyt(url)
						# if spytout == 'too_long':
						# 	await ctx.send(embed=embedq(f'Spotify playlists must have less than {spotify_playlist_limit} tracks.'))
						# 	return
						# objlist = generate_QueueItems(spytout[0])
						# failstring = 'No items failed to queue.'
						# if len(failstring)!=0:
						# 	failstring = 'The following items failed to queue:'
						# 	for i in spytout[1]:
						# 		failstring+=f'\n{i}'
						# queue_multiple(objlist)
						# await ctx.send(embed=embedq(f'Queued {len(objlist)} items.',f'{failstring}'))
						# if not voice.is_playing():
						# 	log('Voice client is not playing; joining...')
						# 	await next_in_queue(ctx, skip=True)
						# return
					else:
						await ctx.send(embed=embedq('Spotify playlist support is disabled.','Contact whoever is hosting your bot if you believe this is a mistake.'))
						return

				log('Checking for album...')
				if '/album/' in url:
					log('Spotify album detected.')
					album_info = spoofy.spotify_album(url)
					url = spoofy.search_ytmusic_album(album_info['title'], album_info['artist'])
					if url==None:
						await ctx.send(embed=embedq('No match could be found.'))
						return
			
			# Search with text if no url is provided
			if 'https://' not in ctx.message.content:
				log('Link not detected, searching with query')
				log(url)
				options=spoofy.search_ytmusic_text(url)
				top_song_title = options[0]['title']
				top_song_url = 'https://www.youtube.com/watch?v='+options[0]['videoId']
				top_video_title = options[1]['title']
				top_video_url = 'https://www.youtube.com/watch?v='+options[1]['videoId']
				if top_song_url==top_video_url:
					url=top_song_url
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
				queue_multiple(objlist)
				await ctx.send(embed=embedq(f'Queued {len(objlist)} items.'))
				if not voice.is_playing():
					await next_in_queue(ctx)
					return
			else:
				# Runs if the input given was not a playlist
				log('URL is not a playlist.')
				log('Checking duration...')
				# Try pytube first as it's faster
				if 'https://www.youtube.com' in url:
					if pytube.YouTube(url).length>duration_limit*60*60:
						log('Item over duration limit; not queueing.')
						await qmessage.edit(embed=embedq(f'Cannot queue items longer than {duration_limit} hours.'))
						return
				else:
					if 'open.spotify.com' in url:
						duration = spoofy.sp.track(url)['duration_ms']/1000
					else:
						try:
							duration = ytdl.extract_info(url,download=False)['duration']
						# 'duration' is not retrieved from the generic extractor used for direct links
						except KeyError as e:
							ffprobe = f'ffprobe {url} -v quiet -show_entries format=duration -of csv=p=0'.split(' ')
							duration = float(subprocess.check_output(ffprobe).decode('utf-8').split('.')[0])

					if duration>duration_limit*60*60:
						log('Item over duration limit; not queueing.')
						await qmessage.edit(embed=embedq(f'Cannot queue items longer than {duration_limit} hours.'))
						return
				log('Checking availability...')
				# Make sure the video exists.
				if 'open.spotify.com' not in url:
					try:
						ytdl.extract_info(url,download=False)
					except yt_dlp.utils.DownloadError as e:
						log('Video unavailable.')
						print(e)
						await qmessage.edit(embed=embedq('This video is unavailable.'))
						return
					except Exception as e:
						print(e)
						await qmessage.edit(embed=embedq('An unexpected error occurred.'))
						return

			# Start the player if we can use the url itself
			try:
				log('Trying to start playing or queueing.')
				if not voice.is_playing():
					log('Voice client is not playing; starting...')
					await playnext(url, ctx)
				else:
					player_queue.append(QueueItem(url))
					title=player_queue[-1].title
					await qmessage.edit(embed=embedq(f'Added {title} to the queue at spot #{len(player_queue)}'))
					log('Appened to queue.')
			except Exception as e:
				print(e)
				raise e

	@commands.command(aliases=['q'])
	async def queue(self, ctx, page: int=1):
		"""Displays the current queue, up to #10."""
		if player_queue==[]:
			await ctx.send(embed=embedq('The queue is empty.'))
			return

		embed=discord.Embed(title='Current queue:',color=0xFFFF00)
		n=1
		start=(10*page)-10
		end=(10*page)
		if 10*page>len(player_queue): end=len(player_queue)
		for i in player_queue[start:end]:
			embed.add_field(name=f'#{n+start}. {i.title}',value=i.url,inline=False)
			n+=1

		try:
			embed.description = (f'Showing {start+1} to {end} of {len(player_queue)} items. Use -queue [page] to see more.')
		except Exception as e:
			print(e)
			raise e
		await ctx.send(embed=embed)

	@commands.command()
	async def remove(self, ctx, spot: int):
		"""Removes an item from the queue. Use -q to get its number."""
		await ctx.send(embed=embedq(f'Removed {player_queue.pop(spot-1).title} from the queue.'))

	@commands.command()
	async def shuffle(self, ctx):
		"""Randomizes the order of the queue."""
		random.shuffle(player_queue)
		await ctx.send(embed=embedq('Queue has been shuffled.'))

	@commands.command(aliases=['s'])
	async def skip(self, ctx):
		"""Skips the currently playing video."""
		await ctx.send(embed=embedq('Skipping...'))
		await next_in_queue(ctx, skip=True)

	@commands.command()
	async def stop(self, ctx):
		"""Stops the player and clears the queue."""
		global player_queue
		player_queue=[]
		if voice.is_playing() or voice.is_paused():
			voice.stop()
			await ctx.send(embed=embedq('Player has been stopped.'))
		else:
			await ctx.send(embed=embedq('Nothing is playing.'))

	@play.before_invoke
	@pause.before_invoke
	@stop.before_invoke
	async def ensure_voice(self, ctx):
		if ctx.voice_client is None:
			if ctx.author.voice:
				log('Joining voice channel.')
				global voice
				voice = await ctx.author.voice.channel.connect()
			else:
				await ctx.send(embed=embedq("You are not connected to a voice channel."))
				raise commands.CommandError("Author not connected to a voice channel.")

# 
# 
# End command code.
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
		return None
	except Exception as e:
		log('An error occurred.')
		print(e)
		embed=discord.Embed(title='An unexpected error occurred; cancelling.',color=0xFFFF00)
		await msg.edit(embed=embed)
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
			await prompt.delete()
			await msg.edit(embed=embed)
			return choice
	# Theoretically the code shouldn't reach this point
	log('Prompt returned outside try/except/else')
	await prompt.delete()

# Queueing system

player_queue=[]

class QueueItem(object):
	def __init__(self, url, title=None):
		self.url = url
		# Saves time on downloading if we've already got the title
		if title is not None: self.title = title
		else: self.title = title_from_url(url)

def generate_QueueItems(playlist):
	objlist = []
	if type(playlist)==list:
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

def queue_multiple(batch):
	# batch must be a list of QueueItem objects
	global player_queue
	for i in batch:
		player_queue.append(i)

nowplaying=None
npurl=''
lastplayed=None
lasturl=''
audio_started=0
paused_at=0
paused_for=0

async def playnext(url, ctx):
	global nowplaying, npurl
	global lastplayed, lasturl
	global audio_started, paused_at, paused_for
	paused_at, paused_for = 0, 0
	lastplayed=nowplaying
	lasturl=npurl
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
			# Prompt the user with choice
			embed=discord.Embed(title='No exact match found; please choose an option.',description=f'Select the number with reactions or use {emoji["cancel"]} to cancel.',color=0xFFFF00)
			
			for i in spyt:
				title=spyt[i]['title']
				url=spyt[i]['url']
				artist=spyt[i]['artist']
				album=spyt[i]['album']
				if artist=='': embed.add_field(name=f'{i+1}. {title}',value=url,inline=False)
				else: embed.add_field(name=f'{i+1}. {title}\nby {artist} - {album}',value=url,inline=False)

			prompt = await ctx.send(embed=embed)
			choice = await prompt_for_choice(ctx, qmessage, prompt, len(spyt))
			if choice==None:
				return
			spyt = spyt[choice-1]
		url = spyt['url']

	try:
		player = await YTDLSource.from_url(url, loop=bot.loop, stream=False)
	except yt_dlp.utils.DownloadError as e:
		await ctx.send(embed=embedq('This video is unavailable.',url))
		await next_in_queue(ctx)
		return

	nowplaying=player
	npurl=url
	voice.stop()
	voice.play(player, after=lambda e: asyncio.run_coroutine_threadsafe(next_in_queue(ctx), bot.loop))
	audio_started = time.time()
	embed=discord.Embed(title=f'Now playing: {player.title}',description=f'Link: {url}',color=0xFFFF00)
	if 'open.spotify.com' in ctx.message.content:
		await qmessage.edit(embed=embed)
	else:
		await ctx.send(embed=embed)
	if lastplayed!=None:
		for i in glob.glob(f'*-#-{lastplayed.ID}-#-*'):
			# Delete last played file
			os.remove(i)
			log(f'Removing: {i}')

async def next_in_queue(ctx, **kwargs):
	skip=kwargs.get('skip',False)
	if skip or (player_queue != [] and not voice.is_playing()):
		if player_queue==[]:
			voice.stop()
		else:
			await playnext(player_queue.pop(0).url, ctx)



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
		if ctx.command.name == 'volume':
			await ctx.send(embed=embedq('An integer between 0 and 100 must be given for volume.'))
		if ctx.command.name == 'analyze':
			await ctx.send(embed=embedq('A spotify track URL is required.'))
	else:
		log(f'Error encountered in command `{ctx.command}`.')
		log(error)
		trace=traceback.format_exception(error)
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