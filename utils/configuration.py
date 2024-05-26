"""Handles loading default and user configuration from YAML."""

# Standard imports
import urllib.request
from pathlib import Path
from typing import Any, Literal

# External imports
import yaml
from benedict import benedict

CONFIG_PATHS: dict[str, str] = {
    'user': 'config.yml', 
    'default': 'config_default.yml'
}

if not Path(CONFIG_PATHS['default']).is_file():
    print('config_default.yml not found; downloading the latest version...')
    urllib.request.urlretrieve('https://raw.githubusercontent.com/svioletg/viMusBot/master/config_default.yml',
        Path(CONFIG_PATHS['default']))

if not Path(CONFIG_PATHS['user']).is_file():
    print('config.yml does not exist; creating blank config.yml...')
    with open(CONFIG_PATHS['user'], 'w', encoding='utf-8') as f:
        f.write('')

with open(CONFIG_PATHS['default'], 'r', encoding='utf-8') as f:
    CONFIG_DEFAULT_DICT = benedict(yaml.safe_load(f))

with open(CONFIG_PATHS['user'], 'r', encoding='utf-8') as f:
    CONFIG_YAML = yaml.safe_load(f)
    CONFIG_DICT = benedict(CONFIG_YAML) if CONFIG_YAML else benedict({})

def get(key: str) -> Any:
    """Looks for the given key in the user config, returns the default value if none is set."""
    return CONFIG_DICT.get(key, CONFIG_DEFAULT_DICT.get(key))

def get_default(key: str) -> Any:
    """Returns the default value for a given key."""
    return CONFIG_DEFAULT_DICT.get(key)

def get_full(config_type: Literal['user', 'default']) -> benedict:
    """Returns the full config benedict object."""
    return CONFIG_DICT if config_type == 'user' else CONFIG_DEFAULT_DICT

# Bot
PUBLIC                  : bool                 = get('public')
TOKEN_FILE_PATH         : str                  = get('token-file')
PUBLIC_PREFIX           : str                  = get('prefixes.public')
DEV_PREFIX              : str                  = get('prefixes.developer')
EMBED_COLOR             : int                  = int(get('embed-color'), 16)
INACTIVITY_TIMEOUT_MINS : int                  = get('inactivity-timeout')
CLEANUP_EXTENSIONS      : list[str]            = get('auto-remove')
DISABLED_COMMANDS       : list[str]            = get('command-blacklist')
COMMAND_ALIASES         : dict[str, list[str]] = get('aliases')
LOG_LEVEL               : str                  = get('logging-options.console-log-level')
LOG_COLORS              : dict[str, str]       = get('logging-options.colors')
DISABLE_LOG_COLORS      : dict[str, str]       = get('logging-options.colors.no-color')
LOG_TRACEBACKS          : bool                 = get('logging-options.log-full-tracebacks')

SHOW_USERS_IN_QUEUE      : bool = get('show-users-in-queue')
ALLOW_SPOTIFY_PLAYLISTS  : bool = get('allow-spotify-playlists')
SPOTIFY_PLAYLIST_LIMIT   : int  = get('spotify-playlist-limit')
FORCE_MATCH_PROMPT       : bool = get('force-match-prompt')
USE_TOP_MATCH            : bool = get('use-top-match')
USE_URL_CACHE            : bool = get('use-url-cache')
DURATION_LIMIT_SECONDS   : int  = get('duration-limit')
MAXIMUM_CONSECUTIVE_URLS : int  = get('maximum-urls')
MAXIMUM_HISTORY_LENGTH   : int  = get('play-history-max')

VOTE_TO_SKIP          : bool = get('vote-to-skip.enabled')
SKIP_VOTES_TYPE       : str  = get('vote-to-skip.threshold-type')
SKIP_VOTES_EXACT      : int  = get('vote-to-skip.threshold-exact')
SKIP_VOTES_PERCENTAGE : int  = get('vote-to-skip.threshold-percentage')
