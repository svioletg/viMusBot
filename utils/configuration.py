"""Handles loading default and user configuration from YAML."""

# Standard imports
import itertools
import logging
import urllib.request
from pathlib import Path
from typing import Any, Literal

# External imports
import yaml
from benedict import benedict

log = logging.getLogger('viMusBot')

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

def check_type(key: str, check) -> Any:
    """Gets a config key and checks if the type is correct. Raises an error if not, returns the value if so."""
    value = get(key)
    if isinstance(value, check):
        return value
    else:
        raise TypeError(f'Error in configuration: Expected {check} for key "{key}"')

def get_full(config_type: Literal['user', 'default']) -> benedict:
    """Returns the full config benedict object."""
    return CONFIG_DICT if config_type == 'user' else CONFIG_DEFAULT_DICT

# Consts from config

log.info('Checking config...')

# For the sake of not making this module a nightmare code-wise, these checks are NOT comprehensive
# i.e. we can check if it's a list, but not if it's a list of some certain type(s).
# Just a surface-level check to catch any immediate problems

PUBLIC                  : bool                 = check_type('public', bool)
TOKEN_FILE_PATH         : str                  = check_type('token-file', str)
PUBLIC_PREFIX           : str                  = check_type('prefixes.public', str)
DEV_PREFIX              : str                  = check_type('prefixes.developer', str)
EMBED_COLOR             : int                  = int(get('embed-color'), 16) # A ValueError here means this isn't a valid hex code
INACTIVITY_TIMEOUT_MINS : int                  = check_type('inactivity-timeout', int)
CLEANUP_EXTENSIONS      : list[str]            = check_type('auto-remove', list)
DISABLED_COMMANDS       : list[str]            = check_type('command-blacklist', list)
COMMAND_ALIASES         : dict[str, list[str]] = check_type('aliases', dict)
# TODO: Merge user and default aliases dicts recursively, and check for conflicts
# existing: list[str] = []
# for key, val in COMMAND_ALIASES:
#     if val in existing:
#         log.warning('The command alias "%s" is set for multiple commands: %s', val)
#         log.warning('This will likely cause issues when attempting to use these aliases.')

LOG_LEVEL               : str                  = check_type('logging-options.console-log-level', str)
LOG_COLORS              : dict[str, str]       = check_type('logging-options.colors', dict)
DISABLE_LOG_COLORS      : bool                 = check_type('logging-options.colors.no-color', bool)
LOG_TRACEBACKS          : bool                 = check_type('logging-options.log-full-tracebacks', bool)

SHOW_USERS_IN_QUEUE     : bool = check_type('show-users-in-queue', bool)
MAX_HISTORY_LENGTH      : int  = max(check_type('play-history-max', int), 20)
ALLOW_SPOTIFY_PLAYLISTS : bool = check_type('allow-spotify-playlists', bool)
MAX_PLAYLIST_LENGTH     : int  = check_type('playlist-track-limit', int)
MAX_ALBUM_LENGTH        : int  = check_type('album-track-limit', int)
MAX_CONSECUTIVE_URLS    : int  = check_type('maximum-urls', int)
FORCE_MATCH_PROMPT      : bool = check_type('force-match-prompt', bool)
if FORCE_MATCH_PROMPT:
    log.warning('Config key "force-match-prompt" is turned on, which may cause problems if this was unintentional.')

USE_TOP_MATCH           : bool = check_type('use-top-match', bool)
DURATION_LIMIT_HOURS    : int  = check_type('duration-limit', int)
DURATION_LIMIT_SECONDS  : int  = DURATION_LIMIT_HOURS * 60 * 60

VOTE_TO_SKIP          : bool = check_type('vote-to-skip.enabled', bool)
SKIP_VOTES_EXACT      : int  = check_type('vote-to-skip.threshold-exact', int)
SKIP_VOTES_PERCENTAGE : int  = check_type('vote-to-skip.threshold-percentage', int)
if SKIP_VOTES_PERCENTAGE > 100:
    log.warning('Config key "vote-to-skip.threshold-percentage" is set higher than 100, which will make skipping impossible.')

SKIP_VOTES_TYPE       : Literal['percentage', 'exact'] = check_type('vote-to-skip.threshold-type', str)
if SKIP_VOTES_TYPE not in ['percentage', 'exact']:
    raise ValueError(f'Config key "vote-to-skip.threshold-type" must be either "percentage" or "exact" (got "{SKIP_VOTES_TYPE}")')

log.info('Config looks valid.')
