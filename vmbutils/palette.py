"""Provides shorthand variables mapped to colorama's color codes, for easier and quicker usage."""

import re

import colorama
from colorama import Fore, Style

import vmbutils.configuration as config

colorama.init(autoreset=True)

NO_COLOR: bool = config.get('logging-options.colors.no-color')

def get_color_config(key: str) -> str:
    """Shorthand for retrieving colors from configuration."""
    try:
        color = config.get(f'logging-options.colors.{key}')
        return color if color else ''
    except KeyError:
        return ''

def get_filename_color(filename: str) -> str:
    """Retrieves the custom color set for a filename if it exists."""
    return get_color_config(filename.replace('.', '-'))

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
        self.file = get_filename_color
        self.warn: str = self.colors[get_color_config('warn')] #type: ignore
        self.error: str = self.colors[get_color_config('error')] #type: ignore
        self.timer: str = self.colors[get_color_config('timer')] #type: ignore
        self.func: str = self.colors[get_color_config('function')] #type: ignore

    def strip_color(self, string) -> str:
        """Uses regex to strip color codes from a string."""
        return re.compile(r'(\x1b\[.*?m)').sub('', string)

    def preview(self):
        """Prints out every color attribute painted in its own color code."""
        for k, v in vars(self).items():
            if k in ['colors', 'file']:
                continue
            if isinstance(v, dict):
                for k2, v2 in v.items():
                    print(f'{v2}{k}[\'{k2}\']', end=' ')
            else:
                print(v+k, end=' ')
            print()
