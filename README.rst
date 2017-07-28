Self-logging exceptions
=======================

* `Source on GitHub <https://github.com/bernhard10/logging_exceptions>`_

Installation
------------


Use setup.py :

.. code-block:: bash

    python setup.py install

Warning
-------

This module modifies `sys.excepthook` when it is imported!

Usage
-----

Self-logging exceptions
~~~~~~~~~~~~~~~~~~~~~~~

Attach a log message to an exception:

.. code-block:: python

    import logging
    import logging_exceptions as exlog

    e = ValueError("Wrong value")
    logger = logging.getLogger(__name__)
    with exlog.log_to_exception(logger, e):
        logger.critical("This is a %s log mressage", "long")
    raise e # The exception can also be raised inside the with statement


If the error is not caught, the log message will be displayed upon program
termination.

Catch the error and display the log message at a costum log-level:

.. code-block:: python

    import logging_exceptions as exlog
    import logging
    try:
        e = ValueError("Wrong value")
        logger = logging.getLogger(__name__)
        with exlog.log_to_exception(logger, e):
            logger.critical("This is a %s log mressage", "long")
            raise e
    except ValueError as err:
        exlog.log(err, level=logging.DEBUG, with_stacktrace=False)

Here, `exlog.log` is a synonym for `exlog.log_exception`

Logging from a different function name and line number
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The code in log_exception calls the `_log` function of a Logger object.
To avoid recording the function name and line number of `log_to_exception`,
`logging_exception` calls `logging.setLoggerClass(ExlogLogger)` to set the
class for all loggers created after import of `logging_exception` to `ExlogLogger`.

`ExlogLogger` is a subclass of `logging.Logger` defined by this module. It
overrides `findCaller` to have more control over the recorded caller.
In addition to ignoring functions defined inside `logging_exceptions`,
`ExlogLogger` classes have the public attribute `ignored_functions`.

By adding function names to `ignored_functions`, it is possible to record
matching function's parents instead of matching functions as the caller.

In particular, the context manager `logging_exceptions.log_at_caller` can be used
in helper functions to temporarily update a logger's `ignored_functions` in order to record a function's caller instead of the function.

The following code will emit a log message with the function name set to 
`foo`, not `helper_function`:

 .. code-block:: python

     import logging_exceptions as exlog
     logger = logging.get_logger(__name__)
     def helper_function():
        with exlog.log_at_caller(logger):
          logger.log("This is a log message")
     def foo():
        helper_function()



Commandline convenience functions
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The following convenience functions are not directly related to exceptions,
but useful if you use argparse.

Add the '--verbose', '--debug' and '--quiet' options to an
argparse.Argumentparser instance.

.. code-block:: python

    import argparse
    import logging_exceptions as exlog

    parser=argparse.ArgumentParser("Some help text")
    exlog.update_parser(parser)
    args = parser.parse_args()

    logging.basicConfig()
    # The following call updates the log levels of the root logger
    # and potential some other loggers.
    exlog.config_from_args(args)

Now the script can be used from the commandline like this:

.. code-block:: bash

    # Set the log-level for the loggers with the names `path.to.module1`
    # and `path.to.module2` to DEBUG.
    python script.py --debug path.to.module1,path.to.module2

Examples
--------

See the file 'logging_exceptions_examples.py'

Comparison to logging.handlers.MemoryHandler
--------------------------------------------

The logging.handlers module contains a handler for a similar purpose: The MemoryHandler.
It buffers log messages and only emits them, if a log record of severity error or above is encountered.
I will quickly explain the differences between MemoryHandler and my module:

MemoryHandler is great if you know that an event of severity ERROR may occur
in the future (typically in the same function) and you want to prepare for
this potential exception. Typically, you know the scope for which the exceptions
have to be buffered and you know when the buffered exceptions are no longer needed and can be discarded.

While for MemoryHandler the error condition is rather unspecific, the scope in
which we have to decide between discarding and emitting the log messages is well
known.

The `log_to_exception` decorator, on the other hand, is useful if the exception
is well specified (it is already created/ caught), but the the scope in which
the exception may or may not be caught is unspecified. Examples would be
library functions that raise an error.

A typical example would be the following:

.. code-block:: python

    import logging
    from logging_exceptions import log_to_exception

    # Whoever calls public_function may want to catch the ValueError and hide
    # the log messages or change their level to logging.DEBUG
    def public_function():
        logger = logging.getLogger(__name__)
        a = some_complex_calculation(12)
        try:
            some_function(a)
        except ValueError as e:
            with log_to_exception(logger, e):
                log.error("While calling `some_function` with %s, "
                          "which is result of `some_complex_calculation`(%d),"
                          " an error occurred", a, 12)
            raise


Compatibility
-------------

Compatible with python 2.7 and python 3
