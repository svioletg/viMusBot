import colorama
from colorama import Fore, Back, Style

colorama.init(autoreset=True)

class Palette:
	def __init__(self):
		super(Palette, self).__init__()
		self.reset = Style.RESET_ALL
		self.file = {
			'bot.py':Style.BRIGHT+Fore.YELLOW,
			'spoofy.py':Style.BRIGHT+Fore.GREEN,
		}
		self.warn = Style.NORMAL+Fore.YELLOW
		self.error = Style.NORMAL+Fore.RED
		self.timer = Style.BRIGHT+Fore.MAGENTA
		self.func = Style.BRIGHT+Fore.BLUE