import os
import sys
import subprocess
import glob
import yt_dlp
import pytube
import asyncio
import discord
from discord.ext import commands
import spoofy
import time
import colorama
from colorama import Fore, Back, Style

# For personal reference
# Represents the version of the overall project, not just this file
version = '1.3.4'

### TODO
TODO = {
	'Make better custom help command':'FEATURE',
	'Pagify the queue list':'FEATURE',
}

# Init colorama
colorama.init(autoreset=True)

# Start logging
discord.utils.setup_logging()

# Personal debug logging
logtimeA = time.time()
logtimeB = time.time()

debug=True
def logln():
	cf = currentframe()
	if debug: print('@ LINE ', cf.f_back.f_lineno)

def log(msg):
	global logtimeA
	global logtimeB
	logtimeB = time.time()
	elapsed = logtimeB-logtimeA
	if debug:
		print(f'{Style.BRIGHT}{Fore.YELLOW}[ bot.py ]{Style.RESET_ALL} {msg}{Style.RESET_ALL} {Style.BRIGHT}{Fore.MAGENTA} {round(elapsed,2)}s')
	logtimeA = time.time()

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
		print('Invalid number of arguments passed to embedq()')
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

def urltitle(url):
	log(f'urltitle {url}')
	# info_dict = ytdl.extract_info(url, download=False)
	# return info_dict.get('title', None)
	return pytube.YouTube(url).title

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

		log('YTDLSource.from_url running')
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

	@commands.command()
	async def thread(self, ctx):
		thread.starttest()

	@commands.command(aliases=['bugs'])
	async def todo(self, ctx):
		"""| -todo (alias: -bugs) | Returns a list of planned features or bugs to be fixed."""
		embed=discord.Embed(title='Here is the current to-do list for viMusBot.',description='Feel free to suggest anything, no matter how minor!\nFEATURE = A new command or new functionality.\nQOL = Improvements to either the user experience or programming workflow.\nBUG = Incorrect or unexpected behavior.\nISSUE = Not a major issue, but something that could be improved.',color=0xFFFF00)
		for i in TODO:
			embed.add_field(name=i,value=TODO[i])

		await ctx.send(embed=embed)

	@commands.command(aliases=['repo', 'github', 'gh'])
	async def repository(self, ctx):
		"""| -repository (aliases: -repo, -github, -gh) | Returns the link to the viMusBot GitHub repository."""
		embed=discord.Embed(title='You can view the bot\'s code and submit bug reports or feature requests here.',description='https://github.com/svioletg/viMusBot',color=0xFFFF00)
		embed.add_field(name='A GitHub account is required to submit issues.',value='',inline=False)
		await ctx.send(embed=embed)

