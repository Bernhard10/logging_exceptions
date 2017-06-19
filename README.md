# Self-logging exceptions

* [Source on GitHub](https://github.com/bernhard10/logging_exceptions)

## Installation


Use setup.py :

```bash
python setup.py install
```

## Comparison to logging.handlers.MemoryHandler

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

```python 
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
```
## Usage

### Self-logging exceptions:

Attach a log message to an exception:

```python
import logging
import logging_exceptions as exlog

e = ValueError("Wrong value")
logger = logging.getLogger(__name__)
with exlog.log_to_exception(logger, e):
  logger.critical("This is a %s log mressage", "long")
raise e # The exception can also be raised inside the with statement
```

If the error is not caught, the log message will be displayed upon program
termination.

Catch the error and display the log message at a costum log-level:

```python
import logging_exceptions as exlog
import logging
try:
  e = ValueError("Wrong value")
  logger = logging.getLogger(__name__)
  with exlog.log_to_exception(logger, e):
    logger.critical("This is a %s log mressage", "long")
    raise e
except ValueError as err:
    exlog.log(err, level=logging.DEBUG)
```

### Commandline convenience functions

The following convenience functions are not directly related to exceptions,
but useful if you use argparse.

Add the '--verbose', '--debug' and '--quiet' options to an
argparse.Argumentparser instance.

```python
import argparse
import logging_exceptions as exlog

parser=argparse.ArgumentParser("Some help text")
exlog.update_parser(parser)
args = parser.parse_args()

logging.basicConfig()
# The following call updates the log levels of the root logger
# and potential some other loggers.
exlog.config_from_args(args)
```

Now the script can be used from the commandline like this:

```bash
python script.py --verbose #Set all loggers to INFO-level
```
```bash

# Set the log-level for the loggers with the names `path.to.module1`
# and `path.to.module2` to DEBUG.
python script.py --debug path.to.module1,path.to.module2
```

## Examples

See the file 'logging_exceptions_examples.py'

## Compatibility

Compatible with python 2.7 and python 3

## License

Copyright (c) 2017 Bernhard C. Thiel <thiel@tbi.univie.ac.at>

Permission is hereby granted, free of charge, to any person obtaining a copy of
this software and associated documentation files (the "Software"), to deal in
the Software without restriction, including without limitation the rights to
use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of
the Software, and to permit persons to whom the Software is furnished to do so,
subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS
FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR
COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER
IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN
CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
