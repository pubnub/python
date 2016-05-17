import json
import logging
import urllib
import urlparse

from twisted.internet import reactor as _reactor
from twisted.internet.defer import Deferred
from twisted.internet import defer
from twisted.internet.protocol import Protocol
from twisted.web.client import Agent, ContentDecoderAgent
from twisted.web.client import RedirectAgent, GzipDecoder
from twisted.web.client import HTTPConnectionPool
from twisted.web.http_headers import Headers
from twisted.internet.ssl import ClientContextFactory

from .enums import HttpMethod
from .exceptions import PubNubException
from .utils import get_data_for_user
from .pubnub_core import PubNubCore


logger = logging.getLogger("pubnub")


class WebClientContextFactory(ClientContextFactory):
    def getContext(self, hostname, port):
        return ClientContextFactory.getContext(self)


class PubNubResponse(Protocol):
    def __init__(self, finished):
        self.finished = finished

    def dataReceived(self, bytes):
        self.finished.callback(bytes)


class PubNubTwisted(PubNubCore):
    """PubNub Python API for Twisted framework"""

    def sdk_platform(self):
        return "-Twisted"

    def __init__(self, config, pool=None, reactor=None):
        super(PubNubTwisted, self).__init__(config)

        if reactor is None:
            self.reactor = _reactor
        else:
            self.reactor = reactor

        if pool is None:
            self.pnconn_pool = HTTPConnectionPool(self.reactor, persistent=True)
            self.pnconn_pool.maxPersistentPerHost = 100000
            self.pnconn_pool.cachedConnectionTimeout = 15
            self.pnconn_pool.retryAutomatically = True
        else:
            self.pnconn_pool = pool

        self.headers = {
            'User-Agent': [self.sdk_name],
        }

    def start(self):
        self.reactor.run()

    def stop(self):
        self.reactor.stop()

    def timeout(self, delay, callback, *args):
        def cb():
            if callback is not None:
                callback(*args)

        timeout = self.reactor.callLater(delay, cb)

        def cancel():
            if timeout.active():
                timeout.cancel()

        return cancel

    def request_async(self, options, success, error):
        """
        Request in non-common for Twisted way - using callbacks
        WARNING: currently is buggy

        :param error:
        :param success:
        :param options:
        :return: async handler
        """
        def handler():
            def _invoke(func, data):
                if func is not None:
                    func(get_data_for_user(data))

            def s(data):
                _invoke(success, data)

            def e(err):
                _invoke(error, err)

            self.request_deferred(options).addCallbacks(s, e)

        return handler()

    def request_deferred(self, options_func):
        # TODO: handle timeout and encoder_map
        # TODO: unify error objects
        rc = self.reactor
        pnconn_pool = self.pnconn_pool
        headers = self.headers
        try:
            options = options_func()
        except PubNubException as e:
            return defer.fail(e)

        url = urlparse.urlunsplit((self.config.scheme(), self.config.origin,
                                   options.path, urllib.urlencode(options.params), ''))

        logger.debug("%s %s" % (HttpMethod.string(options.method), url))

        def handler():
            # url = self.getUrl(request, encoder_map)

            agent = ContentDecoderAgent(RedirectAgent(Agent(
                rc,
                contextFactory=WebClientContextFactory(),
                pool=pnconn_pool
            )), [('gzip', GzipDecoder)])

            try:
                request = agent.request(
                    'GET', url, Headers(headers), None)
            except TypeError:
                request = agent.request(
                    'GET', url.encode(), Headers(headers), None)

            def received(response):
                finished = Deferred()
                response.deliverBody(PubNubResponse(finished))
                return finished

            def complete(data):
                d = Deferred()

                try:
                    data = json.loads(data)
                except ValueError:
                    try:
                        data = json.loads(data.decode("utf-8"))
                    except ValueError:
                        d.errback('json decode error')
                        return

                if 'error' in data and 'status' in data and 'status' != 200:
                    d.errback(data)
                else:
                    d.callback(data)

                return d

            def errback(msg):
                print("TODO: handle errback")
                # TODO: handle this case
                d = Deferred()
                d.errback(msg)
                return d

            request.addCallbacks(received, errback)
            request.addCallbacks(complete, errback)
            return request

        return handler()
