import os
import shutil
import sys
import urllib.request
from pathlib import Path
from zipfile import ZipFile

import colorama
import requests

from palette import Palette

colorama.init(autoreset=True)
plt = Palette()

def check():
	response = requests.get("https://api.github.com/repos/svioletg/viMusBot/releases/latest")
	latest = response.json()
	latest_tag = latest['tag_name'].strip()

	with open('version.txt', 'r') as f:
		current = f.read().strip()

	return current == latest_tag, {'current':current, 'latest':latest}

def main():
	print('Checking...')

	verison_check = check()
	is_latest = verison_check[0]
	current = verison_check[1]['current']
	latest = verison_check[1]['latest']
	latest_tag = latest['tag_name']

	if check()[0]:
		print(f'{plt.yellow}{current}{plt.reset}=={plt.blue}{latest_tag}')
		print('You are up to date.')
		exit()

	print(f'Your local version number:\n{plt.gold}{current}{plt.reset}\n'+
		f'...does not match the current latest release of:\n{plt.lime}{latest_tag}')

	if input('Would you like to update now? (y/n) ').strip().lower() != 'n':
		print('Exiting.')
		raise SystemExit(0)
	
	latest_zip = f'./viMusBot-{latest_tag}.zip'

	print('Retrieving: '+latest['zipball_url'])
	urllib.request.urlretrieve(latest['zipball_url'], latest_zip)

	print('Extracting...')
	with ZipFile(latest_zip, 'r') as zipf:
		source_dir = zipf.namelist()[0]
		zipf.extractall('.')

	print('Copying...')
	source_dir = Path(source_dir)
	cwd = str(Path.cwd())
	shutil.copytree(source_dir, cwd, dirs_exist_ok=True)

	print('Cleaning up...')
	os.remove(latest_zip)
	shutil.rmtree(source_dir)

	with open('version.txt', 'r') as f:
		new_version = f.read()
		print('Done!')
		print(f'You are now on {plt.lime}v{new_version}{plt.reset}')

if __name__ == '__main__':
	main()