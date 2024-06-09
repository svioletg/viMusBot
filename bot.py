"""The main bot script. Running this will start viMusBot."""

# pylint: disable=wrong-import-position

print('Starting up, this can take a few moments...')

# Standard imports
import asyncio
import glob
import logging
import os
import sys
import traceback
from pathlib import Path
from platform import python_version

# External imports
import aioconsole
import colorama
import discord
import yt_dlp
from discord.ext import commands
from pretty_help import PrettyHelp

# Local imports
import utils.configuration as cfg
from cogs import cog_general, cog_voice
from cogs.common import EmojiStr, SilentCancel, embedq
from utils import updating
from utils.miscutil import create_logger
from utils.palette import Palette
from version import VERSION

colorama.init(autoreset=True)
plt = Palette()

# Setup discord logging
discordpy_logfile_handler = logging.FileHandler(filename='discord.log', encoding='utf-8', mode='w')
discord.utils.setup_logging(handler=discordpy_logfile_handler, level=logging.INFO, root=False)

# Setup bot logging
log = create_logger('lydian', Path('lydian.log'))
log.info('Logging for bot.py is now active.')
log.info('Python version: %s', python_version())
log.info('Lydian version: %s', VERSION)

# TODO: Make sure updater is up to snuff
# Check for updates
# if __name__ == '__main__':
#     log.info('Running on version %s; checking for updates...', VERSION)

#     update_check_result = update.get_latest_tag()

#     # Check for an outdated version
#     if update_check_result['current'] != update_check_result['latest']:
#         log.warning('### There is a new release available.')
#         current_tag = update_check_result['current']
#         latest_tag = update_check_result['latest']
#         log.warning('### Current: %s | Latest: %s', current_tag, latest_tag)
#         log.warning('### Use "update.py" or "update.bat" to update.')
#     else:
#         if VERSION.startswith('dev.'):
#             log.warning('You are running a development version.')
#         else:
#             log.info('You are up to date.')

#     log.info('Changelog: https://github.com/svioletg/viMusBot/blob/master/docs/changelog.md')

# Clear out downloaded files
log.info('Removing previously downloaded media files...')
for t in [f for f in glob.glob('*.*') if Path(f).suffix in cfg.CLEANUP_EXTENSIONS]:
    os.remove(t)

# Establish bot user
intents = discord.Intents.default()
intents.messages = True
intents.message_content = True
intents.voice_states = True
intents.reactions = True
intents.guilds = True
intents.members = True

# Set prefix
command_prefix = cfg.PUBLIC_PREFIX if cfg.PUBLIC else cfg.DEV_PREFIX

# Retrieve bot token
log.info('Using token from "%s"...', cfg.TOKEN_FILE_PATH)

if not cfg.PUBLIC:
    log.warning('Starting in dev mode.')

if Path(cfg.TOKEN_FILE_PATH).is_file():
    with open(cfg.TOKEN_FILE_PATH, 'r', encoding='utf-8') as f:
        token = f.read()
else:
    log.error('Filepath "%s" does not exist; exiting.', cfg.TOKEN_FILE_PATH)
    raise SystemExit(0)

bot = commands.Bot(
    command_prefix=commands.when_mentioned_or(command_prefix),
    description='',
    intents=intents,
    help_command = PrettyHelp(False, color=discord.Color(cfg.EMBED_COLOR))
)

