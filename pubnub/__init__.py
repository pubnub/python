import logging
import os

PUBNUB_ROOT = os.path.dirname(os.path.abspath(__file__))


def set_stream_logger(name='pubnub', level=logging.ERROR, format_string=None, stream=None, filter_warning: str = None):
    if format_string is None:
        format_string = "%(asctime)s %(name)s [%(levelname)s] %(message)s"

    logger = logging.getLogger(name)
    logger.setLevel(level)
    handler = logging.StreamHandler(stream)
    handler.setLevel(level)
    formatter = logging.Formatter(format_string)
    handler.setFormatter(formatter)
    logger.addHandler(handler)

    if filter_warning:
        handler.addFilter(lambda record: filter_warning not in record.msg)
