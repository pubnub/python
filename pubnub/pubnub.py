import json
import threading

from .exceptions import PubNubException

from .pubnub_core import PubNubCore


class PubNub(PubNubCore):
    """PubNub Python API"""

    def __init__(self, config):
        PubNubCore.__init__(self, config)

    def request_async(self, path, query, success, error):
        url = self.config.scheme_and_host() + path

        client = AsyncHTTPClient(self, url=url,callback=success, error=error)

        thread = threading.Thread(target=client.run)
        thread.start()

        return thread


class AsyncHTTPClient:
    """A wrapper for threaded calls"""

    def __init__(self, pubnub, url,callback=None, error=None, id=None):
        # TODO: introduce timeouts
        self.url = url
        self.id = id
        self.success = callback
        self.error = error
        self.pubnub = pubnub

    def cancel(self):
        self.success = None
        self.error = None

    def run(self):
        def _invoke(func, data):
            if func is not None:
                func(get_data_for_user(data))

        resp = self.pubnub.session.get(self.url)
        if resp.status_code == 200:
            _invoke(self.success, resp)
        else:
            _invoke(self.error, resp)


def get_data_for_user(data):
    try:
        if 'message' in data and 'payload' in data:
            return {'message': data['message'], 'payload': data['payload']}
        else:
            return data
    except TypeError:
        return data
