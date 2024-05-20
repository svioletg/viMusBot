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
