import logging
import logging.handlers
import sys
import os.path
import contextlib
import copy

###########################################################


__all__ = ['log_to_exception', 'log_exception',
           'update_parser', 'config_from_args',
           'log_at_caller']

##############################################################################
# A costum sys.excepthook that displays all log messages
# associated with an unhandled exception.
###############################################################################

# The except_hook before we modify it
default_excepthook = sys.excepthook


def _log_in_exhook(exception):
    if hasattr(exception, "log"):
        for record in exception.log:
            logging.getLogger(record.name).handle(record)

def logging_excepthook(type, exception, traceback):
    """
    A except_hook that inspects the exception for the 'log' attribute.
    If it finds this attribute, it logs the contained log-records with the
    level ''critical' before calling default_excepthook
    """
    _log_in_exhook(exception)
    default_excepthook(type, exception, traceback)

def ipython_handler(self, etype, value, tb, tb_offset=None):
    _log_in_exhook(value)
    self.showtraceback((etype, value, tb), tb_offset=tb_offset)
    return None

try:
    ipy = get_ipython()
except NameError as e:
    sys.excepthook = logging_excepthook
else:
    ipy.set_custom_exc((Exception,), ipython_handler)

##############################################################################
# A costum Logger subclass that does not record functions and filename
# of this file, but instead the caller's filename and function name.
###############################################################################

# See the comment for logging._srcfile for an explaination why we don't use __file__
# as the second string.
# This variable takes the role of logging._srcfile
ignored_filenames = [ logging._srcfile, os.path.normcase(logging_excepthook.__code__.co_filename)]


class ExlogLogger(logging.Logger):
    def __init__(self, name, level=logging.NOTSET):
        super(ExlogLogger, self).__init__(name, level)
        self.ignored_functions = []

    def findCaller(self, stack_info=False):
        """
        Modified copy of the original logging.Logger.findCaller function.

        Instead of only ignoring the logging Module when searching for
        the function with the logging call, this also ignores logging_exceptions.

        This is implemented by replacing
        """
        f = logging.currentframe()
        #On some versions of IronPython, currentframe() returns None if
        #IronPython isn't run with -X:Frames.
        if f is not None:
            f = f.f_back
        rv = "(unknown file)", 0, "(unknown function)", None
        while hasattr(f, "f_code"):
            co = f.f_code
            filename = os.path.normcase(co.co_filename)
            if filename in ignored_filenames or co.co_name in self.ignored_functions:
                f = f.f_back
                continue
            sinfo = None
            if stack_info:
                sio = io.StringIO()
                sio.write('Stack (most recent call last):\n')
                traceback.print_stack(f, file=sio)
                sinfo = sio.getvalue()
                if sinfo[-1] == '\n':
                    sinfo = sinfo[:-1]
                sio.close()
            rv = (co.co_filename, f.f_lineno, co.co_name, sinfo)
            break
        if sys.version_info.major<3:
            return rv[:3]
        return rv


logging.setLoggerClass(ExlogLogger)

@contextlib.contextmanager
def log_at_caller(logger):
    """
    A context manager for using the parent function as the
    function name attached to the log record

    :param logger: An instance of ExlogLogger. By importing logging_exceptions,
                   the logger class is automatically set to ExlogLogger for all
                   loggers created after logging_exceptions was imported.

    .. warning::

        If logger is not an instance of ExlogLogger (in particular if it is the root logger),
        this context manager will do nothing

    New in Version 0.1.6
    """
    # store the original ignored_functions
    try:
        orig_ignored_f = logger.ignored_functions
    except AttributeError: #The logger is not a ExlogLogger. Do nothing
        orig_ignored_f = None
    else:
        # Make a copy of ignored_functions and add the caller of this contect manager
        logger.ignored_functions = copy.copy(logger.ignored_functions)
        f = logging.currentframe()
        logger.ignored_functions.append(f.f_code.co_name)
    try:
        yield
    finally:
        if orig_ignored_f is not None:
            logger.ignored_functions = orig_ignored_f


