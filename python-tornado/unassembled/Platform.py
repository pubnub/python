import tornado.httpclient

try:
    from hashlib import sha256
    digestmod = sha256
except ImportError:
    import Crypto.Hash.SHA256 as digestmod
    sha256 = digestmod.new

import hmac
import tornado.ioloop
from PubnubCrypto import PubnubCrypto

ioloop = tornado.ioloop.IOLoop.instance()

class Pubnub(PubnubCoreAsync):

    def stop(self): ioloop.stop()
    def start(self): ioloop.start()
    def timeout( self, delay, callback):
        ioloop.add_timeout( time.time()+float(delay), callback )
        
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
        self.headers['User-Agent'] = 'Python-Tornado'
        self.headers['Accept-Encoding'] = self.accept_encoding
        self.headers['V'] = self.version
        self.http = tornado.httpclient.AsyncHTTPClient(max_clients=1000)

    def _request( self, request, callback ) :
        url = self.getUrl(request)
        ## Send Request Expecting JSON Response
        #print self.headers
        request = tornado.httpclient.HTTPRequest( url, 'GET', self.headers, connect_timeout=310, request_timeout=310 ) 
        def responseCallback(response):
            callback(eval(response._get_body()))
        
        self.http.fetch(
            request,
            callback=responseCallback,
        )