class Music(commands.Cog):
	def __init__(self, bot):
		self.bot = bot

	# Playing music / Voice-related

	@commands.command(aliases=['analyse'])
	async def analyze(self, ctx, spotifyurl: str):
		"""| -analyze <spotify_url> | Returns spotify API information regarding a track."""
		embed=spoofy.analyze_track(spotifyurl)
		await ctx.send(embed=embed)

	@commands.command()
	async def clear(self, ctx):
		"""| -clear | Clears the entire queue."""
		global player_queue
		player_queue=[]
		await ctx.send(embed=embedq('Queue cleared.'))

	@commands.command()
	async def join(self, ctx):
		"""| -join | Joins the voice channel of the user."""
		if ctx.author.voice == None:
			await ctx.send('You are not connected to a voice channel.')
		else:
			channel = ctx.author.voice.channel

		if ctx.voice_client is not None:
			return await ctx.voice_client.move_to(channel)

		await channel.connect()

	@commands.command()
	async def leave(self, ctx):
		"""| -leave | Disconnects the bot from voice."""
		global player_queue
		player_queue=[]
		await ctx.voice_client.disconnect()

	@commands.command()
	async def move(self, ctx, old: int, new: int):
		"""| -move <current> <new> | Moves a queue item from <current> to <new>."""
		log('move command')
		try:
			player_queue.insert(new-1, player_queue.pop(old-1))
			await ctx.send(embed=embedq(f'Moved {player_queue[new].title} to #{new}.'))
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
		"""| -nowplaying (alias: -np) | Displays the currently playing video."""
		embed=discord.Embed(title=f'Now playing: {nowplaying.title}',description=f'Link: {npurl}',color=0xFFFF00)
		await ctx.send(embed=embed)

	@commands.command()
	async def pause(self, ctx):
		"""| -pause | Pauses the player."""
		if ctx.voice_client.is_playing():
			ctx.voice_client.pause()
			await ctx.send(embed=embedq('Player has been paused.'))
		elif ctx.voice_client.is_paused():
			await ctx.send(embed=embedq('Player is already paused.'))
		else:
			await ctx.send(embed=embedq('Nothing to pause.'))
		
	@commands.command()
	async def ping(self, ctx):
		"""| -ping | Test command."""
		await ctx.send('Pong!')
		embed=discord.Embed(title='Pong!',description='Pong!',color=0xFFFF00)
		await ctx.send(embed=embed)
		await ctx.send(embed=embedq('this is a test for','the extended embed function'))

	@commands.command(aliases=['p'])
	async def play(self, ctx, *, url: str):
		"""| -play <url> (alias: -p) | Adds a link to the queue. Plays immediately if the queue is empty."""
		log('play command')
		global playctx
		playctx = ctx
		global qmessage
		qmessage = await ctx.send(embed=embedq('Trying to queue...'))

		# Will resume if paused
		# This is handled in on_command_error()

		if 'https://' not in ctx.message.content:
			embed=discord.Embed(title='Query must be a link.')
			await qmessage.edit(embed=embed)
			return

		url = url.split('&list=')[0]
		log(url)
		log('Starting play routine')
		async with ctx.typing():
			if 'open.spotify.com' in url:
				# Locate YT equivalent if spotify link given
				log('Spotify URL was received from play command.')
				embed=discord.Embed(title=f'Spotify link detected, searching YouTube...',description='Please wait; this may take a while!',color=0xFFFF00)
				await qmessage.edit(embed=embed)
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
					log('Generating embed message...')
					embed=discord.Embed(title='No exact match found; please choose an option.',description=f'Select the number with reactions or use {emoji["cancel"]} to cancel.',color=0xFFFF00)
					
					for i in spyt:
						title=spyt[i]['title']
						url=spyt[i]['url']
						# log(f'Checking {title} {url}')
						# try:
						# 	ytdl.extract_info(url,download=False)
						# except yt_dlp.utils.DownloadError as e:
						# 	# Skip unavailable videos
						# 	continue
						# except Exception as e:
						# 	print(e)
						# 	continue
						embed.add_field(name=f'{i+1}. {title}',value=url,inline=False)

					log('Embed created.')
					prompt = await ctx.send(embed=embed)
					# Get reaction menu ready
					log('Adding reactions.')

					for i in spyt:
						await prompt.add_reaction(emoji['num'][i+1])

					await prompt.add_reaction(emoji['cancel'])

					def check(reaction, user):
						log('Reaction check is being called.')
						return user == ctx.message.author and (str(reaction.emoji) in emoji['num'] or str(reaction.emoji)==emoji['cancel'])

					log('Checking for reaction...')

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
							print(str(reaction))
							choice=emoji['num'].index(str(reaction))
							print(choice)
							spyt=spyt[choice-1]
							embed=discord.Embed(title=f'#{choice} chosen.',color=0xFFFF00)
							await qmessage.edit(embed=embed)

					await prompt.delete()

				log('Checking if playlist or album...')
				try:
					if type(spyt)==list:
						objlist = queue_objects_from_list(spyt)
						queue_batch(objlist)
						await ctx.send(embed=embedq(f'Queued {len(objlist)} items.'))
						if not ctx.voice_client.is_playing():
							await next_in_queue(ctx, skip=True)
							return
				except Exception as e:
					print('Exception in spyt playlist check')
					print(e)
					raise e

				url=spyt['url']
			
			# Detecting non-spotify playlists or albums
			valid = ['playlist?list=','/sets/','/album/']
			if any(i in url for i in valid):
				log('URL is a playlist.')
				objlist = queue_objects_from_list(url)
				queue_batch(objlist)
				await ctx.send(embed=embedq(f'Queued {len(objlist)} items.'))
				if not ctx.voice_client.is_playing():
					await next_in_queue(ctx, skip=True)
					return
			else:
				log('URL is not a playlist.')
				log('Checking duration...')
				# Try pytube first as it's faster
				if 'https://www.youtube.com' in url:
					if pytube.YouTube(url).length>duration_limit*60*60:
						log('Item over duration limit; not queueing.')
						await qmessage.edit(embed=embedq(f'Cannot queue items longer than {duration_limit} hours.'))
						return
				else:
					if ytdl.extract_info(url,download=False)['duration']>duration_limit*60*60:
						log('Item over duration limit; not queueing.')
						await qmessage.edit(embed=embedq(f'Cannot queue items longer than {duration_limit} hours.'))
						return
				log('Checking availability...')
				# Make sure the video exists.
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

			# Start the player.
			try:
				log('Trying to start playing or queueing.')
				if not ctx.voice_client.is_playing():
					log('Voice client is not playing; joining...')
					await playnext(url, ctx)
				else:
					player_queue.append(QueueItem(url))
					title=player_queue[-1].title
					await qmessage.edit(embed=embedq(f'Added {title} to the queue at spot #{len(player_queue)}'))
					log('URL appended to queue.')
			except Exception as e:
				print(e)
				raise e

	@commands.command(aliases=['q'])
	async def queue(self, ctx):
		"""| -queue (alias: -q) | Displays the current queue, up to #10."""
		embed=discord.Embed(title='Current queue:',color=0xFFFF00)
		n=1
		for i in player_queue:
			if n<=10: embed.add_field(name=f'#{n}. {i.title}',value=i.url,inline=False)
			n+=1

		await ctx.send(embed=embed)

	@commands.command()
	async def remove(self, ctx, spot):
		"""| -remove <number> | Removes an item from the queue. Use -q to get its number."""
		await ctx.send(embed=embedq(f'Removed {player_queue.pop(spot+1)} from the queue.'))
		player_queue.pop(spot+1)

	@commands.command(aliases=['s'])
	async def skip(self, ctx):
		"""| -skip (alias: -s)| Skips the currently playing video."""
		await ctx.send(embed=embedq('Skipping...'))
		await next_in_queue(ctx, skip=True)

	@commands.command()
	async def stop(self, ctx):
		"""| -stop | Stops the player and clears the queue."""
		global player_queue
		player_queue=[]
		if ctx.voice_client.is_playing() or ctx.voice_client.is_paused():
			ctx.voice_client.stop()
			await ctx.send(embed=embedq('Player has been stopped.'))
		else:
			await ctx.send(embed=embedq('Nothing is playing.'))

	@play.before_invoke
	@pause.before_invoke
	@stop.before_invoke
	async def ensure_voice(self, ctx):
		if ctx.voice_client is None:
			if ctx.author.voice:
				await ctx.author.voice.channel.connect()
			else:
				await ctx.send(embed=embedq("You are not connected to a voice channel."))
				raise commands.CommandError("Author not connected to a voice channel.")


