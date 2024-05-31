"""The main bot script. Running this will start viMusBot."""

# pylint: disable=wrong-import-position

print('Starting up, this can take a few moments...')

# Standard imports
import asyncio
import glob
import logging
import os
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
from cogs.common import EMOJI, SilentCancel, embedq
from utils import miscutil, updater
from utils.palette import Palette
from version import VERSION

colorama.init(autoreset=True)
plt = Palette()

# Setup discord logging
discordpy_logfile_handler = logging.FileHandler(filename='discord.log', encoding='utf-8', mode='w')
discord.utils.setup_logging(handler=discordpy_logfile_handler, level=logging.INFO, root=False)

# Setup bot logging
log = miscutil.create_logger('viMusBot', Path('vimusbot.log'))

log.info('Logging for bot.py is now active.')

log.info('Python version: %s', python_version())
log.info('viMusBot version: %s', VERSION)

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

# Start bot-related events
# class Music(commands.Cog):
#     # Playing music / Voice-related
#     @commands.command(aliases=command_aliases('analyze'))
#     @commands.check(is_command_enabled)
#     async def analyze(self, ctx: commands.Context, spotifyurl: str):
#         """Returns spotify API information regarding a track."""
#         info = media.spotify_track(spotifyurl)
#         title = info['title']
#         artist = info['artist']
#         result = media.analyze_spotify_track(spotifyurl)
#         data = result[0]
#         skip = result[1]
#         # Assemble embed object
#         embed = discord.Embed(title=f'Spotify data for {title} by {artist}', description='Things like key, tempo, and time signature are estimated, and therefore not necessarily accurate.', color=EMBED_COLOR)
#         # Put key, time sig, and tempo at the top
#         embed.add_field(name='Key',value=data['key'])
#         data.pop('key')
#         embed.add_field(name='Tempo',value=data['tempo'])
#         data.pop('tempo')
#         embed.add_field(name='Time Signature',value=data['time_signature'])
#         data.pop('time_signature')

#         # Add the rest
#         for i in data:
#             if i in skip:
#                 continue

#             value=data[i]
#             # Change decimals to percentages
#             # Exclude loudness
#             if isinstance(data[i], (int, float)):
#                 if data[i]<1 and i!='loudness':
#                     value=str(round(data[i]*100,2))+'%'

#             value=str(value)
#             embed.add_field(name=i.title(),value=value)
#         await ctx.send(embed=embed)

#     @commands.command(aliases=command_aliases('loop'))
#     @commands.check(is_command_enabled)
#     async def loop(self, ctx: commands.Context):
#         """Toggles looping for the current track."""
#         global loop_this
#         # Inverts the boolean
#         loop_this = not loop_this
#         log.info(f'Looping {["disabled", "enabled"][loop_this]}.')
#         await ctx.send(embed=embedq(f'{get_loop_icon()}Looping {["disabled", "enabled"][loop_this]}.'))

#     @commands.command(aliases=command_aliases('move'))
#     @commands.check(is_command_enabled)
#     async def move(self, ctx: commands.Context, old: int, new: int):
#         """Moves a queue item from <old> to <new>."""
#         try:
#             to_move = media_queue.get(ctx)[old-1].title
#             media_queue.get(ctx).insert(new-1, media_queue.get(ctx).pop(old-1))
#             await ctx.send(embed=embedq(f'Moved {to_move} to #{new}.'))
#         except IndexError as e:
#             await ctx.send(embed=embedq('The selected number is out of range.'))
#         except Exception as e:
#             await ctx.send(embed=embedq('An unexpected error occurred.'))
#             log.error(e)

#     @commands.command(aliases=command_aliases('shuffle'))
#     @commands.check(is_command_enabled)
#     async def shuffle(self, ctx: commands.Context):
#         """Randomizes the order of the queue."""
#         random.shuffle(media_queue.get(ctx))
#         await ctx.send(embed=embedq('Queue has been shuffled.'))

# ############################################
# 
# End of cog definitions.
# 
# ############################################

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
        await ctx.send(embed=embedq(EMOJI['cancel'] + ' Not enough command arguments given.',
            'Use the `help` command to see the correct syntax.'))
        return
    if isinstance(error, commands.CommandInvokeError):
        if 'ffmpeg was not found' in repr(error):
            log.error('FFmpeg was not found. It must be present either in the bot\'s directory or your system\'s PATH in order to play audio.')
            await ctx.send(embed=embedq(EMOJI['cancel'] + ' Can\'t play audio. Please check the bot\'s logs.'))
            return
    if isinstance(error, NotImplementedError):
        await ctx.send(embed=embedq(EMOJI['cancel'] + f' The command `{ctx.command.name}` is not implemented yet,'+
            'but is planned to be in the future.'))
        return
    if isinstance(error, yt_dlp.utils.DownloadError):
        await ctx.send(embed=embedq(EMOJI['cancel'] + ' Unable to retrieve video.',
            'It may be private, or otherwise unavailable.'))
        return
    if isinstance(error, SilentCancel | commands.CheckFailure | commands.CommandNotFound):
        return # Ignored, or are handled in other modules

    # If anything unexpected occurs, log it
    log.error(error)
    if cfg.LOG_TRACEBACKS:
        log.error('Full traceback to follow...\n\n%s', ''.join(traceback.format_exception(error)))
    await ctx.send(embed=embedq(EMOJI['cancel'] + ' An unexpected error has occurred. Check your logs for more information.',
        str(error)))

