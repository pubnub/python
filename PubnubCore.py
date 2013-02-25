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

import time
import hashlib
import urllib2
import uuid
from PubnubBase import PubnubBase

class PubnubCore(PubnubBase):
    def __init__(
        self,
        publish_key,
        subscribe_key,
        secret_key = False,
        cipher_key = False,
        ssl_on = False,
        origin = 'pubsub.pubnub.com',
        uuid = None
    ) :
        """
        #**
        #* Pubnub
        #*
        #* Init the Pubnub Client API
        #*
        #* @param string publish_key required key to send messages.
        #* @param string subscribe_key required key to receive messages.
        #* @param string secret_key optional key to sign messages.
        #* @param boolean ssl required for 2048 bit encrypted messages.
        #* @param string origin PUBNUB Server Origin.
        #* @param string pres_uuid optional identifier for presence (auto-generated if not supplied)
        #**

        ## Initiat Class
        pubnub = Pubnub( 'PUBLISH-KEY', 'SUBSCRIBE-KEY', 'SECRET-KEY', False )

        """
        super(PubnubCore, self).__init__(
            publish_key=publish_key,
            subscribe_key=subscribe_key,
            secret_key=secret_key,
            cipher_key=cipher_key,
            ssl_on=ssl_on,
            origin=origin,
            UUID=uuid
        )        

        self.subscriptions = {}
        self.timetoken     = 0
        self.version       = '3.4'
        self.accept_encoding = 'gzip'



    def subscribe( self, args ) :
        """
        #**
        #* Subscribe
        #*
        #* This is BLOCKING.
        #* Listen for a message on a channel.
        #*
        #* @param array args with channel and callback.
        #* @return false on fail, array on success.
        #**

        ## Subscribe Example
        def receive(message) :
            print(message)
            return True

        pubnub.subscribe({
            'channel'  : 'hello_world',
            'callback' : receive 
        })

        """

        ## Fail if missing channel
        if not 'channel' in args :
            raise Exception('Missing Channel.')
            return False

        ## Fail if missing callback
        if not 'callback' in args :
            raise Exception('Missing Callback.')
            return False

        ## Capture User Input
        channel   = str(args['channel'])
        callback  = args['callback']
        subscribe_key = args.get('subscribe_key') or self.subscribe_key

        ## Begin Subscribe
        while True :

            timetoken = 'timetoken' in args and args['timetoken'] or 0
            try :
                ## Wait for Message
                response = self._request(self._encode([
                    'subscribe',
                    subscribe_key,
                    channel,
                    '0',
                    str(timetoken)
                ])+['?uuid='+self.uuid], encode=False)

                messages          = response[0]
                args['timetoken'] = response[1]

                ## If it was a timeout
                if not len(messages) :
                    continue

                ## Run user Callback and Reconnect if user permits.
                for message in messages :
                    if not callback(message) :
                        return

            except Exception:
                time.sleep(1)

        return True
