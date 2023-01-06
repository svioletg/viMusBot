import inquirer
import json
import os
import platform
import re
import requests
import shutil
import subprocess
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

print('Getting FFmpeg...')
# TODO: this downloads the source code, check the JSON to see where the
# releases are stored like the gpl folders
ffmpeg_url = None
if ostype == 'Windows':
	response = requests.get("https://api.github.com/repos/BtbN/FFmpeg-Builds/releases/latest")
	ffmpeg = response.json()
	for i in ffmpeg['assets']:
		if 'ffmpeg-master-latest-win64-gpl.zip' in i['browser_download_url']:
			ffmpeg_url = i
elif ostype == 'Linux':
	response = requests.get("https://api.github.com/repos/BtbN/FFmpeg-Builds/releases/latest")
	ffmpeg = response.json()
	for i in ffmpeg['assets']:
		if 'ffmpeg-master-latest-linux64-gpl.tar.xz' in i['browser_download_url']:
			ffmpeg_url = i

if ffmpeg_url == None:
	print('\n[!] Could not find an asset matching the system version.')
	print('FFmpeg was not able to be retrieved.')
	print('It will be required for the bot to function, however setup can continue.')
	input('Press ENTER to continue.')
else:
	match = re.search(r'.*(\..*$)', ffmpeg_url)
	if match == None:
		print('\n[!] Regex match for file extension failed.')
		print('FFmpeg was not able to be retrieved.')
		print('It will be required for the bot to function, however setup can continue.')
		input('Press ENTER to continue.')
	extension = match[1]
	if extension == '.xz': extension = '.tar.xz'
	urllib.request.urlretrieve(ffmpeg_url, f'ffmpeg.{extension}')

print('\nDone! In order for the bot to work, this script will now'+
	'\nguide you through setting up your bot token, and Spotify API credentials.')
print('Please refer to this section of the readme...'+
	'\nhttps://github.com/svioletg/viMusBot/#getting-your-credentials'+
	'...if you do not know where to get this information from.')
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

print('\nThe script will not attempt to install any required Python packages.')
print('This will be done using the "py -m pip install -r requirements.txt" command.')
print('\nIf for whatever reason this will not work for you, you can skip this step.')
print('If you don\'t know what this means, it is likely best to proceed.')
q = [inquirer.List(
	'confirm',
	message=f'Automatically install requirements?',
	choices=['Yes', 'No']
	)]
answer = inquirer.prompt(q)
if answer['confirm'] == 'Yes':
	print('Installing required packages...')
	subprocess.run(['py', '-m', 'pip', 'install', '-r', 'requirements.txt'])
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

input('\nPress ENTER to exit the setup wizard.')