import json
import logging
import time

from .enums import PNStatusCategory
from .structures import ResponseInfo
from . import utils
from .exceptions import PubNubException
from .errors import PNERR_SERVER_ERROR, PNERR_CLIENT_ERROR, PNERR_JSON_DECODING_FAILED
from .pubnub_core import PubNubCore

import tornado.httpclient
import tornado.ioloop
from tornado.concurrent import Future

default_ioloop = tornado.ioloop.IOLoop.instance()
logger = logging.getLogger("pubnub")


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

    def request_sync(self, *args):
        raise NotImplementedError

    def request_async(self, *args):
        raise NotImplementedError

    def request_deferred(self, *args):
        raise NotImplementedError

    def request_future(self, options_func, create_response, create_status_response):
        options = options_func()
        future = Future()

        url = utils.build_url(self.config.scheme(), self.config.origin,
                              options.path, options.query_string)
        logger.debug("%s %s %s" % (options.method_string, url, options.data))

        request = tornado.httpclient.HTTPRequest(
            url=url,
            method=options.method_string,
            headers=self.headers,
            body=options.data if options.data is not None else None,
            connect_timeout=self.config.connect_timeout,
            request_timeout=self.config.non_subscribe_request_timeout)

        def response_callback(response):
            body = response.body
            response_info = None
            status_category = PNStatusCategory.PNUnknownCategory

            if body is not None and len(body) > 0:
                url = utils.urlparse(response.effective_url)
                query = utils.parse_qs(url.query)
                uuid = None
                auth_key = None

                if 'uuid' in query and len(query['uuid']) > 0:
                    uuid = query['uuid'][0]

                if 'auth_key' in query and len(query['auth_key']) > 0:
                    auth_key = query['auth_key'][0]

                response_info = ResponseInfo(
                    status_code=response.code,
                    tls_enabled='https' == url.scheme,
                    origin=url.hostname,
                    uuid=uuid,
                    auth_key=auth_key,
                    client_request=response.request
                )

                try:
                    data = json.loads(body)
                except TypeError:
                    try:
                        data = json.loads(body.decode("utf-8"))
                    except ValueError:
                        tornado_result = TornadoEnvelope(
                            create_response(None),
                            create_status_response(status_category, response, response_info, PubNubException(
                            pn_error=PNERR_JSON_DECODING_FAILED,
                            errormsg='json decode error')
                                                   )
                        )
                        future.set_exception(tornado_result)
                        return
            else:
                data = "N/A"

            if response.error is not None:
                if response.code >= 500:
                    err = PNERR_SERVER_ERROR
                else:
                    err = PNERR_CLIENT_ERROR

                if response.code == 403:
                    status_category = PNStatusCategory.PNAccessDeniedCategory

                if response.code == 400:
                    status_category = PNStatusCategory.PNBadRequestCategory

                future.set_exception(PubNubException(
                        errormsg=data,
                        pn_error=err,
                        status_code=response.code
                ))

                # future.set_exception(tornado_result)
            else:
                future.set_result(TornadoEnvelope(
                    result=create_response(data),
                    status=create_status_response(status_category, data, response_info, None)
                    )
                )

        self.http.fetch(
            request=request,
            callback=response_callback
        )

        return future


class TornadoEnvelope(object):
    def __init__(self, result, status):
        self.result = result
        self.status = status
