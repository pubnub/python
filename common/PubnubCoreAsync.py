## www.pubnub.com - PubNub Real-time push service in the cloud. 
# coding=utf8

## PubNub Real-time Push APIs and Notifications Framework
## Copyright (c) 2010 Stephen Blum
## http://www.pubnub.com/

## -----------------------------------
## PubNub 3.3.4 Real-time Push Cloud API
## -----------------------------------
import sys
import json
import time
import hashlib
import urllib2
import uuid
try:
    from hashlib import sha256
    digestmod = sha256
except ImportError:
    import Crypto.Hash.SHA256 as digestmod
    sha256 = digestmod.new
import hmac
from PubnubCrypto import PubnubCrypto
from PubnubBase import PubnubBase

class PubnubCoreAsync(PubnubBase):

    def start(self): pass 
    def stop(self):  pass
    def timeout( self, delay, callback ):
        pass

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
        #* @param string secret_key required key to sign messages.
        #* @param boolean ssl required for 2048 bit encrypted messages.
        #* @param string origin PUBNUB Server Origin.
        #**

        ## Initiat Class
        pubnub = Pubnub( 'PUBLISH-KEY', 'SUBSCRIBE-KEY', 'SECRET-KEY', False )

        """
        super(PubnubCoreAsync, self).__init__(
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
        #* This is NON-BLOCKING.
        #* Listen for a message on a channel.
        #*
        #* @param array args with channel and message.
        #* @return false on fail, array on success.
        #**

        ## Subscribe Example
        def receive(message) :
            print(message)
            return True

        ## On Connect Callback
        def connected() :
            pubnub.publish({
                'channel' : 'hello_world',
                'message' : { 'some_var' : 'text' }
            })

        ## Subscribe
        pubnub.subscribe({
            'channel'  : 'hello_world',
            'connect'  : connected,
            'callback' : receive
        })

        """
        ## Fail if missing channel
        if not 'channel' in args :
            return 'Missing Channel.'

        ## Fail if missing callback
        if not 'callback' in args :
            return 'Missing Callback.'

        ## Capture User Input
        channel   = str(args['channel'])
        callback  = args['callback']
        connectcb = args['connect']

        if 'errorback' in args:
            errorback = args['errorback']
        else:
            errorback = lambda x: x

        ## New Channel?
        if not (channel in self.subscriptions) :
            self.subscriptions[channel] = {
                'first'     : False,
                'connected' : False,
                'call_ids'  : set()
            }

        ## Ensure Single Connection
        if self.subscriptions[channel]['connected'] :
            return "Already Connected"

        self.subscriptions[channel]['connected'] = 1

        subscribe_call_uuid = uuid.uuid4()
        self.subscriptions[channel]['call_ids'].add(subscribe_call_uuid)

        ## SUBSCRIPTION RECURSION 
        def _subscribe():
            ## STOP CONNECTION?
            if not self.subscriptions[channel]['connected']:
                return
          
            ## STALE CONNECTION?
            call_ids = self.subscriptions[channel]['call_ids']
            if subscribe_call_uuid not in call_ids:
                return

            def sub_callback(response):
                if not self.subscriptions[channel]['first'] :
                    self.subscriptions[channel]['first'] = True
                    connectcb()

                ## STOP CONNECTION?
                if not self.subscriptions[channel]['connected']:
                    return

                ## STALE CONNECTION?
                call_ids = self.subscriptions[channel]['call_ids']
                if subscribe_call_uuid not in call_ids:
                    return

                ## PROBLEM?
                if not response:
                    def time_callback(_time):
                        if not _time:
                            self.timeout( 1, _subscribe )
                            return errorback("Lost Network Connection")
                        else:
                            self.timeout( 1, _subscribe)

                    ## ENSURE CONNECTED (Call Time Function)
                    return self.time({ 'callback' : time_callback })

                self.timetoken = response[1]
                _subscribe()

                pc = PubnubCrypto()
                out = []
                for message in response[0]:
                     callback(self.decrypt(message))

            ## CONNECT TO PUBNUB SUBSCRIBE SERVERS
            try:
                self._request( { "urlcomponents" : [
                    'subscribe',
                    self.subscribe_key,
                    channel,
                    '0',
                    str(self.timetoken)
                ], "urlparams" : {"uuid":self.uuid} }, sub_callback )
            except :
                self.timeout( 1, _subscribe)
                return

        ## BEGIN SUBSCRIPTION (LISTEN FOR MESSAGES)
        _subscribe()


    def unsubscribe( self, args ):
        channel = str(args['channel'])
        if not (channel in self.subscriptions):
            return False

        ## DISCONNECT
        self.subscriptions[channel]['connected'] = 0
        self.subscriptions[channel]['timetoken'] = 0
        self.subscriptions[channel]['first']     = False
        self.subscriptions[channel]['call_ids'].clear()
