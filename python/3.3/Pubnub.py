## www.pubnub.com - PubNub Real-time push service in the cloud. 
# coding=utf8

## PubNub Real-time Push APIs and Notifications Framework
## Copyright (c) 2010 Stephen Blum
## http://www.pubnub.com/

## -----------------------------------
## PubNub 3.0 Real-time Push Cloud API
## -----------------------------------

try: import json
except ImportError: import simplejson as json
import sys
sys.path.append('../..')
import time
import hashlib
import urllib2
import uuid
from PubnubCore import PubnubCore

class Pubnub(PubnubCore):
    def __init__(
        self,
        publish_key,
        subscribe_key,
        secret_key = False,
        ssl_on = False,
        origin = 'pubsub.pubnub.com',
        pres_uuid = None
    ) :
        super(Pubnub, self).__init__(
            publish_key,
            subscribe_key,
            secret_key,
            ssl_on,
            origin,
            pres_uuid
        )        

    def _request( self, request, origin = None, encode = True, params = None, callback = None ) :
        ## Build URL
        url = (origin or self.origin) + '/' + "/".join(
            encode and self._encode(request) or request
        )
        ## Add query params
        if params is not None and len(params) > 0:
            url = url + "?" + "&".join(params)

        ## Send Request Expecting JSONP Response
        try:
            try: usock = urllib2.urlopen( url, None, 200 )
            except TypeError: usock = urllib2.urlopen( url, None )
            response = usock.read()
            usock.close()
            if (callback):
                callback(json.loads(response))
            else:
                return json.loads( response )
        except:
            return None
