import json
import time

from pubnub.utils import get_data_for_user
from .pubnub_core import PubNubCore

import tornado.httpclient
import tornado.ioloop
from tornado.stack_context import ExceptionStackContext

default_ioloop = tornado.ioloop.IOLoop.instance()


class PubNubTornado(PubNubCore):
    def stop(self):
        self._ioloop.stop()

    def start(self):
        self._ioloop.start()

    def timeout(self, delay, callback, *args):
        handle = None

        def cancel():
            self._ioloop.remove_timeout(handle)

        def cb():
            if callback is not None:
                callback(*args)

        handle = self._ioloop.add_timeout(time.time() + float(delay), cb)

        return cancel

    def set_ioloop(self, ioloop):
        self._ioloop = ioloop

    def __init__(self, config):
        super(PubNubTornado, self).__init__(config)
        self._ioloop = default_ioloop

        # self.headers = {'User-Agent': 'Python-Tornado', 'Accept-Encoding': self.accept_encoding, 'V': self.version}
        # TODO: add accept encoding
        self.headers = {'User-Agent': 'Python-Tornado', 'V': self.version}
        self.http = tornado.httpclient.AsyncHTTPClient(max_clients=1000)
        self.id = None
        self.pnsdk = 'PubNub-Python-' + 'Tornado' + '/' + self.version

    def request_async(self, path, query, success, error):
        print("async req")
        url = self.config.scheme_and_host() + path
        self._request(
            url=url,
            callback=success,
            error=error,
            # TODO: set correct timeout
            timeout=15,
            connect_timeout=5,
        )

    def _request(self, url, callback=None, error=None,
                 single=False, timeout=15, connect_timeout=5, encoder_map=None):

        def _invoke(func, data):
            if func is not None:
                func(get_data_for_user(data))

        # TODO: encode url
        # url = self.getUrl(url, encoder_map)

        request = tornado.httpclient.HTTPRequest(
            url, 'GET',
            self.headers,
            connect_timeout=connect_timeout,
            request_timeout=timeout)

        if single is True:
            id = time.time()
            self.id = id

        def responseCallback(response):
            if single is True:
                if not id == self.id:
                    return None

            body = response._get_body()

            if body is None:
                # TODO: handle exception
                return

            def handle_exc(*args):
                return True

            if response.error is not None:
                with ExceptionStackContext(handle_exc):
                    if response.code in [403, 401]:
                        response.rethrow()
                    else:
                        _invoke(error, response.reason)
                    return

            try:
                data = json.loads(body)
            except TypeError:
                try:
                    data = json.loads(body.decode("utf-8"))
                except ValueError:
                    _invoke(error, 'json decode error')
                    return

            if 'error' in data and 'status' in data and 'status' != 200:
                _invoke(error, data)
            else:
                _invoke(callback, data)

        self.http.fetch(
            request=request,
            callback=responseCallback
        )
