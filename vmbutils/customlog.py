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
import vmbutils.configuration as config
from vmbutils.palette import Palette

plt = Palette()

try:
    os.replace('vimusbot.log', 'vimusbot-old.log')
except FileNotFoundError:
    pass

logfile = open('vimusbot.log', 'w', encoding='utf-8')

LOG_BLACKLIST: list = config.get('logging-options.ignore-logs-from')

def newlog(msg: str='', last_logtime: int|float=time.time(), function_source: str='', verbose: bool=False):
    for frame in inspect.stack()[1:]:
        if frame.filename[0] != '<':
            module_source = re.search(r'([^\/\\]+$)',frame.filename).group(0)
            break

    elapsed = time.time() - last_logtime
    timestamp = datetime.now().strftime('%H:%M:%S')
    logstring = f'[{timestamp}] {plt.file[module_source]}[{module_source}]{plt.reset}{plt.func} {function_source}:{plt.reset} {msg}{plt.reset} {plt.timer} {round(elapsed,3)}s'
    # Logs always get written to the logfile regardless of whether console logs are enabled
    logfile.write(plt.strip_color(logstring)+'\n')

    # Allow warnings and errors to get logged to console regardless of function blacklists
    # TODO: This is currently done by detecting colorama's color codes, probably better to use something more explicit
    # TODO: Better yet, is this really necessary at all?
    blacklist_exceptions = [plt.warn, plt.error]

    # If showing logs is disabled, don't print anything to console
    if not config.get('logging-options.show-console-logs'):
        return
    # If the function this log originates from is blacklisted, AND if any warning of error color codes aren't present, don't print to console
    elif function_source in LOG_BLACKLIST and not any(i in logstring for i in blacklist_exceptions):
        return
    # If the log is marked as verbose, and printing verbose logs is disabled, don't print to console
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
