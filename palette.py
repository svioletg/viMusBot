import colorama
from colorama import Fore, Back, Style
import yaml

from sharedmisc import get_nested

colorama.init(autoreset=True)

with open('config_default.yml', 'r') as f:
    config_default = yaml.safe_load(f)

with open('config.yml', 'r') as f:
    config = yaml.safe_load(f)

NO_COLOR: bool = get_nested(config, config_default, 'logging-options', 'colors', 'no-color')

def get_color_config(key: str):
    return get_nested(config, config_default, 'logging-options', 'colors', key)

class Palette:
    def __init__(self):
        # General color names
        self.reset       = Style.RESET_ALL
        self.lime        = Style.BRIGHT+Fore.GREEN   if not NO_COLOR else self.reset
        self.green       = Style.NORMAL+Fore.GREEN   if not NO_COLOR else self.reset
        self.yellow      = Style.BRIGHT+Fore.YELLOW  if not NO_COLOR else self.reset
        self.gold        = Style.NORMAL+Fore.YELLOW  if not NO_COLOR else self.reset
        self.red         = Style.BRIGHT+Fore.RED     if not NO_COLOR else self.reset
        self.darkred     = Style.NORMAL+Fore.RED     if not NO_COLOR else self.reset
        self.magenta     = Style.BRIGHT+Fore.MAGENTA if not NO_COLOR else self.reset
        self.darkmagenta = Style.NORMAL+Fore.MAGENTA if not NO_COLOR else self.reset
        self.blue        = Style.BRIGHT+Fore.BLUE    if not NO_COLOR else self.reset
        self.darkblue    = Style.NORMAL+Fore.BLUE    if not NO_COLOR else self.reset
        # Make dictionary for config usage
        self.colors = vars(self)
        # User-defined
        self.file = {
            'bot.py': self.colors[get_color_config('bot.py')],
            'spoofy.py': self.colors[get_color_config('spoofy.py')],
        }
        self.warn  = self.colors[get_color_config('warn')]
        self.error = self.colors[get_color_config('error')]
        self.timer = self.colors[get_color_config('timer')]
        self.func  = self.colors[get_color_config('function')]

    def strip_color(self, string):
        for k, v in vars(self).items():
            if k == 'colors':
                # Skip the colors dictionary
                continue
            elif type(v) == dict:
                for k2, v2 in v.items():
                    string = string.replace(v2, '')
            else:
                string = string.replace(v, '')

        return string

palette = Palette()

def test():
    column = 0
    for k, v in vars(palette).items():
        if column >= 3:
            column = 0
        if k == 'colors':
            # Skip self.colors since its just the vars of Palette's attributes
            continue
        elif type(v) == dict:
            for k2, v2 in v.items():
                print(f'{v2}{k}[\'{k2}\']', end=' ')
        else:
            print(v+k, end=' ')
    input('\nPress ENTER to continue.')

if __name__ == '__main__':
    test()