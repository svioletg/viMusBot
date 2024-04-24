import yaml
from benedict import benedict

from typing import TypedDict

# TODO: Maybe figure out some way to make this compatible with type checking?
# Could potentially be done with a TypedDict, but I don't think I can use that with benedict
with open('config_default.yml','r') as f:
    config_default = benedict(yaml.safe_load(f))

with open('config.yml','r') as f:
    config = benedict(yaml.safe_load(f))

def get(key: str):
    """
    Looks for the given key in the user config, returns the default value if none is set
    """
    return config.get(key, config_default.get(key))

def get_full() -> benedict:
    """
    Returns the full config benedict object
    """
    return config