# Establish bot user
intents = discord.Intents.default()
intents.messages = True
intents.message_content = True
intents.voice_states = True
intents.reactions = True
intents.guilds = True
intents.members = True

bot = commands.Bot(
	command_prefix=commands.when_mentioned_or('-'),
	description='',
	intents=intents,
)

# Retrieve bot token
try:
	token = open('token.txt').read()
except FileNotFoundError:
	print('token.txt does not exist; exiting.')
	exit()

#
#
# Queueing system
#
#

player_queue=[]

class QueueItem(object):
	def __init__(self, url, title=None):
		self.url = url
		# Saves time on downloading if we've already got the title
		if title is not None:
			self.title = title
		else:
			self.title = urltitle(url)

def queue_objects_from_list(playlist):
	objlist = []
	if type(playlist)==list:
		# Usually only is a list for Spotify
		for i in playlist:
			objlist.append(QueueItem(i['url'],title=i['title']))
		return objlist
	else:
		# Anything youtube-dl natively supports is probably a link
		playlist_ext = ytdl.extract_info(playlist,download=False)
		for i in playlist_ext['entries']:
			objlist.append(QueueItem(i['url'],title=i['title']))
		return objlist

def queue_batch(batch):
	# batch must be a list of QueueItem objects
	global player_queue
	for i in batch:
		player_queue.append(i)

nowplaying=None
npurl=''
lastplayed=None
lasturl=''

async def playnext(url, ctx):
	global nowplaying, npurl
	global lastplayed, lasturl
	lastplayed=nowplaying
	lasturl=npurl

	try:
		player = await YTDLSource.from_url(url, loop=bot.loop, stream=False)
	except yt_dlp.utils.DownloadError as e:
		await ctx.send(embed=embedq('This video is unavailable.',url))
		await next_in_queue(ctx)
		return

	nowplaying = player
	npurl=url
	ctx.voice_client.stop()
	ctx.voice_client.play(player, after=lambda e: asyncio.run_coroutine_threadsafe(next_in_queue(ctx), bot.loop))
	embed=discord.Embed(title=f'Now playing: {player.title}',description=f'Link: {url}',color=0xFFFF00)
	if 'open.spotify.com' in ctx.message.content:
		await qmessage.edit(embed=embed)
	else:
		await ctx.send(embed=embed)

async def next_in_queue(ctx, **kwargs):
	skip=False
	if 'skip' in kwargs:
		if kwargs['skip']==True: skip=True
	if skip or (player_queue != [] and not ctx.voice_client.is_playing()):
		print(player_queue)
		if player_queue==[]:
			ctx.voice_client.stop()
			for i in glob.glob(f'*-#-{nowplaying.ID}-#-*'):
				# Delete last played file
				os.remove(i)
		else:
			await playnext(player_queue.pop(0).url, ctx)
			try:
				for i in glob.glob(f'*-#-{lastplayed.ID}-#-*'):
					# Delete last played file
					os.remove(i)
			except AttributeError as e:
				pass
			except Exception as e:
				log('Exception in next_in_queue')
				print(e)
				raise e


@bot.event
async def on_command_error(ctx, error):
	if isinstance(error, discord.ext.commands.errors.MissingRequiredArgument):
		if ctx.command.name == 'play':
			if ctx.voice_client.is_paused():
				ctx.voice_client.resume()
				await ctx.send(embed=embedq('Player is resuming.'))
			else:
				await ctx.send(embed=embedq('No URL given.'))
		if ctx.command.name == 'volume':
			await ctx.send(embed=embedq('An integer between 0 and 100 must be given for volume.'))
		if ctx.command.name == 'analyze':
			await ctx.send(embed=embedq('A spotify track URL is required.'))

@bot.event
async def on_ready():
	print(f'Logged in as {bot.user} (ID: {bot.user.id})')
	print('------')

async def main():
	async with bot:
		await bot.add_cog(General(bot))
		await bot.add_cog(Music(bot))
		await bot.start(token)

asyncio.run(main())