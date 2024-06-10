# Standard imports

# External imports
import marko
from bs4 import BeautifulSoup, Tag

# Local imports
from utils import updating

class Changelog:
    def __init__(self, release: updating.Release):
        self.release = release
        self.md = BeautifulSoup(marko.convert(release.text), 'html.parser')

        self.developer: list[str] = self.get_list_items(self.md.find('p', 'Developer').find_next('ul')) # type: ignore
        self.features: list[str] = self.get_list_items(self.md.find('p', 'Features').find_next('ul')) # type: ignore
        self.fixes: list[str] = self.get_list_items(self.md.find('p', 'Fixes').find_next('ul')) # type: ignore
        self.other: list[str] = self.get_list_items(self.md.find('p', 'Other').find_next('ul')) # type: ignore

    @staticmethod
    def get_list_items(md_list: Tag) -> list[str]:
        if not md_list:
            return []
        raise NotImplementedError
