import colorama
from colorama import Fore, Back, Style
import requests

from palette import Palette

colorama.init(autoreset=True)
plt = Palette()

response = requests.get("https://api.github.com/repos/svioletg/viMusBot/releases/latest")
latest = response.json()
latest_tag = latest['tag_name']

with open('version.txt', 'r') as f:
	current = f.read()

if current != latest_tag:
	print(f'Your local version number, {plt.yellow}{current}, '+
		f'does not match the current latest release of {plt.blue}{latest_tag}.')
	q = input('Would you like to update now? ')
else:
	print(f'{plt.yellow}{current}{plt.reset}=={plt.blue}{latest_tag}')
	print('You are up to date.')