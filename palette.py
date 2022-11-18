import colorama
from colorama import Fore, Back, Style

colorama.init(autoreset=True)

class Palette:
	def __init__(self):
		super(Palette, self).__init__()
		# General color names
		self.reset = Style.RESET_ALL
		self.lime = Style.BRIGHT+Fore.GREEN
		self.green = Style.NORMAL+Fore.GREEN
		self.yellow = Style.BRIGHT+Fore.YELLOW
		self.gold = Style.NORMAL+Fore.YELLOW
		self.red = Style.BRIGHT+Fore.RED
		self.darkred = Style.NORMAL+Fore.RED
		self.magenta = Style.BRIGHT+Fore.MAGENTA
		self.darkmagenta = Style.NORMAL+Fore.MAGENTA
		self.blue = Style.BRIGHT+Fore.BLUE
		self.darkblue = Style.NORMAL+Fore.BLUE
		self.file = {
			'bot.py': self.yellow,
			'spoofy.py':self.lime,
		}
		# Presets
		self.warn = self.gold
		self.error = self.red
		self.timer = self.magenta
		self.func = self.blue