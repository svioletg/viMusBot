"""Handles loading default and user configuration from YAML."""

from typing import Any, Literal

import yaml
from benedict import benedict

CONFIG_PATHS: dict[str, str] = {
    'user': 'config.yml', 
    'default': 'config_default.yml'
}

with open(CONFIG_PATHS['default'], 'r', encoding='utf-8') as f:
    config_default = benedict(yaml.safe_load(f))

with open(CONFIG_PATHS['user'], 'r', encoding='utf-8') as f:
    config_yaml = yaml.safe_load(f)
    config = benedict(config_yaml) if config_yaml else benedict({})

def get(key: str) -> Any:
    """Looks for the given key in the user config, returns the default value if none is set."""
    return config.get(key, config_default.get(key))

def get_default(key: str) -> Any:
    """Returns the default value for a given key."""
    return config_default.get(key)

def get_full(config_type: Literal['user', 'default']) -> benedict:
    """Returns the full config benedict object."""
    return config if config_type == 'user' else config_default
