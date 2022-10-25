import os
import sys
import glob
import yt_dlp
import asyncio
import discord
from discord.ext import commands
import spoofy

### TODO
# - Queue system
# - Add stop command
# - Add skip command
# - Add support for forcing a youtube search by user

version='1.1.1'

# Start logging
discord.utils.setup_logging()

# Personal debug logging
debug=True
def logln():
	cf = currentframe()
	if debug: print('@ LINE ', cf.f_back.f_lineno)

def log(msg):
	if debug:
		print('[ bot.py ] '+str(msg))

# Used for bot owner-specific commands
myID = '141354677752037377'

# Largely borrowed from:
# https://github.com/Rapptz/discord.py/blob/v2.0.1/examples/basic_voice.py

# Configure youtube dl
ytdl_format_options = {
	'format': 'bestaudio/best',
	'outtmpl': '%(extractor)s-%(id)s-%(title)s.%(ext)s',
	'restrictfilenames': True,
	'noplaylist': True,
	'nocheckcertificate': True,
	'ignoreerrors': False,
	'logtostderr': False,
	'quiet': False,
	'no_warnings': False,
	'default_search': 'auto',
	'source_address': '0.0.0.0',  # bind to ipv4 since ipv6 addresses cause issues sometimes
}

ffmpeg_options = {
	'options': '-vn',
}

ytdl = yt_dlp.YoutubeDL(ytdl_format_options)

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
	'🔟'
	],
}

class YTDLSource(discord.PCMVolumeTransformer):
	def __init__(self, source, *, data, volume=0.5):
		super().__init__(source,volume)

		self.data = data

		self.title = data.get('title')
		self.url = data.get('url')

	@classmethod
	async def from_url(cls, url, *, loop=None, stream=False):
		loop = loop or asyncio.get_event_loop()
		data = await loop.run_in_executor(None, lambda: ytdl.extract_info(url, download=not stream))

		if 'entries' in data:
			# take first item from a playlist
			data = data['entries'][0]

		filename = data['url'] if stream else ytdl.prepare_filename(data)
		return cls(discord.FFmpegPCMAudio(filename, **ffmpeg_options), data=data)



# Commands here
class Music(commands.Cog):
	def __init__(self, bot):
		self.bot = bot

	@commands.command()
	async def ping(self, ctx):
		await ctx.send('Pong!')
		embed=discord.Embed(title='Pong!',description='Pong!',color=0xFFFF00)
		await ctx.send(embed=embed)

	# Playing music / Voice-related
	@commands.command()
	async def join(self, ctx):
		"""Joins a voice channel"""
		if ctx.author.voice == None:
			await ctx.send('You are not connected to a voice channel.')
		else:
			channel = ctx.author.voice.channel

		if ctx.voice_client is not None:
			return await ctx.voice_client.move_to(channel)

		await channel.connect()

	@commands.command(aliases=['p'])
	async def play(self, ctx, *, url: str):
		"""Main music playing command."""
		mid = ctx.message.id
		# Remove old downloaded videos
		for i in glob.glob('*.webm'):
			os.remove(i)

		if 'https://' not in ctx.message.content:
			embed=discord.Embed(title='Query must be a link.')
			await ctx.send(embed=embed)
			return

		async with ctx.typing():
			if 'open.spotify.com' in ctx.message.content:
				# Locate YT equivalent if spotify link given
				log('Spotify URL was received from play command.')
				embed=discord.Embed(title=f'Spotify link detected, searching YouTube...',color=0xFFFF00)
				await ctx.send(embed=embed)
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
						reaction, user = await bot.wait_for('reaction_add', timeout=15.0, check=check)
					except asyncio.TimeoutError as e:
						log('Timeout reached.')
						embed=discord.Embed(title='Timed out; cancelling.',color=0xFFFF00)
						await ctx.send(embed=embed)
						return
					except Exception as e:
						log('An error occurred.')
						print(e)
						embed=discord.Embed(title='An unexpected error occurred; cancelling.',color=0xFFFF00)
						await ctx.send(embed=embed)
						return
					else:
						# If a valid reaction was received.
						log('Received a valid reaction.')
						if str(reaction)==emoji['cancel']:
							embed=discord.Embed(title='Cancelling.',color=0xFFFF00)
							await ctx.send(embed=embed)
							return
						else:
							print(str(reaction))
							choice=emoji['num'].index(str(reaction))
							print(choice)
							spyt=spyt[choice-1]
							embed=discord.Embed(title=f'#{choice} chosen.',color=0xFFFF00)
							await ctx.send(embed=embed)

				url=spyt['url']
			
			player = await YTDLSource.from_url(url, loop=self.bot.loop, stream=False)
			log('Starting player.')
			ctx.voice_client.play(player, after=lambda e: print(f'Player error: {e}') if e else None)

		embed=discord.Embed(title=f'Now playing: {player.title}',color=0xFFFF00)
		await ctx.send(embed=embed)

	@commands.command()
	async def localfile(self, ctx, *, query):
		source = discord.PCMVolumeTransformer(discord.FFmpegPCMAudio(query))
		ctx.voice_client.play(source, after=lambda e: print(f'Player error: {e}') if e else None)

		await ctx.send(f'Now playing: {query}')

	@commands.command()
	async def volume(self, ctx, volume: int):
		"""Changes the player's volume"""

		if ctx.voice_client is None:
			return await ctx.send("Not connected to a voice channel.")

		ctx.voice_client.source.volume = volume / 100
		await ctx.send(f"Changed volume to {volume}%")

	@commands.command()
	async def leave(self, ctx):
		"""Stops and disconnects the bot from voice"""

		await ctx.voice_client.disconnect()

	# Extra
	@commands.command(aliases=['analyse'])
	async def analyze(self, ctx, spotifyurl: str):
		"""Returns spotify API information regarding a track"""
		embed=spoofy.analyzetrack(spotifyurl)
		await ctx.send(embed=embed)

	@play.before_invoke
	async def ensure_voice(self, ctx):
		if ctx.voice_client is None:
			if ctx.author.voice:
				await ctx.author.voice.channel.connect()
			else:
				await ctx.send("You are not connected to a voice channel.")
				raise commands.CommandError("Author not connected to a voice channel.")
		elif ctx.voice_client.is_playing():
			ctx.voice_client.stop()



# Establish bot user
intents = discord.Intents.default()
intents.messages = True
intents.message_content = True
intents.voice_states = True
intents.reactions = True
intents.guilds = True
intents.members = True

bot = commands.Bot(
	command_prefix=commands.when_mentioned_or('$'),
	description='',
	intents=intents,
)

# Retrieve bot token
try:
	token = open('token.txt').read()
except FileNotFoundError:
	print('token.txt does not exist; exiting.')
	exit()

@bot.event
async def on_ready():
	print(f'Logged in as {bot.user} (ID: {bot.user.id})')
	print('------')

@bot.event
async def on_command_error(ctx, error):
	if isinstance(error, discord.ext.commands.errors.MissingRequiredArgument):
		if ctx.command.name == 'play':
			await ctx.send('No URL given.')
		if ctx.command.name == 'volume':
			await ctx.send('An integer between 0 and 100 must be given for volume.')
		if ctx.command.name == 'analyze':
			await ctx.send('A spotify track URL is required.')
		else:
			await ctx.send('Command is missing required arguments.')

async def main():
	async with bot:
		await bot.add_cog(Music(bot))
		await bot.start(token)

asyncio.run(main())