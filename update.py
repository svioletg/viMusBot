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

def check():
	response = requests.get("https://api.github.com/repos/svioletg/viMusBot/releases/latest")
	latest = response.json()
	latest_tag = latest['tag_name']

	with open('version.txt', 'r') as f:
		current = f.read()

	return current == latest_tag, {'current':current, 'latest':latest_tag}

def main():
	print('Checking...')

	if check()[0]:
		print(f'{plt.yellow}{current}{plt.reset}=={plt.blue}{latest_tag}')
		print('You are up to date.')
		exit()

	print(f'Your local version number:\n{plt.gold}{current}{plt.reset}\n'+
		f'...does not match the current latest release of:\n{plt.lime}{latest_tag}')

	confirm = input('Would you like to update now? (y/n) ')
	if confirm == 'n': print('Exiting.'); exit()

	latest_zip = f'viMusBot-{latest_tag}.zip'

	print('Retrieving: '+latest['zipball_url'])
	urllib.request.urlretrieve(latest['zipball_url'], latest_zip)

	print('Extracting...')
	with ZipFile(latest_zip, 'r') as zipf:
		source_dir = zipf.namelist()[0]
		zipf.extractall('.')

	print('Copying...')
	files = os.listdir(source_dir)
	for f in files:
		try:
			shutil.copy(os.path.join(source_dir, f), './')
		except PermissionError as e:
			if f != '.github':
				# Skipping .github is fine, log any other
				# unexpected file errors
				print(e)
				print(f'Skipping {f}...')
			else:
				pass

	print('Cleaning up...')
	os.remove(latest_zip)
	shutil.rmtree(source_dir)

	with open('version.txt', 'r') as f:
		new_version = f.read()
		print('Done!')
		print(f'You are now on {plt.lime}v{new_version}{plt.reset}.')