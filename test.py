import sys

from vmbutils.logging import Log

bot_logger = Log()
log = bot_logger.log
log('Test!')

match sys.argv[1]:
    case 'palette':
        import vmbutils.palette
    case 'configuration':
        import vmbutils.configuration
