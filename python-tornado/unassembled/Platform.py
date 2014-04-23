import tornado.httpclient

try:
    from hashlib import sha256
    digestmod = sha256
except ImportError:
    import Crypto.Hash.SHA256 as digestmod
    sha256 = digestmod.new

import hmac
import tornado.ioloop
from tornado.stack_context import ExceptionStackContext

ioloop = tornado.ioloop.IOLoop.instance()


class Pubnub(PubnubCoreAsync):

    def stop(self):
        ioloop.stop()

    def start(self):
        ioloop.start()

    def timeout(self, delay, callback):
        ioloop.add_timeout(time.time() + float(delay), callback)

    def __init__(
        self,
        publish_key,
        subscribe_key,
        secret_key=False,
        cipher_key=False,
        auth_key=False,
        ssl_on=False,
        origin='pubsub.pubnub.com'
    ):
        super(Pubnub, self).__init__(
            publish_key=publish_key,
            subscribe_key=subscribe_key,
            secret_key=secret_key,
            cipher_key=cipher_key,
            auth_key=auth_key,
            ssl_on=ssl_on,
            origin=origin,
        )
        self.headers = {}
        self.headers['User-Agent'] = 'Python-Tornado'
        self.headers['Accept-Encoding'] = self.accept_encoding
        self.headers['V'] = self.version
        self.http = tornado.httpclient.AsyncHTTPClient(max_clients=1000)
        self.id = None

    def _request(self, request, callback=None, error=None,
                 single=False, read_timeout=5, connect_timeout=5):

        def _invoke(func, data):
            if func is not None:
                func(data)

        url = self.getUrl(request)
        request = tornado.httpclient.HTTPRequest(
            url, 'GET',
            self.headers,
            connect_timeout=connect_timeout,
            request_timeout=read_timeout)
        if single is True:
            id = time.time()
            self.id = id

        def responseCallback(response):
            if single is True:
                if not id == self.id:
                    return None

            body = response._get_body()

            if body is None:
                return

            def handle_exc(*args):
                return True
            if response.error is not None:
                with ExceptionStackContext(handle_exc):
                    if response.code in [403, 401]:
                        response.rethrow()
                    else:
                        _invoke(error, {"message": response.reason})
                    return

            try:
                data = json.loads(body)
            except TypeError as e:
                try:
                    data = json.loads(body.decode("utf-8"))
                except ValueError as ve:
                    _invoke(error, {'error': 'json decode error'})

            if 'error' in data and 'status' in data and 'status' != 200:
                _invoke(error, data)
            else:
                _invoke(callback, data)

        self.http.fetch(
            request=request,
            callback=responseCallback
        )

        def abort():
            pass

        return abort
