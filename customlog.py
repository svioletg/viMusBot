import inspect
import os
import re
import sys
import time
import yaml

from datetime import datetime

from palette import Palette
from sharedmisc import get_nested

plt = Palette()

try:
	os.replace('vimusbot.log', 'vimusbot-old.log')
except FileNotFoundError:
	pass

logfile = open('vimusbot.log', 'w', encoding='utf-8')

with open('config_default.yml', 'r') as f:
	config_default = yaml.safe_load(f)

with open('config.yml', 'r') as f:
	config = yaml.safe_load(f)

LOG_BLACKLIST: list = get_nested(config, config_default, 'logging-options', 'ignore-logs-from')

def newlog(msg: str='', last_logtime: int|float=time.time(), called_from: str='', verbose: bool=False):
	for frame in inspect.stack()[1:]:
		if frame.filename[0] != '<':
			source = re.search(r'([^\/\\]+$)',frame.filename).group(0)
			break

	elapsed = time.time()-last_logtime
	timestamp = datetime.now().strftime('%H:%M:%S')
	logstring = f'[{timestamp}] {plt.file[source]}[{source}]{plt.reset}{plt.func} {called_from}:{plt.reset} {msg}{plt.reset} {plt.timer} {round(elapsed,3)}s'
	logfile.write(plt.strip_color(logstring)+'\n')
	blacklist_exceptions = [plt.warn, plt.error]
	if not get_nested(config, config_default, 'logging-options', 'show-console-logs', source):
		return
	elif called_from in LOG_BLACKLIST and not any(i in logstring for i in blacklist_exceptions):
		return
	elif verbose and not get_nested(config, config_default, 'logging-options', 'show-verbose-logs'):
		return
	else:
		print(logstring)