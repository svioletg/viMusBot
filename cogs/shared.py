# Standard imports
from typing import Optional

# External imports
from discord import Embed
from discord.ext import commands

# Local imports
import utils.configuration as config

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

def is_command_enabled(ctx: commands.Context) -> bool:
    """Checks whether this command's name is found in the configuration's list of disabled commands."""
    return not ctx.command.name in DISABLED_COMMANDS

def command_aliases(command: str) -> list[str]:
    """Returns a list of aliases for the given command."""
    return config.get(f'aliases.{command}')

def embedq(title: str, subtext: Optional[str]=None, color: int=EMBED_COLOR) -> Embed:
    """Shortcut for making embeds for messages."""
    return Embed(title=title, description=subtext, color=color)
