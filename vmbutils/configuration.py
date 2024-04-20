import yaml
from benedict import benedict

with open('config_default.yml','r') as f:
    config_default = benedict(yaml.safe_load(f))

with open('config.yml','r') as f:
    config = benedict(yaml.safe_load(f))

def get(key: str):
    return config.get(key, config_default.get(key))