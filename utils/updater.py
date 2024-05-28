"""Automatic updater for the bot. Checks the locally stored version number against the latest release up on GitHub
and replaces local files if a new version exists."""

# Standard imports
import os
import shutil
import urllib.request
from pathlib import Path
from zipfile import ZipFile

# External imports
import colorama
import requests

# Local imports
from version import VERSION
from utils.palette import Palette

colorama.init(autoreset=True)
plt = Palette()

def get_latest_tag() -> dict:
    """Retrieves the latest release on the viMusBot repository and stores it along with the detected local version."""
    response: requests.Response = requests.get('https://api.github.com/repos/svioletg/viMusBot/releases/latest', timeout=5)
    latest: dict = response.json()
    latest_tag: str = latest['tag_name'].strip()

    return {'tag': latest_tag, 'response_json': latest}

def main():
    print('Checking...')

    latest: dict = get_latest_tag()
    up_to_date: bool = VERSION == latest['tag']

    if up_to_date:
        print(f'Current: {plt.gold}{VERSION}{plt.reset} | Latest: {plt.lime}{latest['tag']}')
        print('You are up to date.')
        return

    print(f'Current: {plt.gold}{VERSION}{plt.reset} | Latest: {plt.lime}{latest['tag']}')

    if input('A new version is available. Update now? (y/n) ').strip().lower() != 'y':
        print('Exiting.')
        return

    latest_zip = f'./viMusBot-{latest['tag']}.zip'

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

    with open('version.txt', 'r', encoding='utf-8') as f:
        new_version = f.read()
        print('Done!')
        print(f'You are now using: {plt.lime}v{new_version}{plt.reset}')

if __name__ == '__main__':
    main()
