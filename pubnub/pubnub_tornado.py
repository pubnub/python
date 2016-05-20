import json
import time
import urllib
import urlparse

from .exceptions import PubNubException
from .errors import PNERR_SERVER_ERROR, PNERR_CLIENT_ERROR, PNERR_JSON_DECODING_FAILED
from .pubnub_core import PubNubCore

import tornado.httpclient
import tornado.ioloop
from tornado.concurrent import Future

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

    def sdk_platform(self):
        return "-Tornado"

    def __init__(self, config):
        super(PubNubTornado, self).__init__(config)
        self._ioloop = default_ioloop

        self.http = tornado.httpclient.AsyncHTTPClient(max_clients=1000)
        self.id = None
        # TODO: add accept encoding should be configurable
        self.headers = {
            'User-Agent': self.sdk_name,
            'Accept-Encoding': 'utf-8'
        }

    def request_async(self, options, success, error):
        def _invoke(func, data):
            if func is not None:
                func(data)

        url = urlparse.urlunsplit((self.config.scheme(), self.config.origin,
                                   options.path, urllib.urlencode(options.params), ''))
        # TODO: encode url
        # url = self.getUrl(url, encoder_map)

        request = tornado.httpclient.HTTPRequest(
            url=url,
            method=options.method_string,
            headers=self.headers,
            body=options.data if options.data is not None else None,
            connect_timeout=self.config.connect_timeout,
            request_timeout=self.config.non_subscribe_request_timeout)

        def response_callback(response):
            body = response.body

            if body is not None and len(body) > 0:
                try:
                    data = json.loads(body)
                except TypeError:
                    try:
                        data = json.loads(body.decode("utf-8"))
                    except ValueError:
                        _invoke(error, PubNubException(
                            pn_error=PNERR_JSON_DECODING_FAILED,
                            errormsg='json decode error'
                        ))
                        return
            else:
                data = "N/A"

            if response.error is not None:
                if response.code >= 500:
                    err = PNERR_SERVER_ERROR
                else:
                    err = PNERR_CLIENT_ERROR

                _invoke(error, PubNubException(
                    errormsg=data,
                    pn_error=err,
                    status_code=response.code
                ))
            else:
                _invoke(success, data)

        self.http.fetch(
            request=request,
            callback=response_callback
        )

    # TODO: add Tornado Feature support
    def request_deferred(self, options_func):
        options = options_func()
        future = Future()
        self.request_async(
            options,
            lambda res: future.set_result(res),
            lambda err: future.set_exception(err)
        )
        return future
