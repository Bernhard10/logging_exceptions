import logging
import argparse
import logging_exceptions

parser = argparse.ArgumentParser()
update_parser(parser)


def foo():
    log = logging.getLogger("main.foo")
    log.info("Logging is enabled for logger 2.")
    for level in [logging.DEBUG, logging.INFO, logging.WARNING, logging.ERROR, logging.CRITICAL]:
        log.log(level, "Logging at level %s.", level)

def raise_error(value):
    try:
        raise ValueError("Test value Error")
    except ValueError as e:
        logging_exceptions.attach(e, "raise_error called with value %s", value)
        raise



if __name__ == "__main__":
    args = parser.parse_args()
    logging.basicConfig()
    logging_exceptions.use_colored_output(True)
    logging_exceptions.config_from_args(args)
    log = logging.getLogger("main1")
    log.info("Logging is enabled for logger 1.")

    for level in [logging.DEBUG, logging.INFO, logging.WARNING, logging.ERROR, logging.CRITICAL]:
        log.log(level, "Logging at level %s.", level)

    foo()

    try:
        raise_error(24)
    except Exception as e:
        logging_exceptions.log_exception(e, logging.INFO)

    try:
        raise_error(124)
    except Exception as e:
        logging_exceptions.log_exception(e, logger=log)

    try:
        raise_error(42)
    except Exception as e:
        logging_exceptions.log_exception(e, logging.WARNING, logger=logging.getLogger("main.exception"))

    log.info("Almost there")
    raise_error(-1)