@bot.event
async def on_command_error(ctx: commands.Context, error: BaseException):
    """Handles any exceptions raised by any commands or modules."""
    if isinstance(error, commands.MissingRequiredArgument):
        await ctx.send(embed=embedq(EmojiStr.cancel + ' Not enough command arguments given.',
            'Use the `help` command to see the correct syntax.'))
        return
    if isinstance(error, commands.CommandInvokeError):
        if 'ffmpeg was not found' in repr(error):
            log.error('FFmpeg was not found. It must be present either in the bot\'s directory or your system\'s PATH in order to play audio.')
            await ctx.send(embed=embedq(EmojiStr.cancel + ' Can\'t play audio. Please check the bot\'s logs.'))
            return
    if isinstance(error, NotImplementedError):
        await ctx.send(embed=embedq(EmojiStr.cancel + f' The command `{ctx.command.name}` is not implemented yet,'+
            'but is planned to be in the future.'))
        return
    if isinstance(error, yt_dlp.utils.DownloadError):
        await ctx.send(embed=embedq(EmojiStr.cancel + ' Unable to retrieve video.',
            'It may be private, or otherwise unavailable.'))
        return
    if isinstance(error, SilentCancel | commands.CheckFailure | commands.CommandNotFound):
        return # Ignored, or are handled in other modules

    # If anything unexpected occurs, log it
    log.error(error)
    if cfg.LOG_TRACEBACKS:
        log.error('Full traceback to follow...\n\n%s', ''.join(traceback.format_exception(error)))
    await ctx.send(embed=embedq(EmojiStr.cancel + ' An unexpected error has occurred. Check your logs for more information.',
        str(error)))

@bot.event
async def on_error(event_name, *args, **kwargs): # pylint: disable=unused-argument
    """Handles any non-command errors."""
    error = sys.exc_info()[1]
    log.error(error)
    if cfg.LOG_TRACEBACKS:
        log.error('Full traceback to follow...\n\n%s', ''.join(traceback.format_exception(error)))

@bot.event
async def on_ready():
    "Runs when the bot is ready to start."
    log.info('Logged in as %s (ID: %s)', bot.user, bot.user.id)
    log.info('=' * 20)
    log.info('Ready!')

# Begin main thread

asyncio_tasks: dict[str, asyncio.Task] = {}

async def console_thread():
    """Handles console commands."""
    log.info('Console is active.')
    while True:
        try:
            user_input: str = await aioconsole.ainput('')
            user_input = user_input.lower().strip()
            if user_input == '':
                continue
            match user_input:
                case 'colors':
                    plt.preview()
                    print()
                case 'stop':
                    log.info('Stopping the bot...')
                    log.debug('Leaving voice if connected...')
                    # await voice.disconnect()
                    log.debug('Cancelling bot task...')
                    asyncio_tasks['bot'].cancel()
                    try:
                        await asyncio_tasks['bot']
                    except asyncio.exceptions.CancelledError:
                        pass
                    log.debug('Cancelling console task...')
                    asyncio_tasks['console'].cancel()
                    try:
                        await asyncio_tasks['console']
                    except asyncio.exceptions.CancelledError:
                        pass
                case _:
                    log.info('Unrecognized command "%s"', user_input)
        except Exception as e:
            log.info('Error encountered in console thread!')
            log.error(e)
            if cfg.LOG_TRACEBACKS:
                log.error('Full traceback to follow...\n\n%s', ''.join(traceback.format_exception(e)))

async def bot_thread():
    """Async thread for the Discord bot."""
    log.info('Starting bot thread...')
    log.debug('Assigning bot logger to cogs...')
    cog_general.log = log
    cog_voice.log = log
    async with bot:
        log.debug('Adding cog: General')
        await bot.add_cog(cog_general.General(bot))
        log.debug('Adding cog: Voice')
        await bot.add_cog(cog_voice.Voice(bot))
        log.info('Logging in with token, please wait for a "Ready!" message before using any commands...')
        await bot.start(token)

async def main():
    """Creates main tasks and runs everything."""
    asyncio_tasks['bot'] = asyncio.create_task(bot_thread())
    asyncio_tasks['console'] = asyncio.create_task(console_thread())
    try:
        await asyncio.gather(asyncio_tasks['bot'], asyncio_tasks['console'])
    except asyncio.exceptions.CancelledError:
        pass

if __name__ == '__main__':
    asyncio.run(main())
