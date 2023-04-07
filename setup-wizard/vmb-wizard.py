import inquirer
import json
import os
import platform
import re
import requests
import shutil
import subprocess
<<<<<<< HEAD
<<<<<<< HEAD
=======
import sys
>>>>>>> dev
=======
import sys
>>>>>>> dev
import tkinter
import tkinter.filedialog
import urllib.request
import webbrowser

from zipfile import ZipFile

# ACQUIRE FFMPEG AUTOMATICALLY

print('Starting...\n')

ostype = platform.system()

root = tkinter.Tk()
root.withdraw()

print('Welcome to the viMusBot setup wizard.'+
	'\nThis script will guide you through configuring what you need to run the bot,'+
	'\nand will automatically acquire the necessary files.')
input('Press ENTER to continue.')

print('\nPlease select where you\'d like viMusBot to be setup in.')

while True:
	setup_dir = tkinter.filedialog.askdirectory(parent=root, title='Choose where to setup viMusBot')
	q = [inquirer.List(
		'confirm',
		message=f'Files will be downloaded to {setup_dir}. Continue?',
		choices=['Yes', 'No']
		)]
	answer = inquirer.prompt(q)
	if answer['confirm'] == 'Yes': break

# Get latest viMusBot release

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

# FFmpeg & FFprobe

print('\nGetting FFmpeg...')
ffmpeg_url = None
if ostype == 'Darwin':
	# MacOS
	# There's builds available for mac but no way to get
	# the latest release automatically like with the github
	# repository for Windows, and because I'm not able
	# to test this on Mac enough to be confident it'll work
	print('Automatic FFmpeg & FFprobe retrieval is currently unsupported for MacOS.')
	print('FFmpeg will not be automatically acquired,'+
		'\nbut setup can proceed regardless.')
	input('Press ENTER to continue.')
elif ostype == 'Linux':
	print('Since you appear to be running Linux, it is best to '+
		'\ninstall FFmpeg by opening a terminal, and running...'+
		'\nsudo apt-get install ffmpeg'+
		'\n...or the equivalent for your distro\'s package manager.')
elif ostype == 'Windows':
	response = requests.get("https://api.github.com/repos/BtbN/FFmpeg-Builds/releases/latest")
	ffmpeg = response.json()
	for i in ffmpeg['assets']:
		if 'ffmpeg-master-latest-win64-gpl.zip' in i['browser_download_url']:
			ffmpeg_url = i['browser_download_url']

	if ffmpeg_url == None:
		print('\n[!] Could not find an asset matching the system version.')
		print('FFmpeg was not able to be retrieved.')
		print('It will be required for the bot to function, however setup can continue.')
		input('Press ENTER to continue.')
	else:
		urllib.request.urlretrieve(ffmpeg_url, 'ffmpeg.zip')
		print('Extracting...')
		with ZipFile('ffmpeg.zip', 'r') as zipf:
			source_dir = zipf.namelist()[0]
			zipf.extractall('.')

		print('Copying...')
		shutil.copy(source_dir+'bin/ffmpeg.exe', './')
		shutil.copy(source_dir+'bin/ffprobe.exe', './')

		print('Cleaning up...')
		os.remove('ffmpeg.zip')
		shutil.rmtree(source_dir)
else:
	print('[!] Type of OS could not be determined.')
<<<<<<< HEAD
<<<<<<< HEAD
	print('FFmpeg will not be automatically acquired,'+
		'\nbut setup can proceed regardless.')
=======
	print('FFmpeg will not be automatically acquired, '+
		'but setup can proceed regardless.')
>>>>>>> dev
=======
	print('FFmpeg will not be automatically acquired, '+
		'but setup can proceed regardless.')
>>>>>>> dev
	input('Press ENTER to continue.')

# Token, spotify config

print('\n\n*****\n\nDone! In order for the bot to work, this script will now'+
	'\nguide you through setting up your bot token, and Spotify API credentials.')
print('Please refer to this section of the readme...'+
	'\nhttps://github.com/svioletg/viMusBot/#getting-your-credentials'+
	'\n...if you do not know where to get this information from.')

q = input('\nType "open" to open this URL in your default browser, or press ENTER to continue.\n')
if q == 'open':
	webbrowser.open('https://github.com/svioletg/viMusBot/#getting-your-credentials')

print('Follow the instructions linked above.'+
	'\nSince you are using this wizard, you may ignore any instructions about'+
	'\ncreating files, as you will simply input them here.\n')

bot_token = input('Bot token: ')
print(f'Creating token.txt...')
with open('token.txt', 'w') as f:
	f.write(bot_token)

spotify_creds = {'spotify':{}}
spotify_creds['spotify']['client_id'] = input('(Spotify) Client ID: ')
spotify_creds['spotify']['client_secret'] = input('(Spotify) Client Secret: ')
print(f'Creating spotify_config.json...')
with open('spotify_config.json', 'w') as f:
	json.dump(spotify_creds, f)

# Python Packages

print('\nThe script will now attempt to install any required Python packages.')
<<<<<<< HEAD
<<<<<<< HEAD
print('This will be done using the "py -m pip install -r requirements.txt" command.')
print('\nIf for whatever reason this will not work for you, you can skip this step.')
print('If you don\'t know what this means, it is likely best to proceed.')
=======
print(f'This will be done by running the command "{sys.executable} -m pip install -r requirements.txt"')
print('\nIf for whatever reason this will not work for you, you can skip this step.')
print('If you don\'t know what this means, it\'s likely that this won\'t be a concern.')
>>>>>>> dev
=======
print(f'This will be done by running the command "{sys.executable} -m pip install -r requirements.txt"')
print('\nIf for whatever reason this will not work for you, you can skip this step.')
print('If you don\'t know what this means, it\'s likely that this won\'t be a concern.')
>>>>>>> dev
q = [inquirer.List(
	'confirm',
	message=f'Automatically install requirements?',
	choices=['Yes', 'No']
<<<<<<< HEAD
<<<<<<< HEAD
	)]
answer = inquirer.prompt(q)
if answer['confirm'] == 'Yes':
	print('Installing required packages...')
	subprocess.run(['py', '-m', 'pip', 'install', '-r', 'requirements.txt'])
=======
=======
>>>>>>> dev
)]
answer = inquirer.prompt(q)
if answer['confirm'] == 'Yes':
	print('Installing required packages...')
	subprocess.run([sys.executable, '-m', 'pip', 'install', '-r', 'requirements.txt'])
<<<<<<< HEAD
>>>>>>> dev
=======
>>>>>>> dev
else:
	print('Skipping requirements for now.')

print('\nDone!')
print('Creating config.yml...')
shutil.copy('config_default.yml', 'config.yml')

print('\nIn the folder you specified earlier, there should now be a "config.yml" file.')
print('This contains various settings and preferences for how the bot functions,'+
	'\nand it is recommended to look through them in case you\'d like to change something.')
print('The file can be opened in any text editor, although a program like Notepad++ is suggested.')

print(f'\nThe bot should now be ready to go in {setup_dir}')
print('Run "bot.py" in a console or double-click it to start the bot.')
print('\nWhen running the bot, it will notify you if there is an update.')
print('You can update the bot automatically by running "update.py".')

input('\nPress ENTER to exit the setup wizard.')