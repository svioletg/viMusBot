# Standard imports
import logging
import time
from asyncio import TimeoutError
from typing import Iterable, Optional

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
INACTIVITY_TIMEOUT : int       = config.get('inactivity-timeout')
CLEANUP_EXTENSIONS : list[str] = config.get('auto-remove')
DISABLED_COMMANDS  : list[str] = config.get('command-blacklist')

SHOW_USERS_IN_QUEUE      : bool = config.get('show-users-in-queue')
ALLOW_SPOTIFY_PLAYLISTS  : bool = config.get('allow-spotify-playlists')
USE_TOP_MATCH            : bool = config.get('use-top-match')
USE_URL_CACHE            : bool = config.get('use-url-cache')
SPOTIFY_PLAYLIST_LIMIT   : int  = config.get('spotify-playlist-limit')
DURATION_LIMIT           : int  = config.get('duration-limit')
MAXIMUM_CONSECUTIVE_URLS : int  = config.get('maximum-urls')

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
    return config.get(f'aliases.{command}')

def embedq(title: str, subtext: Optional[str]=None, color: int=EMBED_COLOR) -> Embed:
    """Shortcut for making embeds for messages."""
    return Embed(title=title, description=subtext, color=color)

def timestamp_from_seconds(seconds: int|float) -> str:
    """Returns a formatted string in either MM:SS or HH:MM:SS from the given time in seconds."""
    # Omit the hour place if not >=60 minutes
    return time.strftime('%M:%S' if seconds < 3600 else '%H:%M:%S', time.gmtime(seconds))

async def prompt_for_choice(bot: commands.Bot, ctx: commands.Context, prompt_msg: Message, choice_options: Iterable, timeout_seconds: int=30) -> int | str | None:
    """Adds reactions to a given Message (`prompt_msg`) and returns the outcome.

    Returns None if the prompt failed in some way or was cancelled, returns an integer if a choice was made successfully.
    """
    # Get reaction menu ready
    log.info('Prompting for reactions...')

    choice_map = {num:key for num, key in enumerate(choice_options)}
    choice_amount = len(choice_map)

    if choice_amount > len(EMOJI['num']):
        log.debug('Number of choices (%s) out of range for emoji number list.', choice_amount)
        await prompt_msg.edit(embed=embedq(f'Couldn\'t make choice prompt, limit ({len(EMOJI['num'])}) exceeded.'))
        return

    for i in range(choice_amount):
        await prompt_msg.add_reaction(EMOJI['num'][i + 1])

    await prompt_msg.add_reaction(EMOJI['cancel'])

    def check(reaction: Reaction, user: Member) -> bool:
        log.debug('Reaction check is being called...')
        return user == ctx.message.author and (str(reaction.emoji) in EMOJI['num'] or str(reaction.emoji) == EMOJI['cancel'])

    log.debug('Waiting for reaction...')

    try:
        reaction, user = await bot.wait_for('reaction_add', timeout=timeout_seconds, check=check)
    except TimeoutError:
        log.debug('Choice prompt timeout reached.')
        await prompt_msg.delete()
        return
    else:
        # If a valid reaction was received.
        log.debug('Received a valid reaction.')

        if str(reaction) == EMOJI['cancel']:
            log.debug('Selection cancelled.')
            await prompt_msg.delete()
            return
        else:
            choice = EMOJI['num'].index(str(reaction))
            log.debug('%s selected.', choice)
            await prompt_msg.delete()
            return choice
