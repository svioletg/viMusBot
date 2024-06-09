"""Automatic updater for the bot. Checks the locally stored version number against the latest release up on GitHub,
and replaces local files if a new version exists."""

# Standard imports
import os
import re
import shutil
import sys
import urllib.request
from pathlib import Path
from string import ascii_lowercase
from typing import Self
from zipfile import ZipFile

# External imports
import colorama
import requests

# Local imports
from utils.palette import Palette
from version import VERSION

colorama.init(autoreset=True)
plt = Palette(load_config=False)

class Release:
    """Organizes useful information from a GitHub API reponse of a release."""
    def __init__(self, response_json: dict):
        """
        @response_json: Dictionary retrieved from using `.json()` on a `Response`.
        """
        self.name: str = response_json['name']
        self.tag: str = response_json['tag_name']
        self.version: tuple[int, ...] = self.get_version_tuple(self.tag)

        self.url: str = response_json['html_url']
        self.zip: str = response_json['zipball_url']
        self.tarball: str = response_json['tarball_url']

        self.is_prerelease: bool = response_json['prerelease']
        self.is_draft: bool = response_json['draft']

        self.text: str = response_json['body']
        self.date: str = re.match(r"(\d{4}-\d{2}-\d{2})", response_json['published_at'])[0] # type: ignore

    @classmethod
    def from_url(cls, github_url: str) -> Self:
        """Creates a `Release` from a GitHub API release URL."""
        response = requests.get(github_url, timeout=5)
        return cls(response.json())

    @staticmethod
    def get_version_tuple(tag_string: str) -> tuple[int, ...]:
        """Turns a tag string (e.g. `"1.8.3c") into a tuple of integers. (e.g. `(1, 8, 3, 3)`)
        Version extension letters will be turned into integers based off their alphabetical position."""
        version: list = tag_string.split('.')
        if version[0] == 'dev':
            return (-1, int(version[1]))
        if version_ext := re.findall(r"([a-z])", version[-1]):
            version[-1] = re.sub(r"([a-z])", '', version[-1])
            version.append(ascii_lowercase.index(version_ext[0]) + 1)
        return tuple(map(int, version))

def get_latest_tag() -> Release:
    """Retrieves the latest release on the viMusBot repository and stores it along with the detected local version."""
    return Release.from_url('https://api.github.com/repos/svioletg/viMusBot/releases/latest')

def main():
    print('Checking...')

    VERSION = '1.9.0'

    latest = get_latest_tag()
    local = Release.get_version_tuple(VERSION)

    if local[0] == -1:
        print('Development version detected; can\'t compare to latest.')
        print('Exiting.')
        return

    if local == latest.version:
        print('You are up to date.')
        print(f'Current: {plt.lime}{VERSION}{plt.reset} = Latest: {plt.lime}{latest.tag}')
        print('Exiting.')
        return

    if latest.version > local:
        print('A new update is available.')
        print(f'Current: {plt.gold}{VERSION}{plt.reset} < Latest: {plt.lime}{latest.tag}')

    if input('\nUpdate now? (y/n) ').strip().lower() != 'y':
        print('Exiting.')
        return

    latest_archive = Path(f'viMusBot-{latest.tag}.zip')

    print('Retrieving: ' + latest.zip)
    urllib.request.urlretrieve(latest.zip, latest_archive)

    print('Extracting...')
    with ZipFile(latest_archive, 'r') as zipf:
        extract_destination = Path(zipf.namelist()[0])
        zipf.extractall('newupdate')
        return

    print('Copying...')
    cwd = str(Path.cwd())
    shutil.copytree(extract_destination, cwd, dirs_exist_ok=True)

    print('Cleaning up...')
    os.remove(latest_archive)
    shutil.rmtree(extract_destination)

    with open('version.txt', 'r', encoding='utf-8') as f:
        new_version = f.read()
        print('Done!')
        print(f'You are now on: {plt.lime}v{new_version}{plt.reset}')

if __name__ == '__main__':
    main()
