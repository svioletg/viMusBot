# Standard imports
import asyncio
import logging
import time
from typing import Optional

# External imports
from discord import Embed, Member, Message, Reaction
from discord.ext import commands

# Local imports
import utils.configuration as config

log = logging.getLogger('viMusBot')

PUBLIC             : bool      = config.get('public')
TOKEN_FILE_PATH    : str       = config.get('token-file')
PUBLIC_PREFIX      : str       = config.get('prefixes.public')
DEV_PREFIX         : str       = config.get('prefixes.developer')
EMBED_COLOR        : int       = int(config.get('embed-color'), 16)
INACTIVITY_TIMEOUT_MINS : int       = config.get('inactivity-timeout')
CLEANUP_EXTENSIONS : list[str] = config.get('auto-remove')
DISABLED_COMMANDS  : list[str] = config.get('command-blacklist')
LOG_LEVEL          : str       = config.get('logging-options.console-log-level')
LOG_TRACEBACKS     : bool      = config.get('logging-options.log-full-tracebacks')

SHOW_USERS_IN_QUEUE      : bool = config.get('show-users-in-queue')
ALLOW_SPOTIFY_PLAYLISTS  : bool = config.get('allow-spotify-playlists')
USE_TOP_MATCH            : bool = config.get('use-top-match')
USE_URL_CACHE            : bool = config.get('use-url-cache')
SPOTIFY_PLAYLIST_LIMIT   : int  = config.get('spotify-playlist-limit')
DURATION_LIMIT           : int  = config.get('duration-limit')
MAXIMUM_CONSECUTIVE_URLS : int  = config.get('maximum-urls')
MAXIMUM_HISTORY_LENGTH   : int  = config.get('play-history-max')

VOTE_TO_SKIP          : bool = config.get('vote-to-skip.enabled')
SKIP_VOTES_TYPE       : str  = config.get('vote-to-skip.threshold-type')
SKIP_VOTES_EXACT      : int  = config.get('vote-to-skip.threshold-exact')
SKIP_VOTES_PERCENTAGE : int  = config.get('vote-to-skip.threshold-percentage')

EMOJI = {
    'cancel': '❌',
    'confirm': '✅',
    'repeat': '🔁',
    'info': 'ℹ️',
    'num': [
        '0️⃣', '1️⃣', '2️⃣', '3️⃣', '4️⃣', '5️⃣', '6️⃣', '7️⃣', '8️⃣', '9️⃣', '🔟',
    ],
}

def is_command_enabled(ctx: commands.Context) -> bool:
    """Checks whether this command's name is found in the configuration's list of disabled commands."""
    return not ctx.command.name in DISABLED_COMMANDS

def command_aliases(command: str) -> list[str]:
    """Returns a list of aliases for the given command."""
    return config.get(f'aliases.{command}') or []

def embedq(title: str, subtext: Optional[str]=None, color: int=EMBED_COLOR) -> Embed:
    """Shortcut for making embeds for messages."""
    return Embed(title=title, description=subtext, color=color)

def timestamp_from_seconds(seconds: int|float) -> str:
    """Returns a formatted string in either MM:SS or HH:MM:SS from the given time in seconds."""
    # Omit the hour place if not >=60 minutes
    return time.strftime('%M:%S' if seconds < 3600 else '%H:%M:%S', time.gmtime(seconds))

async def prompt_for_choice(bot: commands.Bot, ctx: commands.Context,
    prompt_msg: Message, choice_nums: int, timeout_seconds: int=30, delete_after: bool=True) -> int | asyncio.TimeoutError | ValueError:
    """Adds reactions to a given Message (`prompt_msg`) and returns the outcome.

    Returns the chosen number if a valid selection was made, otherwise a `TimeoutError` if a timeout occurred,\
    a `ValueError` if `choice_nums` was greater than 10, or 0 if the selection was cancelled.

    @prompt_msg: A `Message` containing the choices that will be edited or deleted depending on the outcome.
    @choice_nums: How many choices to give. Will always start at 1 and end at `cohice_nums`. Maximum of 10,\
        as that is the highest number an individual emoji can represent.
    @timeout_seconds: (`30`) How long to wait before automatically cancelling the prompt, in seconds.
    @delete_after: (`True`) Whether to delete the choice prompt after either a timeout has occurred,\
        the selection was cancelled, or a valid selection was made.
    """
    # Get reaction menu ready
    log.info('Prompting for reactions...')

    if choice_nums > len(EMOJI['num']):
        log.debug('Number of choices (%s) out of range for emoji number list.', choice_nums)
        await prompt_msg.edit(embed=embedq(f'Couldn\'t make choice prompt, limit ({len(EMOJI['num'])}) exceeded.'))
        return ValueError('choice_nums can not be greater than 10.')

    for i in range(choice_nums):
        await prompt_msg.add_reaction(EMOJI['num'][i + 1])

    await prompt_msg.add_reaction(EMOJI['cancel'])

    def check(reaction: Reaction, user: Member) -> bool:
        return user == ctx.message.author and (str(reaction.emoji) in EMOJI['num'] or str(reaction.emoji) == EMOJI['cancel'])

    log.debug('Waiting for reaction...')

    try:
        reaction, user = await bot.wait_for('reaction_add', timeout=timeout_seconds, check=check)
    except asyncio.TimeoutError as e:
        log.debug('Choice prompt timeout reached.')
        if delete_after:
            await prompt_msg.delete()
        return e

    # If a valid reaction was received.
    log.debug('Received a valid reaction.')

    if str(reaction) == EMOJI['cancel']:
        log.debug('Selection cancelled.')
        if delete_after:
            await prompt_msg.delete()
        return 0

    choice = EMOJI['num'].index(str(reaction))
    log.debug('%s selected.', choice)
    if delete_after:
        await prompt_msg.delete()
    return choice
