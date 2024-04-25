"""Custom logging module for viMusBot"""

# Standard libraries
import inspect
import os
import re
import time
import traceback
from datetime import datetime
from pathlib import Path

# Third-party libraries
from benedict import benedict

# Local modules
import vmbutils.configuration as config
from vmbutils.palette import Palette

LOG_OPTIONS: benedict = config.get('logging-options') # type: ignore
LOG_BLACKLIST: list[str] = config.get('logging-options.ignore-logs-from') # type: ignore
LOG_FILE: Path = Path('../vimusbot.log')

plt = Palette()

try:
    os.replace(LOG_FILE, Path('vimusbot-old.log'))
except FileNotFoundError:
    pass

class Log:
    """Inner class to actually handle the logging"""
    def __init__(self):
        self.last_logtime: float = 0

    def log(self, msg: str,
            last_logtime: float = time.time(),
            function_source: str = inspect.currentframe().f_back.f_code.co_name, # type: ignore
            verbose: bool = False):
        """Constructs a log string, writes it to the log file, and returns the string"""
        module_source: str = '<unknown>'
        for frame in inspect.stack()[1:]:
            if frame.filename[0] != '<':
                module_source = re.search(r'([^\/\\]+$)', frame.filename).group(0) # type: ignore
                break

        elapsed = time.time() - last_logtime
        timestamp = datetime.now().strftime('%H:%M:%S')
        log_string = f'[{timestamp}] {plt.file(module_source)}[{module_source}] '+\
            f'{plt.func}{function_source}:{plt.reset} {msg}{plt.reset} '+\
            f'{plt.timer}... {round(elapsed,3)}s'
        # Logs always get written to the logfile regardless of whether console logs are enabled
        with open(LOG_FILE, 'w', encoding='utf-8') as f:
            f.write(plt.strip_color(log_string)+'\n')

        # Allow warnings and errors to get logged to console regardless of function blacklists
        # TODO: This is currently done by detecting colorama's color codes, probably better to use something more explicit
        # TODO: Better yet, is this really necessary at all?
        blacklist_exceptions = [plt.warn, plt.error]

        # If showing logs is disabled, don't print anything to console
        if LOG_OPTIONS.get('show-console-logs'):
            # TODO: Has to be a better way to do these checks.
            if not (function_source in LOG_BLACKLIST \
                    and not any(i in log_string for i in blacklist_exceptions))\
                    and not (verbose and not LOG_OPTIONS.get('show-verbose-logs')):
                print(log_string)

        self.last_logtime = time.time()

    def log_traceback(self, error: BaseException):
        """Logs the traceback of a given exception to the file, and the console if applicable"""
        trace = traceback.format_exception(error)
        self.log(f'Full traceback below.\n\n{plt.error}{''.join(trace)}')
