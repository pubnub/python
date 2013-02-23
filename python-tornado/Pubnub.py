## www.pubnub.com - PubNub Real-time push service in the cloud. 
# coding=utf8

## PubNub Real-time Push APIs and Notifications Framework
## Copyright (c) 2010 Stephen Blum
## http://www.pubnub.com/

## -----------------------------------
## PubNub 3.1 Real-time Push Cloud API
## -----------------------------------
import sys
sys.path.append('../')
from PubnubCoreAsync import PubnubCoreAsync
import json
import time
import hashlib
import urllib2
import tornado.httpclient
import sys
import uuid

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
            publish_key,
            subscribe_key,
            secret_key,
            ssl_on,
            origin,
        )        

    def _request( self, request, callback ) :
        ## Build URL
        url = self.origin + '/' + "/".join([
            "".join([ ' ~`!@#$%^&*()+=[]\\{}|;\':",./<>?'.find(ch) > -1 and
                hex(ord(ch)).replace( '0x', '%' ).upper() or
                ch for ch in list(bit)
            ]) for bit in request])
        print url
        ## Send Request Expecting JSON Response
        http = tornado.httpclient.AsyncHTTPClient(max_clients=1000)
        request = tornado.httpclient.HTTPRequest( url, 'GET', dict({
            'V' : '3.1',
            'User-Agent' : 'Python-Tornado',
            'Accept-Encoding' : 'gzip'
        }) ) 
        def responseCallback(response):
            print response._get_body()
            callback(response._get_body())
        
        http.fetch(
            request,
            callback=responseCallback,
            connect_timeout=310,
            request_timeout=310
        )

