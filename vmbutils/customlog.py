# Standard libraries
import inspect
import os
import re
import time
import traceback
from datetime import datetime

# Third-party libraries
import yaml
from benedict import benedict

# Local modules
from vmbutils.palette import Palette

plt = Palette()

try:
    os.replace('vimusbot.log', 'vimusbot-old.log')
except FileNotFoundError:
    pass

logfile = open('vimusbot.log', 'w', encoding='utf-8')

with open('config_default.yml', 'r', encoding='utf-8') as f:
    config_default = benedict(yaml.safe_load(f))

with open('config.yml', 'r') as f:
    config = benedict(yaml.safe_load(f))

LOG_BLACKLIST: list = config.get('logging-options.ignore-logs-from')

def newlog(msg: str='', last_logtime: int|float=time.time(), function_source: str='', verbose: bool=False):
    for frame in inspect.stack()[1:]:
        if frame.filename[0] != '<':
            module_source = re.search(r'([^\/\\]+$)',frame.filename).group(0)
            break

    elapsed = time.time() - last_logtime
    timestamp = datetime.now().strftime('%H:%M:%S')
    logstring = f'[{timestamp}] {plt.file[module_source]}[{module_source}]{plt.reset}{plt.func} {function_source}:{plt.reset} {msg}{plt.reset} {plt.timer} {round(elapsed,3)}s'
    logfile.write(plt.strip_color(logstring)+'\n')
    blacklist_exceptions = [plt.warn, plt.error]
    if not config.get('logging-options.show-console-logs'):
        return
    elif function_source in LOG_BLACKLIST and not any(i in logstring for i in blacklist_exceptions):
        return
    elif verbose and not config.get('logging-options.show-verbose-logs'):
        return
    else:
        print(logstring)

def log(msg: str, verbose: bool=False):
    global last_logtime
    newlog(msg, last_logtime, function_source=inspect.currentframe().f_back.f_code.co_name, verbose=verbose)
    last_logtime = time.time()

def log_traceback(error: BaseException):
    trace = traceback.format_exception(error)
    log(f'Full traceback below.\n\n{plt.error}{''.join(trace)}')
