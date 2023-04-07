import colorama
from colorama import Fore, Back, Style
import yaml

colorama.init(autoreset=True)

with open('config.yml', 'r') as f:
	config = yaml.safe_load(f)

colorconfig = config['logging-options']['colors']

if colorconfig['no-color']==True:
	for i in colorconfig:
		colorconfig[i] = 'reset'

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
		# Make dictionary for config usage
		self.colors = vars(self)
		# User-defined
		self.file = {
			'bot.py': self.colors[colorconfig['bot.py']],
			'spoofy.py': self.colors[colorconfig['spoofy.py']],
		}
		self.warn = self.colors[colorconfig['warn']]
		self.error = self.colors[colorconfig['error']]
		self.timer = self.colors[colorconfig['timer']]
		self.func = self.colors[colorconfig['function']]

	def strip_color(self, string):
		for k, v in vars(self).items():
			if k=='colors':
				# Skip the colors dictionary
				continue
			elif type(v)==dict:
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
<<<<<<< HEAD
<<<<<<< HEAD
			print(v+k)
	input('Press ENTER to continue.')
=======
			print(v+k, end=' ')
	input('\nPress ENTER to continue.')
>>>>>>> dev
=======
			print(v+k, end=' ')
	input('\nPress ENTER to continue.')
>>>>>>> dev

if __name__ == '__main__':
	test()