"""Tool to help see what's missing in `config.md`. For developer usage."""

import re
import marko
from bs4 import BeautifulSoup

import utils.configuration as cfg

with open('docs/config.md', 'r', encoding='utf-8') as f:
    md = BeautifulSoup(marko.convert(f.read()), 'html.parser')

md_keys: list[str] = ['.'.join(re.findall(r"<code>(.*?)</code>", str(h))) for h in md.find_all('h3')]

yaml_keys = cfg.CONFIG_DEFAULT_DICT.keypaths()

difference: set[str] = set(yaml_keys) - set(md_keys)

if not difference:
    print('No difference.')
else:
    print('Difference:\n')
    print('\n'.join(sorted(difference)))

print('\n')

while True:
    match input('md = Show keys found in config.md | d = Show keys found in YAML missing in config.md | e = Exit\n> ').strip().lower():
        case 'md':
            print('\n'.join(sorted(md_keys)))
        case 'd':
            print('Difference:\n')
            print('\n'.join(sorted(difference)))
        case 'e':
            raise SystemExit
        case _:
            print('Invalid option.')
