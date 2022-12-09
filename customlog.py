import os
import sys
import yaml
import inspect
import re
import time
from datetime import datetime
from palette import Palette

plt = Palette()

try:
	os.replace('vimusbot.log','vimusbot-old.log')
except FileNotFoundError:
	pass

logfile = open('vimusbot.log','w')

with open('config.yml','r') as f:
	config = yaml.safe_load(f)

log_blacklist = config['logging-options']['ignore-logs-from']

def newlog(msg='', last_logtime=time.time(), called_from=''):
	for frame in inspect.stack()[1:]:
		if frame.filename[0] != '<':
			source = re.search(r'([^\/\\]+$)',frame.filename).group(0)
			break

	elapsed = time.time()-last_logtime
	timestamp = datetime.now().strftime('%m-%d-%Y %H:%M:%S')
	logstring = f'[{timestamp}] [{source}] {called_from}: {msg}  {round(elapsed,3)}s'
	logfile.write(logstring+'\n')

	logstring = f'{plt.file[source]}[{source}]{plt.reset}{plt.func} {called_from}:{plt.reset} {msg}{plt.reset} {plt.timer} {round(elapsed,3)}s'
	blacklist_exceptions = [plt.warn, plt.error]
	if (any(i in logstring for i in blacklist_exceptions) or called_from not in log_blacklist) and config['logging-options']['show-console-logs'][source]:
		print(logstring)