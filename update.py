import colorama
from colorama import Fore, Back, Style
import inquirer
import os
import requests
import shutil
import urllib.request
from zipfile import ZipFile

from palette import Palette

colorama.init(autoreset=True)
plt = Palette()

response = requests.get("https://api.github.com/repos/svioletg/viMusBot/releases/latest")
latest = response.json()
latest_tag = latest['tag_name']

with open('version.txt', 'r') as f:
	current = f.read()

if current == latest_tag:
	print(f'{plt.yellow}{current}{plt.reset}=={plt.blue}{latest_tag}')
	print('You are up to date.')
	exit()

print(f'Your local version number:    \n{plt.gold}{current}{plt.reset}\n'+
	f'...does not match the current latest release of:    \n{plt.lime}{latest_tag}')

confirm = input('Would you like to update now? (y/n) ')
if confirm == 'n': print('Exiting.'); exit()

latest_zip = f'viMusBot-{latest_tag}.zip'

print('Retrieving: '+latest['zipball_url'])
urllib.request.urlretrieve(latest['zipball_url'], latest_zip)

print('Extracting...')
with ZipFile(latest_zip, 'r') as zipf:
	source_dir = zipf.namelist()[0]
	zipf.extractall('.')

print('Moving...')
files = os.listdir()

for f in files:
	shutil.move(os.path.join(source_dir, f), './')

print('Deleting zip...')
os.remove(latest_zip)