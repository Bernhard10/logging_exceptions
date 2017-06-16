import logging
import logging.handlers
import sys
import os.path

log = logging.getLogger(__name__)


def find_caller():
    """
    Unfortunately, I saw no way around copy-pasting this from logging.Logger.findCaller
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

def attach_log_to_exception(exception, msg, *args):
    """
    Adds a log-record to the exception's 'bl_log' attribute

    Creates the 'bl_log' list, if the attribute does not yet exist.

    msg, args and kwargs are the same as for logging.Logger.debug()
    """

    fn, lno, func = find_caller()
    record = logging.LogRecord(type(exception).__name__, logging.CRITICAL, fn, lno, msg, args, None, func)
    # Copy the LogRecord from the handler's buffer to the exception
    if hasattr(exception, "bl_log"):
        if isinstance(exception.bl_log, list):
            exception.bl_log.append(record)
        else:
            log.warning("Cannot attach log to exception %s. Potential name clash with attribute 'bl_log'", type(exception).__name__)
    else:
        exception.bl_log = [record]

attach = attach_log_to_exception


# The except_hook before we modify it
default_excepthook = sys.excepthook

def logging_excepthook(type, exception, traceback):
    """
    A except_hook that inspects the exception for the 'bl_log' attribute.
    If it finds this attribute, it logs the contained log-records with the
    level ''critical' before calling default_excepthook
    """
    if hasattr(exception, "bl_log"):
        for record in exception.bl_log:
            logging.getLogger().handle(record)
    default_excepthook(type, exception, traceback)

sys.excepthook = logging_excepthook

def log_at_level(record, level=None, logger=None):
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

def log_exception(exception, level=None, logger=None):
    """
    Log the given exception at the specified level with the specified logger.
    """
    if logger is None:
        logger = logging.getLogger()
    if hasattr(exception, "bl_log"):
        for record in exception.bl_log:
            log_at_level(record, level, logger)
    if level is None:
        level = logging.CRITICAL

    fn, lno, func = find_caller()
    record = logging.LogRecord(logger.name, logging.CRITICAL, fn, lno, "Exception of type '%s' occurred:", type(exception).__name__, sys.exc_info(), func)
    log_at_level(record, level, logger)



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
                        help="A comma-seperated list of logger names for which debug output will be activated.")
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
