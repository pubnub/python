import logging
import threading

from .errors import PNERR_DEFERRED_NOT_IMPLEMENTED
from .exceptions import PubNubException

from .pubnub_core import PubNubCore, pn_request

logger = logging.getLogger("pubnub")


class PubNub(PubNubCore):
    """PubNub Python API"""

    def __init__(self, config):
        PubNubCore.__init__(self, config)

    def sdk_platform(self):
        return ""

    def request_async(self, options, success, error):
        client = AsyncHTTPClient(self, options, success, error)

        thread = threading.Thread(target=client.run)
        thread.start()

        return thread

    def request_deferred(self, options_func):
        raise PubNubException(pn_error=PNERR_DEFERRED_NOT_IMPLEMENTED)


class AsyncHTTPClient:
    """A wrapper for threaded calls"""

    def __init__(self, pubnub, options, callback=None, error=None, id=None):
        # TODO: introduce timeouts
        self.options = options
        self.id = id
        self.success = callback
        self.error = error
        self.pubnub = pubnub

    def cancel(self):
        self.success = None
        self.error = None

    def run(self):
        try:
            res = pn_request(self.pubnub.session, self.pubnub.config.scheme_and_host(), self.pubnub.headers,
                             self.options, self.pubnub.config.connect_timeout,
                             self.pubnub.config.non_subscribe_request_timeout)
            self.success(res)
        except PubNubException as e:
            self.error(e)
