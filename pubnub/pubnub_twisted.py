import json
import logging

from StringIO import StringIO

from twisted.internet import reactor as _reactor
from twisted.internet.defer import Deferred
from twisted.internet import defer
from twisted.internet.protocol import Protocol
from twisted.web.client import Agent, ContentDecoderAgent
from twisted.web.client import RedirectAgent, GzipDecoder
from twisted.web.client import HTTPConnectionPool
from twisted.web.http_headers import Headers
from twisted.internet.ssl import ClientContextFactory
from twisted.web.client import FileBodyProducer

from . import utils
from .errors import PNERR_JSON_DECODING_FAILED, PNERR_SERVER_ERROR, PNERR_CLIENT_ERROR
from .exceptions import PubNubException
from .pubnub_core import PubNubCore


logger = logging.getLogger("pubnub")


class WebClientContextFactory(ClientContextFactory):
    def getContext(self, hostname, port):
        return ClientContextFactory.getContext(self)


# class PubNubResponse(Protocol, TimeoutMixin):
class PubNubResponse(Protocol):
    def __init__(self, finished, code):
        self.finished = finished
        self.code = code

    def dataReceived(self, body):
        self.finished.callback(TwistedResponse(body, self.code))


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

    def async_error_to_return(self, e, errback):
        errback(e)

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
                    func(data)

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

        url = utils.build_url(self.config.scheme(), self.config.origin,
                              options.path, options.params)

        logger.debug("%s %s %s" % (options.method_string, url, options.data))

        def handler():
            # url = self.getUrl(request, encoder_map)

            agent = ContentDecoderAgent(RedirectAgent(Agent(
                rc,
                contextFactory=WebClientContextFactory(),
                pool=pnconn_pool
            )), [('gzip', GzipDecoder)])

            if options.data is not None:
                print(options.data)
                body = FileBodyProducer(StringIO(options.data))
            else:
                body = None

            try:
                request = agent.request(
                    options.method_string,
                    url,
                    Headers(headers),
                    body)
            except TypeError:
                request = agent.request(
                    options.method_string,
                    url.encode(),
                    Headers(headers),
                    body)

            def received(response):
                finished = Deferred()

                response.deliverBody(PubNubResponse(finished, response.code))
                return finished

            def success(response):
                response_body = response.body
                code = response.code
                d = Deferred()

                try:
                    data = json.loads(response_body)
                except ValueError:
                    try:
                        data = json.loads(response_body.decode("utf-8"))
                    except ValueError:
                        d.errback(PubNubException(
                            pn_error=PNERR_JSON_DECODING_FAILED,
                            errormsg='json decode error'
                        ))
                        return

                if code != 200:
                    if code >= 500:
                        err = PNERR_SERVER_ERROR
                    else:
                        err = PNERR_CLIENT_ERROR

                    if data is None:
                        data = "N/A"

                    d.errback(PubNubException(
                        pn_error=err,
                        errormsg=data,
                        status_code=code
                    ))
                else:
                    d.callback(data)

                return d

            request.addCallback(received)
            # request.addErrback(error)
            request.addCallback(success)
            # request.addErrback(error)
            return request

        return handler()


class TwistedResponse(object):
    def __init__(self, body, code):
        self.body = body
        self.code = code
