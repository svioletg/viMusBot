import colorama
<<<<<<< HEAD
<<<<<<< HEAD
from colorama import Fore, Back, Style
import inquirer
=======
>>>>>>> dev
=======
>>>>>>> dev
import os
import requests
import shutil
import sys
<<<<<<< HEAD
<<<<<<< HEAD
=======
import tkinter
import tkinter.filedialog
>>>>>>> dev
=======
import tkinter
import tkinter.filedialog
>>>>>>> dev
import urllib.request
from zipfile import ZipFile

from palette import Palette

<<<<<<< HEAD
<<<<<<< HEAD
=======
=======
>>>>>>> dev
# Just so I can test this in another directory
if '--test' in sys.argv:
	root = tkinter.Tk()
	root.withdraw()
	target_dir = tkinter.filedialog.askdirectory(parent=root, title='Choose where to setup viMusBot')
else:
	target_dir = '.'

<<<<<<< HEAD
>>>>>>> dev
=======
>>>>>>> dev
colorama.init(autoreset=True)
plt = Palette()

def check():
	response = requests.get("https://api.github.com/repos/svioletg/viMusBot/releases/latest")
	latest = response.json()
<<<<<<< HEAD
<<<<<<< HEAD
	latest_tag = latest['tag_name']

	with open('version.txt', 'r') as f:
		current = f.read()
=======
=======
>>>>>>> dev
	latest_tag = latest['tag_name'].strip()

	with open('version.txt', 'r') as f:
		current = f.read().strip()
<<<<<<< HEAD
>>>>>>> dev
=======
>>>>>>> dev

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

	confirm = input('Would you like to update now? (y/n) ')
	if confirm == 'n': print('Exiting.'); exit()

<<<<<<< HEAD
<<<<<<< HEAD
	latest_zip = f'viMusBot-{latest_tag}.zip'
=======
	latest_zip = f'{target_dir}/viMusBot-{latest_tag}.zip'
>>>>>>> dev
=======
	latest_zip = f'{target_dir}/viMusBot-{latest_tag}.zip'
>>>>>>> dev

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

if __name__ == '__main__':
	main()