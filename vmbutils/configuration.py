"""Handles loading default and user configuration from YAML."""

from pathlib import Path
from typing import Any, Literal

import yaml
from benedict import benedict

parent_dir = Path(__file__).parent.parent

with open(Path(parent_dir, 'config_default.yml'), 'r', encoding='utf-8') as f:
    config_default = benedict(yaml.safe_load(f))

with open(Path(parent_dir, 'config.yml'), 'r', encoding='utf-8') as f:
    config = benedict(yaml.safe_load(f))

def get(key: str) -> Any:
    """Looks for the given key in the user config, returns the default value if none is set"""
    return config.get(key, config_default.get(key))

def get_full(config_type: Literal['user', 'default']) -> benedict:
    """Returns the full config benedict object"""
    return config if config_type == 'user' else config_default
