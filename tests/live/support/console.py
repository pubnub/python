"""quiet_logging(): silence the SDK loggers for a block. Tests that check log output use the caplog fixture instead.
DEBUG logs of the SDK print request URLs, so nothing the tier prints may come from a DEBUG pubnub logger unredacted."""
import contextlib
import logging


@contextlib.contextmanager
def quiet_logging(name='pubnub', level=logging.CRITICAL):
    logger = logging.getLogger(name)
    before = logger.level
    logger.setLevel(level)
    try:
        yield logger
    finally:
        logger.setLevel(before)