@bot.event
async def on_ready():
    log.info('Logged in as %s (ID: %s)', bot.user, bot.user.id)
    log.info('=' * 20)
    log.info('Ready!')

# Begin main thread

asyncio_tasks: dict[str, asyncio.Task] = {}

async def console_thread():
    log.info('Console is active.')
    while True:
        try:
            user_input: str = await aioconsole.ainput('')
            user_input = user_input.lower().strip()
            if user_input == '':
                continue

            # Console debugging commands
            if user_input.startswith('test'):
                pass
            #     if PUBLIC:
            #         print('Debugging commands are disabled in public mode.')
            #         continue
                
            #     # TODO: Some sort of help command would be good
            #     params = user_input.split()

            #     if params[1] == 'play':
            #         if len(params) < 3:
            #             print('Not enough arguments. Usage: test play <source> [flags] (available flags: invalid, multiple, playlist, album)')
            #             print('You can also use "test play all" to run every combination of this test. This can take several minutes.')
            #             continue
            #         if params[2] != 'all':
            #             test_start = time.time()
            #             result = await Tests.test_play(params[2], flags=params[3:])
            #             if result is None:
            #                 # Returns None if the test was aborted
            #                 continue
            #             print(f'{plt.gold}ARGS: {result["arguments"]} {plt.reset}\n{result["conclusion"]}')
            #             test_end = time.time()
            #             print(f'Test finished in {plt.magenta}{test_end - test_start}s')
            #         elif params[2] == 'all':
            #             # Run full test suite of all combinations
            #             confirmation = await aioconsole.ainput('> About to run every combination of -play test. This could take several minutes. Continue? (y/n) ')
            #             if confirmation.lower() != 'y':
            #                 print('> Aborted.')
            #                 continue

            #             test_results: dict[str, list] = {'pass': [], 'fail': []}
            #             test_result_string: str = ''
            #             def add_test_result(result: tuple[bool, dict]):
            #                 nonlocal test_results, test_result_string
            #                 test_result_string += f'{f'{plt.green}PASS' if result['passed'] else f'{plt.red}FAIL'} | ARGS: {result['arguments']}\n'
            #                 if result['passed']:
            #                     test_results['pass'].append((result['arguments'], result['conclusion']))
            #                 else: 
            #                     test_results['fail'].append((result['arguments'], result['conclusion']))
                        
            #             test_sources: list[str] = Tests.test_sources + ['any', 'mixed']
            #             test_start: float = time.time()
            #             tests_run: int = 0
            #             # Go through all test combinations
            #             try:
            #                 # 'invalid', 'single', and 'no-list' will be skipped over by the test function
            #                 # They're just here to make generating the combinations easier
            #                 test_conditions = itertools.product(
            #                     test_sources, 
            #                     ['valid', 'invalid'], 
            #                     ['single', 'multiple'], 
            #                     ['no-list', 'playlist', 'album']
            #                     )
            #                 for src, valid, multiple_urls, playlist_or_album in test_conditions:
            #                     add_test_result(await Tests.test_play(src, flags=[valid, multiple_urls, playlist_or_album]))
            #                     tests_run += 1
            #                     log.info(f'{plt.blue}{tests_run}{plt.reset} tests run, of which '+
            #                         f'{plt.green}{len(test_results['pass'])} have passed, and '+
            #                         f'{plt.red}{len(test_results['fail'])} have failed.'
            #                         )
            #             except Exception as e:
            #                 log.error(e)
            #                 log.info(f'{plt.red}Traceback encountered, tests aborted.')

            #             test_end: float = time.time()
            #             test_duration: float = math.floor(test_end - test_start)

            #             print(f'Finished {plt.blue}{tests_run}{plt.reset} tests.')
            #             # print(test_result_string)
            #             print(f'FINISHED IN {plt.magenta}{timestamp_from_seconds(test_duration)} or {test_duration}s{plt.reset} | PASS/FAIL: {plt.green}{len(test_results['pass'])}{plt.reset}/{plt.red}{len(test_results['fail'])}')
            #             if test_results['fail'] != []:
            #                 print('FAILED TESTS:')
            #                 for arguments, conclusion in test_results['fail']:
            #                     print(f'ARGS: {plt.gold}{arguments}\n{plt.reset}{conclusion}')
            #             else:
            #                 print(f'{plt.green}ALL TESTS PASSED')
            else:
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

async def bot_thread():
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
    asyncio_tasks['bot'] = asyncio.create_task(bot_thread())
    asyncio_tasks['console'] = asyncio.create_task(console_thread())
    try:
        await asyncio.gather(asyncio_tasks['bot'], asyncio_tasks['console'])
    except asyncio.exceptions.CancelledError:
        pass

if __name__ == '__main__':
    asyncio.run(main())
