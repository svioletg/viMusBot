import inquirer
import os
import platform
import requests
import shutil
import tkinter
import tkinter.filedialog
import urllib.request

from zipfile import ZipFile

print('Starting...\n')

ostype = platform.system()

root = tkinter.Tk()
root.withdraw()

print('Welcome to the viMusBot setup wizard.'+
	'\nThis script will guide you through configuring what you need to run the bot,'+
	'\nand will automatically acquire the necessary files.')
print('\nPlease select where you\'d like viMusBot to be setup in.')
input('Press ENTER to open the selection prompt.')

while True:
	setup_dir = tkinter.filedialog.askdirectory(parent=root, title='Choose where to setup viMusBot')
	q = [inquirer.List(
		'confirm',
		message=f'Files will be downloaded to {setup_dir}. Continue?',
		choices=['Yes', 'No']
		)]
	answer = inquirer.prompt(q)
	if answer['confirm'] == 'Yes': break

# Start downloading
print('Getting the latest version...')
response = requests.get("https://api.github.com/repos/svioletg/viMusBot/releases/latest")
latest = response.json()
latest_tag = latest['tag_name']
latest_zip = f'viMusBot-{latest_tag}.zip'

os.chdir(setup_dir)

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