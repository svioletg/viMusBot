"""General-purpose, miscellaneous utility methods."""

# Standard imports
import logging
import re
import time
from pathlib import Path
from sys import stdout
from typing import Callable

# External imports
import colorlog

# Local imports
import utils.configuration as config
from utils.palette import Palette

plt = Palette()

def time_func(func: Callable, printout: bool=True) -> float:
    """Times the execution of a callable, prints out the result if allowed, and returns the result of the called function
    
    @printout: Whether to print a string containing the time elapsed
    """
    ta = time.perf_counter()
    func_result = func()
    tb = time.perf_counter()
    if printout:
        print(f'{func} ... completed in ... {tb - ta}s')
    return func_result

def create_logger(logger_name: str, logfile: str | Path) -> logging.Logger:
    levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
    use_color: bool = not config.get('logging-options.colors.no-color')
    new_logger = colorlog.getLogger(logger_name)
    date_format = '%y-%m-%d %H:%M:%S'
    log_string_pre = '[%(asctime)s] [{c_module_}%(filename)s%(reset)s/{c_}%(levelname)s%(reset)s]'+\
        ' in {c_func_}%(funcName)s%(reset)s: {c_}%(message)s'
    
    log_string_no_color = re.sub(r"({c_(.*?)})", '', log_string_pre)
    log_string_no_color = re.sub(r"%\(reset\)s", '', log_string_no_color)
    log_string_colored = re.sub(r"({c_(.*?)})", r'%(\2log_color)s', log_string_pre)

    print(log_string_no_color)
    print(log_string_colored)

    def get_log_colors(use_color: bool=True):
        log_colors = {
            'DEBUG':    'cyan' if use_color else '',
            'INFO':     'green'  if use_color else '',
            'WARNING':  'yellow'  if use_color else '',
            'ERROR':    'red'  if use_color else '',
            'CRITICAL': 'red,bg_white' if use_color else ''
        }
        return log_colors
    
    def get_secondary_log_colors(use_color: bool=True):
        secondary_log_colors = {
            'module': {l:'purple' if use_color else '' for l in levels},
            'func': {l:'blue' if use_color else '' for l in levels},
        }
        return secondary_log_colors

    log_format_no_color = logging.Formatter(log_string_no_color, datefmt=date_format)
    log_format_colored = colorlog.ColoredFormatter(log_string_colored, datefmt=date_format,
        log_colors=get_log_colors(use_color=use_color),
        secondary_log_colors=get_secondary_log_colors(use_color=use_color)
    )

    stdout_handler = colorlog.StreamHandler(stream=stdout)
    stdout_handler.setFormatter(log_format_colored)
    stdout_handler.setLevel(colorlog.INFO)

    file_handler = logging.FileHandler(filename=logfile, encoding='utf-8', mode='w')
    file_handler.setFormatter(log_format_no_color)
    file_handler.setLevel(logging.DEBUG)

    new_logger.addHandler(stdout_handler)
    new_logger.addHandler(file_handler)

    new_logger.setLevel(colorlog.DEBUG)
    return new_logger
