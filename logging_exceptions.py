import logging
import logging.handlers
import sys
import os.path

__all__ = [ 'attach_log_to_exception', 'attach', 'log_exception', 'log',
            'update_parser', 'config_from_args']

###############################################################################
### A costum sys.excepthook that displays all log messages
### associated with an unhandled exception.
###############################################################################

# The except_hook before we modify it
default_excepthook = sys.excepthook

def logging_excepthook(type, exception, traceback):
    """
    A except_hook that inspects the exception for the 'log' attribute.
    If it finds this attribute, it logs the contained log-records with the
    level ''critical' before calling default_excepthook
    """
    if hasattr(exception, "log"):
        for record in exception.log:
            logging.getLogger().handle(record)
    default_excepthook(type, exception, traceback)

sys.excepthook = logging_excepthook

###############################################################################
### Public API for attaching log messages to exceptions and
### for displaying logs associated with caught exceptions.
###############################################################################

def attach_log_to_exception(exception, msg, *args):
    """
    Adds a log-record to the exception's 'log' attribute

    Creates the 'log' list, if the attribute does not yet exist.

    msg, and args are the same as for logging.Logger.debug()
    """
    logger = logging.getLogger(__name__)

    fn, lno, func = _find_caller()
    record = logging.LogRecord(type(exception).__name__, logging.CRITICAL, fn,
                               lno, msg, args, None, func)
    # Copy the LogRecord from the handler's buffer to the exception
    if hasattr(exception, "log"):
        if isinstance(exception.log, list):
            exception.log.append(record)
        else:
            logger.warning("Cannot attach log to exception %s. "
                           "Potential name clash with attribute 'log'",
                           type(exception).__name__)
    else:
        # Create attributa as a 1-element list.
        exception.log = [record]

attach = attach_log_to_exception

def log_exception(exception, level=None, logger=None):
    """
    Log the given exception at the specified level with the specified logger.

    If a logger is given, its name is not used, however, its handler
    and its level are respected.
    """
    if logger is None:
        logger = logging.getLogger()
    if hasattr(exception, "log"):
        for record in exception.log:
            _log_at_level(record, level, logger)
    if level is None:
        level = logging.CRITICAL

    fn, lno, func = find_caller()
    record = logging.LogRecord(logger.name, logging.CRITICAL, fn, lno,
                               "Exception of type '%s' occurred:",
                               type(exception).__name__, sys.exc_info(), func)
    _log_at_level(record, level, logger)

log = log_exception
###############################################################################
### Public API: Convenience functions for argparsing
###############################################################################

# A sentinel
class _Default:
    pass
_DEFAULT = _Default()

def update_parser(parser, use_shortcuts=True):
    """
    Adds the options 'verbose', 'debug' and 'quiet' to an argparse.ArgumentParser object

    If use_shortcuts is True, '-v', '-q' are added as well.
    """
    if use_shortcuts:
        v = ['-v', '--verbose']
        q = ['-q', '--quiet']
    else:
        v = ['--verbose']
        q = ['--quiet']
    parser.add_argument( *v, action='store_true',
                        help="Show verbose output (Output logged at level logging.INFO)")
    parser.add_argument('--debug', type=str, nargs='?', const=_DEFAULT,
                        help="A comma-seperated list of logger names for which debug output will be activated."
                             "WARNING: If you misspell the logger name, this argument will be ignored")
    parser.add_argument( *q, type=str, nargs='?', const=_DEFAULT,
                        help="A comma-seperated list of logger names for which only messages logged at the level 'CRITICAL' will be shown."
                             "Use this without arguments if everything should be quiet.")
    return parser

def config_from_args(args):
    """
    Handle the --quiet, --verbose and --debug options.
    """
    if hasattr(args, "verbose") and args.verbose:
        logging.getLogger().setLevel(logging.INFO)
    if args.debug is not None:
        if args.debug is _DEFAULT:
            logging.getLogger().setLevel(logging.DEBUG)
        else:
            for logger_name in args.debug.split(","):
                if logger_name == "__root__":
                    logging.getLogger().setLevel(logging.DEBUG)
                logging.getLogger(logger_name).setLevel(logging.DEBUG)
    if args.quiet is not None:
        if args.quiet is _DEFAULT:
            logging.getLogger().setLevel(logging.CRITICAL)
        else:
            for logger_name in args.quiet.split(","):
                if logger_name == "__root__":
                    logging.getLogger().setLevel(logging.CRITICAL)
                logging.getLogger(logger_name).setLevel(logging.CRITICAL)

###############################################################################
### Private utility functions
###############################################################################
def _find_caller():
    """
    See logging.logger.findCaller

    Unfortunately, I saw no way around copy-pasting this
    from logging.Logger.findCaller. However, I did not bother guaranteeing
    compatibility with IronPython and frozen modules.
    """
    f = sys._getframe()
    rv = "(unknown file)", 0, "(unknown function)"
    while hasattr(f, "f_code"):
        co = f.f_code
        filename = os.path.normcase(co.co_filename)
        if filename == os.path.normcase(__file__):
            f = f.f_back
            continue
        rv = (co.co_filename, f.f_lineno, co.co_name)
        break
    return rv

def _log_at_level(record, level=None, logger=None):
    """
    Log a log-record at the given level using the given logger.

    If logger is None, uses the root logger.
    If level is None, use the record's level.
    """
    if logger is None:
        logger = logging.getLogger()
    if level is not None:
        record.levelno = level
        record.levelname = logging.getLevelName(level)

    if record.levelno >= logger.getEffectiveLevel():
        logger.handle(record)

###############################################################################
### Colored log messages, Thanks to airmind @ stackoverflow
### This is not part of the public API and may be replaced by the
### colorlog package in the future
###############################################################################
#Colored log output http://stackoverflow.com/a/384125
#The foreground is set with 30 plus the number of the color
BLACK, RED, GREEN, YELLOW, BLUE, MAGENTA, CYAN, WHITE = range(8)

#These are the sequences need to get colored ouput
RESET_SEQ = "\033[0m"
COLOR_SEQ = "\033[1;%dm"
BOLD_SEQ = "\033[1m"

COLORS_LIGHT = {
    'WARNING': YELLOW,
    'INFO': BLACK,
    'DEBUG': WHITE,
    'CRITICAL': RED,
    'ERROR': RED
}
COLORS_DARK = {
    'WARNING': YELLOW,
    'INFO': WHITE,
    'DEBUG': BLACK,
    'CRITICAL': RED,
    'ERROR': RED
}
class ColoredFormatter(logging.Formatter):
    def __init__(self, colors, msg=None):
        logging.Formatter.__init__(self, msg)
        self.colors = colors
    def format(self, record):
        levelname = record.levelname
        return ( COLOR_SEQ % (30 + self.colors[levelname]) +
                 logging.Formatter.format(self, record) +  RESET_SEQ)

def use_colored_output(dark_bg = False):
    ch = logging.StreamHandler()
    ch.setLevel(logging.DEBUG)
    if dark_bg:
        colors = COLORS_DARK
    else:
        colors = COLORS_LIGHT
    ch.setFormatter(ColoredFormatter(colors, "%(levelname)s:%(name)s.%(funcName)s[%(lineno)d]: %(message)s"))
    logging.getLogger().handlers[0].setFormatter(ch)
