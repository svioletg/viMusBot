"""General-purpose, miscellaneous utility methods."""

# Standard imports
import logging
import colorlog
from pathlib import Path
from sys import stdout

# Local imports
import utils.configuration as config
from utils.palette import Palette

plt = Palette()

def create_logger(logger_name: str, logfile: str | Path) -> logging.Logger:
    levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
    use_color: bool = not config.get('logging-options.colors.no-color')
    new_logger = colorlog.getLogger(logger_name)
    log_string = '[%(asctime)s] [%(module_log_color)s%(filename)s%(reset)s/%(log_color)s%(levelname)s%(reset)s]'+\
        '@ %(func_log_color)s%(funcName)s%(reset)s: %(log_color)s%(message)s'
    date_format = '%y-%m-%d %H:%M:%S'

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

    log_format_no_color = colorlog.ColoredFormatter(log_string, datefmt=date_format,
        log_colors=get_log_colors(use_color=False),
        secondary_log_colors=get_secondary_log_colors(use_color=False)
    )
    log_format_colored = colorlog.ColoredFormatter(log_string, datefmt=date_format,
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
