from twisted.web.client import getPage
from twisted.internet import reactor
from twisted.internet.defer import Deferred
from twisted.internet.protocol import Protocol
from twisted.web.client import Agent, ContentDecoderAgent
from twisted.web.client import RedirectAgent, GzipDecoder
from twisted.web.client import HTTPConnectionPool
from twisted.web.http_headers import Headers
from twisted.internet.ssl import ClientContextFactory
from twisted.internet.task import LoopingCall
import twisted
from hashlib import sha256
import time
import json

import traceback


from twisted.python.compat import (
    _PY3, unicode, intToBytes, networkString, nativeString)

pnconn_pool = HTTPConnectionPool(reactor, persistent=True)
pnconn_pool.maxPersistentPerHost = 100000
pnconn_pool.cachedConnectionTimeout = 15
pnconn_pool.retryAutomatically = True

class Pubnub(PubnubCoreAsync):

    def start(self):
        reactor.run()

    def stop(self):
        reactor.stop()

    def timeout(self, delay, callback):
        reactor.callLater(delay, callback)

    def __init__(
        self,
        publish_key,
        subscribe_key,
        secret_key=False,
        cipher_key=False,
        auth_key=None,
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
        self.headers['User-Agent'] = ['Python-Twisted']
        #self.headers['Accept-Encoding'] = [self.accept_encoding]
        self.headers['V'] = [self.version]

    def _request(self, request, callback=None, error=None, single=False):
        global pnconn_pool

        def _invoke(func, data):
            if func is not None:
                func(data)

        ## Build URL

        url = self.getUrl(request)

        agent = ContentDecoderAgent(RedirectAgent(Agent(
            reactor,
            contextFactory=WebClientContextFactory(),
            pool=self.ssl and None or pnconn_pool
        )), [('gzip', GzipDecoder)])

        try:
            request = agent.request(
                'GET', url, Headers(self.headers), None)
        except TypeError as te:
            request = agent.request(
                'GET', url.encode(), Headers(self.headers), None)

        if single is True:
            id = time.time()
            self.id = id

        def received(response):
            if not isinstance(response, twisted.web._newclient.Response):
                _invoke(error, {"message" : "Not Found"})
                return

            finished = Deferred()
            if response.code in [401,403]:
                response.deliverBody(PubNubPamResponse(finished))
            else:
                response.deliverBody(PubNubResponse(finished))

            return finished

        def complete(data):
            if single is True:
                if id != self.id:
                    return None
            try:
                data = json.loads(data)
            except ValueError as e:
                try:
                    data = json.loads(data.decode("utf-8"))
                except ValueError as e:
                    _invoke(error, {'error': 'json decode error'})

            if 'error' in data and 'status' in data and 'status' != 200:
                _invoke(error, data)
            else:
                _invoke(callback, data)

        def abort():
            pass

        request.addCallback(received)
        request.addCallback(complete)

        return abort


class WebClientContextFactory(ClientContextFactory):
    def getContext(self, hostname, port):
        return ClientContextFactory.getContext(self)


class PubNubPamResponse(Protocol):
    def __init__(self, finished):
        self.finished = finished

    def dataReceived(self, bytes):
        self.finished.callback(bytes)


class PubNubResponse(Protocol):
    def __init__(self, finished):
        self.finished = finished

    def dataReceived(self, bytes):
        self.finished.callback(bytes)