###############################################################################
# Public API for attaching log messages to exceptions and
# for displaying logs associated with caught exceptions.
###############################################################################


@contextlib.contextmanager
def log_to_exception(logger, exception):
    # __enter__:
    # store the original logger configuration
    propagate = logger.propagate
    original_handlers = logger.handlers
    # Assign a new handler
    logger.handlers = [logging.handlers.BufferingHandler(1000)]
    logger.propagate = False
    try:
        yield
    finally:
        # __exit__:
        # Attach the log records to the exception
        if hasattr(exception, "log"):
            try:
                exception.log.extend(logger.handlers[0].buffer)
            except AttributeError:
                # No attribute extend. Issue a warning and discard buffered
                log = logging.getLogger(__name__)
                warnings.warn("Cannot attach log to exception {}. "
                              "Potential name clash with attribute "
                              "'log'".format(type(exception).__name__))
        else:
            exception.log = logger.handlers[0].buffer
        # Restore original logger configutration
        logger.propagate = propagate
        logger.handlers = original_handlers


def log_exception(exception, level=None, logger=None, with_stacktrace=True):
    """
    Log the given exception at the specified level with the specified logger.

    If a logger is given, its name is not used, however, its handler
    and its level are respected.

    :param with_stacktrace: Whether or not to show the stack_trace. New in version 0.1.5
    """
    if hasattr(exception, "log"):
        for record in exception.log:
            _log_at_level(record, level, logger)
        if exception.log and logger is None:
            logger = logging.getLogger(exception.log[-1].name)
    if level is None:
        level = logging.CRITICAL

    if logger is None:
        logger = logging.getLogger()
    if level is None:
        level = logging.CRITICAL
    msg = "Exception of type '%s' occurred:"
    if not with_stacktrace:
        msg += " "+str(exception)
    logger.log(level, msg,
               type(exception).__name__, exc_info=with_stacktrace)


log = log_exception

###############################################################################
# Public API: Convenience functions for argparsing
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
    parser.add_argument(*v, action='store_true',
                        help="Show verbose output (Output logged at level logging.INFO)")
    parser.add_argument('--debug', type=str, nargs='?', const=_DEFAULT,
                        help="A comma-seperated list of logger names for which debug output will be activated."
                             "WARNING: If you misspell the logger name, this argument will be ignored")
    parser.add_argument(*q, type=str, nargs='?', const=_DEFAULT,
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
# Private utility functions
###############################################################################


def _log_at_level(record, level=None, logger=None):
    """
    Log a log-record at the given level using the given logger.

    If logger is None, uses the root logger.
    If level is None, use the record's level.
    """
    if logger is None:
        logger = logging.getLogger(record.name)
    if level is not None:
        record.levelno = level
        record.levelname = logging.getLevelName(level)

    if record.levelno >= logger.getEffectiveLevel():
        # We use callHandlers instead of handle, because we already applied
        # the filters when the log record was created.
        logger.callHandlers(record)


###############################################################################
# Colored log messages, Thanks to airmind @ stackoverflow
# This is not part of the public API and may be replaced by the
# colorlog package in the future
###############################################################################
# Colored log output http://stackoverflow.com/a/384125
# The foreground is set with 30 plus the number of the color
BLACK, RED, GREEN, YELLOW, BLUE, MAGENTA, CYAN, WHITE = range(8)

# These are the sequences need to get colored ouput
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
        return (COLOR_SEQ % (30 + self.colors[levelname]) +
                logging.Formatter.format(self, record) + RESET_SEQ)


def use_colored_output(dark_bg=False):
    ch = logging.StreamHandler()
    ch.setLevel(logging.DEBUG)
    if dark_bg:
        colors = COLORS_DARK
    else:
        colors = COLORS_LIGHT
    cf = ColoredFormatter(
            colors, "%(levelname)s:%(name)s.%(funcName)s[%(lineno)d]: %(message)s")
    try:
        logging.getLogger().handlers[0].setFormatter(ch)
    except IndexError:
        ch.setFormatter(cf)
        logging.getLogger().addHandler(ch)
