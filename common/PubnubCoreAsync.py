try:
    from hashlib import sha256
    digestmod = sha256
except ImportError:
    import Crypto.Hash.SHA256 as digestmod
    sha256 = digestmod.new
import hmac
import threading
from threading import current_thread
import threading

class PubnubCoreAsync(PubnubBase):

    def start(self): pass 
    def stop(self):  pass

    def __init__(
        self,
        publish_key,
        subscribe_key,
        secret_key = False,
        cipher_key = False,
        auth_key = None,
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
            auth_key=auth_key,
            ssl_on=ssl_on,
            origin=origin,
            UUID=uuid
        )        

        self.subscriptions = {}
        self.timetoken     = 0
        self.last_timetoken = 0
        self.version       = '3.3.4'
        self.accept_encoding = 'gzip'
        self.SUB_RECEIVER  = None
        self._connect    = None
        self._tt_lock    = threading.RLock()

    def get_channel_list(self, channels):
        channel = ''
        first = True
        if self._channel_list_lock:
            with self._channel_list_lock:
                for ch in channels:
                    if not channels[ch]['subscribed']:
                        continue
                    if not first:
                        channel += ','
                    else:
                        first = False
                    channel += ch
        else:
            for ch in channels:
                if not channels[ch]['subscribed']:
                    continue
                if not first:
                    channel += ','
                else:
                    first = False
                channel += ch

        return channel

    def subscribe( self, args=None, sync=False ) :
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
        if args is None:
            _invoke(error, "Arguments Missing")
            return
        channel         = args['channel'] if 'channel' in args else None
        callback        = args['callback'] if 'callback' in args else None
        connect         = args['connect'] if 'connect' in args else None
        disconnect      = args['disconnect'] if 'disconnect' in args else None
        reconnect       = args['reconnect'] if 'reconnect' in args else None
        error           = args['error'] if 'error' in args else None

        with self._tt_lock:
            self.last_timetoken = self.timetoken if self.timetoken != 0 else self.last_timetoken
            self.timetoken = 0

        if channel is None:
            _invoke(error, "Channel Missing")
            return
        if callback is None:
            _invoke(error, "Callback Missing")
            return

        if sync is True and self.susbcribe_sync is not None:
            self.susbcribe_sync(args)
            return

        def _invoke(func,msg=None):
            if func is not None:
                if msg is not None:
                    func(msg)
                else:
                    func()

        def _invoke_connect():
            if self._channel_list_lock:
                with self._channel_list_lock:
                    for ch in self.subscriptions:
                        chobj = self.subscriptions[ch]
                        if chobj['connected'] is False:
                            chobj['connected'] = True
                            _invoke(chobj['connect'],chobj['name'])

        def _invoke_error(err=None):
            for ch in self.subscriptions:
                chobj = self.subscriptions[ch]
                _invoke(chobj.error,err)

        '''
        if callback is None:
            _invoke(error, "Callback Missing")
            return

        if channel is None:
            _invoke(error, "Channel Missing")
            return
        '''

        def _get_channel():
            for ch in self.subscriptions:
                chobj = self.subscriptions[ch]
                if chobj['subscribed'] is True:
                    return chobj


        ## New Channel?
        if not channel in self.subscriptions:
            if self._channel_list_lock:
                with self._channel_list_lock:
                    self.subscriptions[channel] = {
                        'name'          : channel,
                        'first'         : False,
                        'connected'     : False,
                        'subscribed'    : True,
                        'callback'      : callback,
                        'connect'       : connect,
                        'disconnect'    : disconnect,
                        'reconnect'     : reconnect
                    }
            else:
                self.subscriptions[channel] = {
                    'name'          : channel,
                    'first'         : False,
                    'connected'     : False,
                    'subscribed'    : True,
                    'callback'      : callback,
                    'connect'       : connect,
                    'disconnect'    : disconnect,
                    'reconnect'     : reconnect
                }

        ## return if already connected to channel
        if channel in self.subscriptions and 'connected' in self.subscriptions[channel] and self.subscriptions[channel]['connected'] is True:
            _invoke(error, "Already Connected")
            return
            
            

        ## SUBSCRIPTION RECURSION 
        def _connect():
          
            self._reset_offline()

            def sub_callback(response):
                ## ERROR ?
                if not response or error in response:
                    _invoke_error()

                _invoke_connect()

                with self._tt_lock:
                    #print 'A tt : ', self.timetoken , ' last tt : ' , self.last_timetoken
                    self.timetoken = self.last_timetoken if self.timetoken == 0 and self.last_timetoken != 0 else response[1]
                    #print 'B tt : ', self.timetoken , ' last tt : ' , self.last_timetoken
                    if len(response) > 2:
                        channel_list = response[2].split(',')
                        response_list = response[0]
                        for ch in enumerate(channel_list):
                            if ch[1] in self.subscriptions:
                                chobj = self.subscriptions[ch[1]]
                                _invoke(chobj['callback'],self.decrypt(response_list[ch[0]]))
                    else:
                        response_list = response[0]
                        chobj = _get_channel()
                        for r in response_list:
                            if chobj:
                                _invoke(chobj['callback'], self.decrypt(r))

                    #with self._tt_lock:
                    #    self.timetoken = self.last_timetoken if self.timetoken == 0 and self.last_timetoken != 0 else response[1]
                    _connect()



            channel_list = self.get_channel_list(self.subscriptions)
            ## CONNECT TO PUBNUB SUBSCRIBE SERVERS
            try:
                self.SUB_RECEIVER = self._request( { "urlcomponents" : [
                    'subscribe',
                    self.subscribe_key,
                    channel_list,
                    '0',
                    str(self.timetoken)
                ], "urlparams" : {"uuid":self.uuid} }, sub_callback, single=True )
            except Exception as e:
                print e
                self.timeout( 1, _connect)
                return

        self._connect = _connect


        ## BEGIN SUBSCRIPTION (LISTEN FOR MESSAGES)
        _connect()

    def _reset_offline(self):
        if self.SUB_RECEIVER is not None:
            self.SUB_RECEIVER()
        self.SUB_RECEIVER = None

    def CONNECT(self):
        self._reset_offline()
        self._connect()


    def unsubscribe( self, args ):
        #print(args['channel'])
        channel = str(args['channel'])
        if not (channel in self.subscriptions):
            return False

        ## DISCONNECT
        self.subscriptions[channel]['connected'] = 0
        self.subscriptions[channel]['subscribed'] = False
        self.subscriptions[channel]['timetoken'] = 0
        self.subscriptions[channel]['first']     = False
        self.CONNECT()
