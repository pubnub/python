## www.pubnub.com - PubNub Real-time push service in the cloud. 
# coding=utf8

## PubNub Real-time Push APIs and Notifications Framework
## Copyright (c) 2010 Stephen Blum
## http://www.pubnub.com/

## -----------------------------------
## PubNub 3.1 Real-time Push Cloud API
## -----------------------------------
import sys
import json
import time
import hashlib
import urllib2
import uuid
from PubnubCoreAsync import PubnubCoreAsync
try:
    from hashlib import sha256
    digestmod = sha256
except ImportError:
    import Crypto.Hash.SHA256 as digestmod
    sha256 = digestmod.new
import hmac
from twisted.web.client import getPage
from twisted.internet import reactor
from twisted.internet.defer import Deferred
from twisted.internet.protocol import Protocol
from twisted.web.client import Agent, ContentDecoderAgent, RedirectAgent, GzipDecoder
from twisted.web.client import HTTPConnectionPool
from twisted.web.http_headers import Headers
from PubnubCrypto import PubnubCrypto
from twisted.internet.ssl import ClientContextFactory

pnconn_pool = HTTPConnectionPool(reactor, persistent=True)
pnconn_pool.maxPersistentPerHost    = 100
pnconn_pool.cachedConnectionTimeout = 310

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
            ssl_on=ssl_on,
            origin=origin,
        )        
        self.headers = {}
        self.headers['User-Agent'] = ['Python-Twisted']
        #self.headers['Accept-Encoding'] = [self.accept_encoding]
        self.headers['V'] = [self.version]

    def _request( self, request, callback ) :
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
        print url
        request     = agent.request( 'GET', url, Headers(self.headers), None )

        def received(response):
            #print response
            finished = Deferred()
            response.deliverBody(PubNubResponse(finished))
            return finished

        def complete(data):
            callback(data)

        request.addCallback(received)
        request.addBoth(complete)

class WebClientContextFactory(ClientContextFactory):
    def getContext(self, hostname, port):
        return ClientContextFactory.getContext(self)
	   
class PubNubResponse(Protocol):
    def __init__( self, finished ):
        self.finished = finished

    def dataReceived( self, bytes ):
            self.finished.callback(bytes)

