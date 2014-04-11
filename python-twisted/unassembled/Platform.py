from twisted.web.client import getPage
from twisted.internet import reactor
from twisted.internet.defer import Deferred
from twisted.internet.protocol import Protocol
from twisted.web.client import Agent, ContentDecoderAgent, RedirectAgent, GzipDecoder
from twisted.web.client import HTTPConnectionPool
from twisted.web.http_headers import Headers
from twisted.internet.ssl import ClientContextFactory
from twisted.internet.task import LoopingCall
import twisted
from hashlib import sha256
import time

pnconn_pool = HTTPConnectionPool(reactor, persistent=True)
pnconn_pool.maxPersistentPerHost    = 100000
pnconn_pool.cachedConnectionTimeout = 310
pnconn_pool.retryAutomatically = True

class Pubnub(PubnubCoreAsync):

    def start(self): reactor.run()
    def stop(self):  reactor.stop()
    def timeout( self, delay, callback ):
        reactor.callLater( delay, callback )

    def __init__(
        self,
        publish_key,
        subscribe_key,
        secret_key = False,
        cipher_key = False,
        ssl_on = False,
        origin = 'pubsub.pubnub.com'
    ) :
        super(Pubnub, self).__init__(
            publish_key=publish_key,
            subscribe_key=subscribe_key,
            secret_key=secret_key,
            cipher_key=cipher_key,
            ssl_on=ssl_on,
            origin=origin,
        )        
        self.headers = {}
        self.headers['User-Agent'] = ['Python-Twisted']
        #self.headers['Accept-Encoding'] = [self.accept_encoding]
        self.headers['V'] = [self.version]
        self._channel_list_lock = None

    def _request( self, request, callback, single=False ) :
        global pnconn_pool

        ## Build URL
        '''
        url = self.origin + '/' + "/".join([
            "".join([ ' ~`!@#$%^&*()+=[]\\{}|;\':",./<>?'.find(ch) > -1 and
                hex(ord(ch)).replace( '0x', '%' ).upper() or
                ch for ch in list(bit)
            ]) for bit in request])
        '''
        url = self.getUrl(request)

        agent       = ContentDecoderAgent(RedirectAgent(Agent(
            reactor,
            contextFactory = WebClientContextFactory(),
            pool = self.ssl and None or pnconn_pool
        )), [('gzip', GzipDecoder)])

        request     = agent.request( 'GET', url, Headers(self.headers), None )

        if single is True:
            id = time.time()
            self.id = id

        def received(response):
            finished = Deferred()
            response.deliverBody(PubNubResponse(finished))
            return finished

        def complete(data):
            if single is True:
                if not id == self.id:
                    return None
            try:
                callback(eval(data))
            except Exception as e:
                pass
                #need error handling here

        def abort():
            pass

        request.addCallback(received)
        request.addBoth(complete)

        return abort

class WebClientContextFactory(ClientContextFactory):
    def getContext(self, hostname, port):
        return ClientContextFactory.getContext(self)
	   
class PubNubResponse(Protocol):
    def __init__( self, finished ):
        self.finished = finished

    def dataReceived( self, bytes ):
            self.finished.callback(bytes)

