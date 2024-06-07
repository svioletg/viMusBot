"""Provides shorthand variables mapped to colorama's color codes, for easier and quicker usage."""

# Standard imports
import re
from typing import cast

# External imports
import colorama
from colorama import Fore, Style

# Local imports
import utils.configuration as cfg

colorama.init(autoreset=True)

NO_COLOR: bool = cfg.DISABLE_LOG_COLORS

class Palette:
    """Contains color attributes and public methods."""
    def __init__(self):
        # General color names
        self.reset       = Style.RESET_ALL

        self.brightwhite = Style.BRIGHT + Fore.WHITE
        self.white       = Style.NORMAL + Fore.WHITE
        self.grey        = Style.DIM + Fore.WHITE
        self.gray = self.grey

        self.lime        = Style.BRIGHT + Fore.GREEN
        self.green       = Style.NORMAL + Fore.GREEN

        self.yellow      = Style.BRIGHT + Fore.YELLOW
        self.gold        = Style.NORMAL + Fore.YELLOW
        self.darkgold    = Style.DIM    + Fore.YELLOW

        self.lightred    = Style.BRIGHT + Fore.RED
        self.red         = Style.NORMAL + Fore.RED
        self.darkred     = Style.DIM    + Fore.RED

        self.magenta     = Style.BRIGHT + Fore.MAGENTA
        self.purple      = Style.NORMAL + Fore.MAGENTA
        self.darkpurple  = Style.DIM    + Fore.MAGENTA

        self.cyan        = Style.BRIGHT + Fore.CYAN
        self.cerulean    = Style.NORMAL + Fore.CYAN
        self.teal        = Style.DIM    + Fore.CYAN

        self.blue        = Style.BRIGHT + Fore.BLUE
        self.darkblue    = Style.NORMAL + Fore.BLUE
        self.navy        = Style.DIM    + Fore.BLUE

        # User-defined
        self._user_defined = None # This is just used for the preview display
        self.timer = self.parse_color_config('timer')
        self.module = self.parse_color_config('module')
        self.function = self.parse_color_config('function')

        self.debug = self.parse_color_config('debug')
        self.info = self.parse_color_config('info')
        self.warn = self.parse_color_config('warn')
        self.error = self.parse_color_config('error')
        self.critical = self.parse_color_config('critical')

    def parse_color_config(self, key: str) -> str:
        """Parse what's entered in the config for this key into an escape code."""
        key = cfg.LOG_COLORS[key]
        colors = key.split(' on ')
        fg = ''
        bg = ''

        if len(colors) == 0:
            fg = self.white
        if len(colors) >= 1:
            fg = getattr(self, colors[0])
        if len(colors) >= 2:
            splitstr = cast(str, getattr(self, colors[1])).split('[')
            code = splitstr[-1].strip('m')
            bg = '['.join(splitstr[:-1] + [f'{int(code) + 10}m'])
        return fg + bg


    @staticmethod
    def strip_color(string) -> str:
        """Uses regex to strip color codes from a string."""
        return re.compile(r'(\x1b\[.*?m)').sub('', string)

    def preview(self):
        """Prints out every color attribute painted in its own color code."""
        for k, v in vars(self).items():
            if k == '_user_defined':
                print('\nCurrently set color options:')
                continue
            if isinstance(v, dict):
                for k2, v2 in v.items():
                    print(f'{v2}{k}[\'{k2}\']', end=' ')
            else:
                print(v+k, end=' ')
            print()
