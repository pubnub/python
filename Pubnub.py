try:
    import json
except ImportError:
    import simplejson as json

import time
import hashlib
import uuid
import sys

try:
    from urllib.parse import quote
except ImportError:
    from urllib2 import quote

from base64 import urlsafe_b64encode
from hashlib import sha256


import hmac



from Crypto.Cipher import AES
from Crypto.Hash import MD5
from base64 import encodestring, decodestring
import hashlib
import hmac


class PubnubCrypto2():
    """
    #**
    #* PubnubCrypto
    #*
    #**

    ## Initiate Class
    pc = PubnubCrypto

    """

    def pad(self, msg, block_size=16):
        """
        #**
        #* pad
        #*
        #* pad the text to be encrypted
        #* appends a padding character to the end of the String
        #* until the string has block_size length
        #* @return msg with padding.
        #**
        """
        padding = block_size - (len(msg) % block_size)
        return msg + chr(padding) * padding

    def depad(self, msg):
        """
        #**
        #* depad
        #*
        #* depad the decryptet message"
        #* @return msg without padding.
        #**
        """
        return msg[0:-ord(msg[-1])]

    def getSecret(self, key):
        """
        #**
        #* getSecret
        #*
        #* hases the key to MD5
        #* @return key in MD5 format
        #**
        """
        return hashlib.sha256(key).hexdigest()

    def encrypt(self, key, msg):
        """
        #**
        #* encrypt
        #*
        #* encrypts the message
        #* @return message in encrypted format
        #**
        """
        secret = self.getSecret(key)
        Initial16bytes = '0123456789012345'
        cipher = AES.new(secret[0:32], AES.MODE_CBC, Initial16bytes)
        enc = encodestring(cipher.encrypt(self.pad(msg)))
        return enc

    def decrypt(self, key, msg):
        """
        #**
        #* decrypt
        #*
        #* decrypts the message
        #* @return message in decryped format
        #**
        """
        secret = self.getSecret(key)
        Initial16bytes = '0123456789012345'
        cipher = AES.new(secret[0:32], AES.MODE_CBC, Initial16bytes)
        return self.depad((cipher.decrypt(decodestring(msg))))


class PubnubCrypto3():
    """
    #**
    #* PubnubCrypto
    #*
    #**

    ## Initiate Class
    pc = PubnubCrypto

    """

    def pad(self, msg, block_size=16):
        """
        #**
        #* pad
        #*
        #* pad the text to be encrypted
        #* appends a padding character to the end of the String
        #* until the string has block_size length
        #* @return msg with padding.
        #**
        """
        padding = block_size - (len(msg) % block_size)
        return msg + (chr(padding) * padding).encode('utf-8')

    def depad(self, msg):
        """
        #**
        #* depad
        #*
        #* depad the decryptet message"
        #* @return msg without padding.
        #**
        """
        return msg[0:-ord(msg[-1])]

    def getSecret(self, key):
        """
        #**
        #* getSecret
        #*
        #* hases the key to MD5
        #* @return key in MD5 format
        #**
        """
        return hashlib.sha256(key.encode("utf-8")).hexdigest()

    def encrypt(self, key, msg):
        """
        #**
        #* encrypt
        #*
        #* encrypts the message
        #* @return message in encrypted format
        #**
        """
        secret = self.getSecret(key)
        Initial16bytes = '0123456789012345'
        cipher = AES.new(secret[0:32], AES.MODE_CBC, Initial16bytes)
        return encodestring(
            cipher.encrypt(self.pad(msg.encode('utf-8')))).decode('utf-8')

    def decrypt(self, key, msg):
        """
        #**
        #* decrypt
        #*
        #* decrypts the message
        #* @return message in decryped format
        #**
        """
        secret = self.getSecret(key)
        Initial16bytes = '0123456789012345'
        cipher = AES.new(secret[0:32], AES.MODE_CBC, Initial16bytes)
        return (cipher.decrypt(
            decodestring(msg.encode('utf-8')))).decode('utf-8')


class PubnubBase(object):
    def __init__(
        self,
        publish_key,
        subscribe_key,
        secret_key=False,
        cipher_key=False,
        auth_key=None,
        ssl_on=False,
        origin='pubsub.pubnub.com',
        UUID=None
    ):
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
        #* @param string pres_uuid optional identifier
        #*    for presence (auto-generated if not supplied)
        #**

        ## Initiat Class
        pubnub = Pubnub( 'PUBLISH-KEY', 'SUBSCRIBE-KEY', 'SECRET-KEY', False )

        """
        self.origin = origin
        self.limit = 1800
        self.publish_key = publish_key
        self.subscribe_key = subscribe_key
        self.secret_key = secret_key
        self.cipher_key = cipher_key
        self.ssl = ssl_on
        self.auth_key = auth_key

        if self.ssl:
            self.origin = 'https://' + self.origin
        else:
            self.origin = 'http://' + self.origin

        self.uuid = UUID or str(uuid.uuid4())

        if type(sys.version_info) is tuple:
            self.python_version = 2
            self.pc = PubnubCrypto2()
        else:
            if sys.version_info.major == 2:
                self.python_version = 2
                self.pc = PubnubCrypto2()
            else:
                self.python_version = 3
                self.pc = PubnubCrypto3()

        if not isinstance(self.uuid, str):
            raise AttributeError("pres_uuid must be a string")

    '''

    def _sign(self, channel, message):
        ## Sign Message
        if self.secret_key:
            signature = hashlib.md5('/'.join([
                self.publish_key,
                self.subscribe_key,
                self.secret_key,
                channel,
                message
            ])).hexdigest()
        else:
            signature = '0'
        return signature
    '''

    def _pam_sign(self, msg):
        """Calculate a signature by secret key and message."""

        return urlsafe_b64encode(hmac.new(
            self.secret_key.encode("utf-8"),
            msg.encode("utf-8"),
            sha256
        ).digest())

    def _pam_auth(self, query, apicode=0, callback=None):
        """Issue an authenticated request."""

        if 'timestamp' not in query:
            query['timestamp'] = int(time.time())

        ## Global Grant?
        if 'auth' in query and not query['auth']:
            del query['auth']

        if 'channel' in query and not query['channel']:
            del query['channel']

        params = "&".join([
            x + "=" + quote(
                str(query[x]), safe=""
            ) for x in sorted(query)
        ])
        sign_input = "{subkey}\n{pubkey}\n{apitype}\n{params}".format(
            subkey=self.subscribe_key,
            pubkey=self.publish_key,
            apitype="audit" if (apicode) else "grant",
            params=params
        )

        query['signature'] = self._pam_sign(sign_input)

        return self._request({"urlcomponents": [
            'v1', 'auth', "audit" if (apicode) else "grant",
            'sub-key',
            self.subscribe_key
        ], 'urlparams': query},
            self._return_wrapped_callback(callback))

    def grant(self, channel, authkey=False, read=True,
              write=True, ttl=5, callback=None):
        """Grant Access on a Channel."""

        return self._pam_auth({
            "channel": channel,
            "auth": authkey,
            "r": read and 1 or 0,
            "w": write and 1 or 0,
            "ttl": ttl
        }, callback=callback)

    def revoke(self, channel, authkey=False, ttl=1, callback=None):
        """Revoke Access on a Channel."""

        return self._pam_auth({
            "channel": channel,
            "auth": authkey,
            "r": 0,
            "w": 0,
            "ttl": ttl
        }, callback=callback)

    def audit(self, channel=False, authkey=False, callback=None):
        return self._pam_auth({
            "channel": channel,
            "auth": authkey
        }, 1, callback=callback)

    def encrypt(self, message):
        if self.cipher_key:
            message = json.dumps(self.pc.encrypt(
                self.cipher_key, json.dumps(message)).replace('\n', ''))
        else:
            message = json.dumps(message)

        return message

    def decrypt(self, message):
        if self.cipher_key:
            message = self.pc.decrypt(self.cipher_key, message)

        return message

    def _return_wrapped_callback(self, callback=None):
        def _new_format_callback(response):
            if 'payload' in response:
                if (callback is not None):
                    callback({'message': response['message'],
                              'payload': response['payload']})
            else:
                if (callback is not None):
                    callback(response)
        if (callback is not None):
            return _new_format_callback
        else:
            return None

    def publish(channel, message, callback=None, error=None):
        """
        #**
        #* Publish
        #*
        #* Send a message to a channel.
        #*
        #* @param array args with channel and message.
        #* @return array success information.
        #**

        ## Publish Example
        info = pubnub.publish({
            'channel' : 'hello_world',
            'message' : {
                'some_text' : 'Hello my World'
            }
        })
        print(info)

        """

        message = self.encrypt(message)

        ## Send Message
        return self._request({"urlcomponents": [
            'publish',
            self.publish_key,
            self.subscribe_key,
            '0',
            channel,
            '0',
            message
        ], 'urlparams': {'auth': self.auth_key}},
            callback=self._return_wrapped_callback(callback),
            error=self._return_wrapped_callback(error))

    def presence(self, channel, callback, error=None):
        """
        #**
        #* presence
        #*
        #* This is BLOCKING.
        #* Listen for presence events on a channel.
        #*
        #* @param array args with channel and callback.
        #* @return false on fail, array on success.
        #**

        ## Presence Example
        def pres_event(message) :
            print(message)
            return True

        pubnub.presence({
            'channel'  : 'hello_world',
            'callback' : receive
        })
        """
        return self.subscribe({
            'channel': channel + '-pnpres',
            'subscribe_key': self.subscribe_key,
            'callback': self._return_wrapped_callback(callback)})

    def here_now(self, channel, callback, error=None):
        """
        #**
        #* Here Now
        #*
        #* Load current occupancy from a channel.
        #*
        #* @param array args with 'channel'.
        #* @return mixed false on fail, array on success.
        #*

        ## Presence Example
        here_now = pubnub.here_now({
            'channel' : 'hello_world',
        })
        print(here_now['occupancy'])
        print(here_now['uuids'])

        """

        ## Get Presence Here Now
        return self._request({"urlcomponents": [
            'v2', 'presence',
            'sub_key', self.subscribe_key,
            'channel', channel
        ], 'urlparams': {'auth': self.auth_key}},
            callback=self._return_wrapped_callback(callback),
            error=self._return_wrapped_callback(error))

    def history(self, channel, count=100, reverse=False,
                start=None, end=None, callback=None, error=None):
        """
        #**
        #* History
        #*
        #* Load history from a channel.
        #*

        ## History Example
        history = pubnub.detailedHistory({
            'channel' : 'hello_world',
            'count'   : 5
        })
        print(history)

        """

        params = dict()

        params['count'] = count
        params['reverse'] = reverse
        params['start'] = start
        params['end'] = end

        ## Get History
        return self._request({'urlcomponents': [
            'v2',
            'history',
            'sub-key',
            self.subscribe_key,
            'channel',
            channel,
        ], 'urlparams': {'auth': self.auth_key}},
            callback=self._return_wrapped_callback(callback),
            error=self._return_wrapped_callback(error))

    def time(self, callback=None):
        """
        #**
        #* Time
        #*
        #* Timestamp from PubNub Cloud.
        #*
        #* @return int timestamp.
        #*

        ## PubNub Server Time Example
        timestamp = pubnub.time()
        print(timestamp)

        """

        time = self._request({'urlcomponents': [
            'time',
            '0'
        ]}, callback)
        if time is not None:
            return time[0]

    def _encode(self, request):
        return [
            "".join([' ~`!@#$%^&*()+=[]\\{}|;\':",./<>?'.find(ch) > -1 and
                     hex(ord(ch)).replace('0x', '%').upper() or
                     ch for ch in list(bit)
                     ]) for bit in request]

    def getUrl(self, request):
        ## Build URL
        url = self.origin + '/' + "/".join([
            "".join([' ~`!@#$%^&*()+=[]\\{}|;\':",./<>?'.find(ch) > -1 and
                     hex(ord(ch)).replace('0x', '%').upper() or
                     ch for ch in list(bit)
                     ]) for bit in request["urlcomponents"]])
        if ("urlparams" in request):
            url = url + '?' + "&".join([x + "=" + str(y) for x, y in request[
                "urlparams"].items() if y is not None])
        return url


try:
    from hashlib import sha256
    digestmod = sha256
except ImportError:
    import Crypto.Hash.SHA256 as digestmod
    sha256 = digestmod.new
import hmac


class EmptyLock():
    def __enter__(self):
        pass

    def __exit__(self, a, b, c):
        pass

empty_lock = EmptyLock()


class PubnubCoreAsync(PubnubBase):

    def start(self):
        pass

    def stop(self):
        pass

    def __init__(
        self,
        publish_key,
        subscribe_key,
        secret_key=False,
        cipher_key=False,
        auth_key=None,
        ssl_on=False,
        origin='pubsub.pubnub.com',
        uuid=None,
        _tt_lock=empty_lock,
        _channel_list_lock=empty_lock
    ):
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
        self.timetoken = 0
        self.last_timetoken = 0
        self.version = '3.3.4'
        self.accept_encoding = 'gzip'
        self.SUB_RECEIVER = None
        self._connect = None
        self._tt_lock = _tt_lock
        self._channel_list_lock = _channel_list_lock
        self._connect = lambda: None

    def get_channel_list(self, channels):
        channel = ''
        first = True
        with self._channel_list_lock:
            for ch in channels:
                if not channels[ch]['subscribed']:
                    continue
                if not first:
                    channel += ','
                else:
                    first = False
                channel += ch
        return channel

    def get_channel_array(self):
        channels = self.subscriptions
        channel = []
        with self._channel_list_lock:
            for ch in channels:
                if not channels[ch]['subscribed']:
                    continue
                channel.append(ch)
        return channel

    def each(l, func):
        if func is None:
            return
        for i in l:
            func(i)

    def subscribe(self, channel, callback, error=None,
                  connect=None, disconnect=None, reconnect=None, sync=False):
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

        with self._tt_lock:
            self.last_timetoken = self.timetoken if self.timetoken != 0 \
                else self.last_timetoken
            self.timetoken = 0

        if sync is True and self.susbcribe_sync is not None:
            self.susbcribe_sync(args)
            return

        def _invoke(func, msg=None):
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
                            _invoke(chobj['connect'], chobj['name'])

        def _invoke_error(channel_list=None, err=None):
            if channel_list is None:
                for ch in self.subscriptions:
                    chobj = self.subscriptions[ch]
                    _invoke(chobj['error'], err)
            else:
                for ch in channel_list:
                    chobj = self.subscriptions[ch]
                    _invoke(chobj['error'], err)

        def _get_channel():
            for ch in self.subscriptions:
                chobj = self.subscriptions[ch]
                if chobj['subscribed'] is True:
                    return chobj

        ## New Channel?
        if not channel in self.subscriptions or \
                self.subscriptions[channel]['subscribed'] is False:
                with self._channel_list_lock:
                    self.subscriptions[channel] = {
                        'name': channel,
                        'first': False,
                        'connected': False,
                        'subscribed': True,
                        'callback': callback,
                        'connect': connect,
                        'disconnect': disconnect,
                        'reconnect': reconnect,
                        'error': error
                    }

        ## return if already connected to channel
        if channel in self.subscriptions and \
            'connected' in self.subscriptions[channel] and \
                self.subscriptions[channel]['connected'] is True:
                    _invoke(error, "Already Connected")
                    return

        ## SUBSCRIPTION RECURSION
        def _connect():

            self._reset_offline()

            def error_callback(response):
                ## ERROR ?
                if not response or \
                    ('message' in response and
                        response['message'] == 'Forbidden'):
                            _invoke_error(response['payload'][
                                'channels'], response['message'])
                            _connect()
                            return
                if 'message' in response:
                    _invoke_error(err=response['message'])
   

            def sub_callback(response):
                ## ERROR ?
                if not response or \
                    ('message' in response and
                        response['message'] == 'Forbidden'):
                            _invoke_error(response['payload'][
                                'channels'], response['message'])
                            _connect()
                            return

                _invoke_connect()

                with self._tt_lock:
                    self.timetoken = \
                        self.last_timetoken if self.timetoken == 0 and \
                        self.last_timetoken != 0 else response[1]
                    if len(response) > 2:
                        channel_list = response[2].split(',')
                        response_list = response[0]
                        for ch in enumerate(channel_list):
                            if ch[1] in self.subscriptions:
                                chobj = self.subscriptions[ch[1]]
                                _invoke(chobj['callback'],
                                        self.decrypt(response_list[ch[0]]))
                    else:
                        response_list = response[0]
                        chobj = _get_channel()
                        for r in response_list:
                            if chobj:
                                _invoke(chobj['callback'], self.decrypt(r))

                    _connect()

            channel_list = self.get_channel_list(self.subscriptions)
            if len(channel_list) <= 0:
                return

            ## CONNECT TO PUBNUB SUBSCRIBE SERVERS
            #try:
            self.SUB_RECEIVER = self._request({"urlcomponents": [
                'subscribe',
                self.subscribe_key,
                channel_list,
                '0',
                str(self.timetoken)
            ], "urlparams": {"uuid": self.uuid, "auth": self.auth_key}},
                sub_callback,
                error_callback,
                single=True)
            '''
            except Exception as e:
                print(e)
                self.timeout(1, _connect)
                return
            '''

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

    def unsubscribe(self, channel):

        if channel in self.subscriptions is False:
            return False

        ## DISCONNECT
        with self._channel_list_lock:
            if channel in self.subscriptions:
                self.subscriptions[channel]['connected'] = 0
                self.subscriptions[channel]['subscribed'] = False
                self.subscriptions[channel]['timetoken'] = 0
                self.subscriptions[channel]['first'] = False
        self.CONNECT()


class PubnubCore(PubnubCoreAsync):
    def __init__(
        self,
        publish_key,
        subscribe_key,
        secret_key=False,
        cipher_key=False,
        auth_key=None,
        ssl_on=False,
        origin='pubsub.pubnub.com',
        uuid=None
    ):
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
        #* @param string pres_uuid optional
        #*  identifier for presence (auto-generated if not supplied)
        #**

        ## Initiat Class
        pubnub = Pubnub( 'PUBLISH-KEY', 'SUBSCRIBE-KEY', 'SECRET-KEY', False )

        """
        super(PubnubCore, self).__init__(
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
        self.timetoken = 0
        self.version = '3.4'
        self.accept_encoding = 'gzip'

    def subscribe_sync(self, channel, callback, timetoken=0):
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

        subscribe_key = self.subscribe_key

        ## Begin Subscribe
        while True:

            try:
                ## Wait for Message
                response = self._request({"urlcomponents": [
                    'subscribe',
                    subscribe_key,
                    channel,
                    '0',
                    str(timetoken)
                ], "urlparams": {"uuid": self.uuid}})

                messages = response[0]
                timetoken = response[1]

                ## If it was a timeout
                if not len(messages):
                    continue

                ## Run user Callback and Reconnect if user permits.
                for message in messages:
                    if not callback(self.decrypt(message)):
                        return

            except Exception:
                time.sleep(1)

        return True


try:
    import urllib.request
except ImportError:
    import urllib2

import threading
import json
import time
import threading
from threading import current_thread

latest_sub_callback_lock = threading.RLock()
latest_sub_callback = {'id': None, 'callback': None}


class HTTPClient:
    def __init__(self, url, urllib_func=None,
                 callback=None, error=None, id=None):
        self.url = url
        self.id = id
        self.callback = callback
        self.error = error
        self.stop = False
        self._urllib_func = urllib_func

    def cancel(self):
        self.stop = True
        self.callback = None
        self.error = None

    def run(self):

        def _invoke(func, data):
            if func is not None:
                func(data)

        if self._urllib_func is None:
            return

        '''
        try:
            resp = urllib2.urlopen(self.url, timeout=320)
        except urllib2.HTTPError as http_error:
            resp = http_error
        '''
        resp = self._urllib_func(self.url, timeout=320)
        data = resp[0]
        code = resp[1]

        if self.stop is True:
            return
        if self.callback is None:
            global latest_sub_callback
            global latest_sub_callback_lock
            with latest_sub_callback_lock:
                if latest_sub_callback['id'] != self.id:
                    return
                else:
                    if latest_sub_callback['callback'] is not None:
                        latest_sub_callback['id'] = 0
                        print data
                        try:
                            data = json.loads(data)
                        except ValueError as e:
                            _invoke(latest_sub_callback['error'],
                                    {'error': 'json decoding error'})
                            return
                        print code
                        if code != 200:
                            print 'ERROR'
                            _invoke(latest_sub_callback['error'], data)
                        else:
                            print 'CALLBACK'
                            _invoke(latest_sub_callback['callback'], data)
        else:
            try:
                data = json.loads(data)
            except ValueError:
                _invoke(self.error, {'error': 'json decoding error'})
                return

            if code != 200:
                _invoke(self.error, data)
            else:
                _invoke(self.callback, data)


def _urllib_request_2(url, timeout=320):
    try:
        resp = urllib2.urlopen(url, timeout=timeout)
    except urllib2.HTTPError as http_error:
        resp = http_error
    except urllib2.URLError as error:
        #print error.reason
        msg = { "message" : str(error.reason)}
        #print str(msg)
        return (json.dumps(msg),0)
    
    return (resp.read(), resp.code)


def _urllib_request_3(url, timeout=320):
    #print(url)
    try:
        resp = urllib.request.urlopen(url, timeout=timeout)
    except (urllib.request.HTTPError, urllib.request.URLError) as http_error:
        resp = http_error
    r = resp.read().decode("utf-8")
    #print(r)
    return (r, resp.code)

_urllib_request = None


class PubnubAsync(PubnubCoreAsync):
    def __init__(
        self,
        publish_key,
        subscribe_key,
        secret_key=False,
        cipher_key=False,
        auth_key=None,
        ssl_on=False,
        origin='pubsub.pubnub.com',
        pres_uuid=None
    ):
        super(Pubnub, self).__init__(
            publish_key=publish_key,
            subscribe_key=subscribe_key,
            secret_key=secret_key,
            cipher_key=cipher_key,
            auth_key=auth_key,
            ssl_on=ssl_on,
            origin=origin,
            uuid=pres_uuid,
            _tt_lock=threading.RLock(),
            _channel_list_lock=threading.RLock()
        )
        global _urllib_request
        if self.python_version == 2:
            _urllib_request = _urllib_request_2
        else:
            _urllib_request = _urllib_request_3

    def timeout(self, interval, func):
        def cb():
            time.sleep(interval)
            func()
        thread = threading.Thread(target=cb)
        thread.start()

    def _request_async(self, request, callback=None, error=None, single=False):
        global _urllib_request
        ## Build URL
        url = self.getUrl(request)
        if single is True:
            id = time.time()
            client = HTTPClient(url=url, urllib_func=_urllib_request,
                                callback=None, error=None, id=id)
            with latest_sub_callback_lock:
                latest_sub_callback['id'] = id
                latest_sub_callback['callback'] = callback
                latest_sub_callback['error'] = error
        else:
            client = HTTPClient(url=url, urllib_func=_urllib_request,
                                callback=callback, error=error)

        thread = threading.Thread(target=client.run)
        thread.start()

        def abort():
            client.cancel()
        return abort

    def _request_sync(self, request):
        global _urllib_request
        ## Build URL
        url = self.getUrl(request)
        ## Send Request Expecting JSONP Response
        response = _urllib_request(url, timeout=320)
        try:
            resp_json = json.loads(response[0])
        except ValueError:
            return [0, "JSON Error"]

        if response[1] != 200 and 'status' in resp_json:
            return {'message': resp_json['message'],
                    'payload': resp_json['payload']}

        return resp_json

    def _request(self, request, callback=None, error=None, single=False):
        if callback is None:
            return self._request_sync(request)
        else:
            self._request_async(request, callback, error, single=single)

'''

    def _request3_sync( self, request) :
        ## Build URL
        url = self.getUrl(request)
        ## Send Request Expecting JSONP Response
        try:
            response = urllib.request.urlopen(url,timeout=310)
            resp_json = json.loads(response.read().decode("utf-8"))
        except Exception as e:
            return None

        return resp_json

    def _request3_async( self, request, callback, single=False ) :
        pass

    def _request3(self, request, callback=None, single=False):
        if callback is None:
            return self._request3_sync(request,single=single)
        else:
            self._request3_async(request, callback, single=single)
            '''


import tornado.httpclient

try:
    from hashlib import sha256
    digestmod = sha256
except ImportError:
    import Crypto.Hash.SHA256 as digestmod
    sha256 = digestmod.new

import hmac
import tornado.ioloop
from tornado.stack_context import ExceptionStackContext

ioloop = tornado.ioloop.IOLoop.instance()


class PubnubTornado(PubnubCoreAsync):

    def stop(self):
        ioloop.stop()

    def start(self):
        ioloop.start()

    def timeout(self, delay, callback):
        ioloop.add_timeout(time.time() + float(delay), callback)

    def __init__(
        self,
        publish_key,
        subscribe_key,
        secret_key=False,
        cipher_key=False,
        auth_key=False,
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
        self.headers['User-Agent'] = 'Python-Tornado'
        self.headers['Accept-Encoding'] = self.accept_encoding
        self.headers['V'] = self.version
        self.http = tornado.httpclient.AsyncHTTPClient(max_clients=1000)
        self.id = None

    def _request(self, request, callback=None, error=None,
                 single=False, read_timeout=5, connect_timeout=5):

        def _invoke(func, data):
            if func is not None:
                func(data)

        url = self.getUrl(request)
        request = tornado.httpclient.HTTPRequest(
            url, 'GET',
            self.headers,
            connect_timeout=connect_timeout,
            request_timeout=read_timeout)
        if single is True:
            id = time.time()
            self.id = id

        def responseCallback(response):
            if single is True:
                if not id == self.id:
                    return None

            body = response._get_body()

            if body is None:
                return

            def handle_exc(*args):
                return True
            if response.error is not None:
                with ExceptionStackContext(handle_exc):
                    if response.code in [403, 401]:
                        response.rethrow()
                    else:
                        _invoke(error, {"message": response.reason})
                    return

            try:
                data = json.loads(body)
            except TypeError as e:
                try:
                    data = json.loads(body.decode("utf-8"))
                except ValueError as ve:
                    _invoke(error, {'error': 'json decode error'})

            if 'error' in data and 'status' in data and 'status' != 200:
                _invoke(error, data)
            else:
                _invoke(callback, data)

        self.http.fetch(
            request=request,
            callback=responseCallback
        )

        def abort():
            pass

        return abort

## www.pubnub.com - PubNub Real-time push service in the cloud. 
# coding=utf8

## PubNub Real-time Push APIs and Notifications Framework
## Copyright (c) 2010 Stephen Blum
## http://www.pubnub.com/

## -----------------------------------
## PubNub 3.3.5 Real-time Push Cloud API
## -----------------------------------


from Crypto.Cipher import AES
from Crypto.Hash import MD5
from base64 import encodestring, decodestring
import hashlib
import hmac


class PubnubCrypto2():
    """
    #**
    #* PubnubCrypto
    #*
    #**

    ## Initiate Class
    pc = PubnubCrypto

    """

    def pad(self, msg, block_size=16):
        """
        #**
        #* pad
        #*
        #* pad the text to be encrypted
        #* appends a padding character to the end of the String
        #* until the string has block_size length
        #* @return msg with padding.
        #**
        """
        padding = block_size - (len(msg) % block_size)
        return msg + chr(padding) * padding

    def depad(self, msg):
        """
        #**
        #* depad
        #*
        #* depad the decryptet message"
        #* @return msg without padding.
        #**
        """
        return msg[0:-ord(msg[-1])]

    def getSecret(self, key):
        """
        #**
        #* getSecret
        #*
        #* hases the key to MD5
        #* @return key in MD5 format
        #**
        """
        return hashlib.sha256(key).hexdigest()

    def encrypt(self, key, msg):
        """
        #**
        #* encrypt
        #*
        #* encrypts the message
        #* @return message in encrypted format
        #**
        """
        secret = self.getSecret(key)
        Initial16bytes = '0123456789012345'
        cipher = AES.new(secret[0:32], AES.MODE_CBC, Initial16bytes)
        enc = encodestring(cipher.encrypt(self.pad(msg)))
        return enc

    def decrypt(self, key, msg):
        """
        #**
        #* decrypt
        #*
        #* decrypts the message
        #* @return message in decryped format
        #**
        """
        secret = self.getSecret(key)
        Initial16bytes = '0123456789012345'
        cipher = AES.new(secret[0:32], AES.MODE_CBC, Initial16bytes)
        return self.depad((cipher.decrypt(decodestring(msg))))


class PubnubCrypto3():
    """
    #**
    #* PubnubCrypto
    #*
    #**

    ## Initiate Class
    pc = PubnubCrypto

    """

    def pad(self, msg, block_size=16):
        """
        #**
        #* pad
        #*
        #* pad the text to be encrypted
        #* appends a padding character to the end of the String
        #* until the string has block_size length
        #* @return msg with padding.
        #**
        """
        padding = block_size - (len(msg) % block_size)
        return msg + (chr(padding) * padding).encode('utf-8')

    def depad(self, msg):
        """
        #**
        #* depad
        #*
        #* depad the decryptet message"
        #* @return msg without padding.
        #**
        """
        return msg[0:-ord(msg[-1])]

    def getSecret(self, key):
        """
        #**
        #* getSecret
        #*
        #* hases the key to MD5
        #* @return key in MD5 format
        #**
        """
        return hashlib.sha256(key.encode("utf-8")).hexdigest()

    def encrypt(self, key, msg):
        """
        #**
        #* encrypt
        #*
        #* encrypts the message
        #* @return message in encrypted format
        #**
        """
        secret = self.getSecret(key)
        Initial16bytes = '0123456789012345'
        cipher = AES.new(secret[0:32], AES.MODE_CBC, Initial16bytes)
        return encodestring(
            cipher.encrypt(self.pad(msg.encode('utf-8')))).decode('utf-8')

    def decrypt(self, key, msg):
        """
        #**
        #* decrypt
        #*
        #* decrypts the message
        #* @return message in decryped format
        #**
        """
        secret = self.getSecret(key)
        Initial16bytes = '0123456789012345'
        cipher = AES.new(secret[0:32], AES.MODE_CBC, Initial16bytes)
        return (cipher.decrypt(
            decodestring(msg.encode('utf-8')))).decode('utf-8')


try:
    import json
except ImportError:
    import simplejson as json

import time
import hashlib
import uuid
import sys

try:
    from urllib.parse import quote
except ImportError:
    from urllib2 import quote

from base64 import urlsafe_b64encode
from hashlib import sha256


import hmac


class PubnubBase(object):
    def __init__(
        self,
        publish_key,
        subscribe_key,
        secret_key=False,
        cipher_key=False,
        auth_key=None,
        ssl_on=False,
        origin='pubsub.pubnub.com',
        UUID=None
    ):
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
        #* @param string pres_uuid optional identifier
        #*    for presence (auto-generated if not supplied)
        #**

        ## Initiat Class
        pubnub = Pubnub( 'PUBLISH-KEY', 'SUBSCRIBE-KEY', 'SECRET-KEY', False )

        """
        self.origin = origin
        self.limit = 1800
        self.publish_key = publish_key
        self.subscribe_key = subscribe_key
        self.secret_key = secret_key
        self.cipher_key = cipher_key
        self.ssl = ssl_on
        self.auth_key = auth_key

        if self.ssl:
            self.origin = 'https://' + self.origin
        else:
            self.origin = 'http://' + self.origin

        self.uuid = UUID or str(uuid.uuid4())

        if type(sys.version_info) is tuple:
            self.python_version = 2
            self.pc = PubnubCrypto2()
        else:
            if sys.version_info.major == 2:
                self.python_version = 2
                self.pc = PubnubCrypto2()
            else:
                self.python_version = 3
                self.pc = PubnubCrypto3()

        if not isinstance(self.uuid, str):
            raise AttributeError("pres_uuid must be a string")

    '''

    def _sign(self, channel, message):
        ## Sign Message
        if self.secret_key:
            signature = hashlib.md5('/'.join([
                self.publish_key,
                self.subscribe_key,
                self.secret_key,
                channel,
                message
            ])).hexdigest()
        else:
            signature = '0'
        return signature
    '''

    def _pam_sign(self, msg):
        """Calculate a signature by secret key and message."""

        return urlsafe_b64encode(hmac.new(
            self.secret_key.encode("utf-8"),
            msg.encode("utf-8"),
            sha256
        ).digest())

    def _pam_auth(self, query, apicode=0, callback=None):
        """Issue an authenticated request."""

        if 'timestamp' not in query:
            query['timestamp'] = int(time.time())

        ## Global Grant?
        if 'auth' in query and not query['auth']:
            del query['auth']

        if 'channel' in query and not query['channel']:
            del query['channel']

        params = "&".join([
            x + "=" + quote(
                str(query[x]), safe=""
            ) for x in sorted(query)
        ])
        sign_input = "{subkey}\n{pubkey}\n{apitype}\n{params}".format(
            subkey=self.subscribe_key,
            pubkey=self.publish_key,
            apitype="audit" if (apicode) else "grant",
            params=params
        )

        query['signature'] = self._pam_sign(sign_input)

        return self._request({"urlcomponents": [
            'v1', 'auth', "audit" if (apicode) else "grant",
            'sub-key',
            self.subscribe_key
        ], 'urlparams': query},
            self._return_wrapped_callback(callback))

    def grant(self, channel, authkey=False, read=True,
              write=True, ttl=5, callback=None):
        """Grant Access on a Channel."""

        return self._pam_auth({
            "channel": channel,
            "auth": authkey,
            "r": read and 1 or 0,
            "w": write and 1 or 0,
            "ttl": ttl
        }, callback=callback)

    def revoke(self, channel, authkey=False, ttl=1, callback=None):
        """Revoke Access on a Channel."""

        return self._pam_auth({
            "channel": channel,
            "auth": authkey,
            "r": 0,
            "w": 0,
            "ttl": ttl
        }, callback=callback)

    def audit(self, channel=False, authkey=False, callback=None):
        return self._pam_auth({
            "channel": channel,
            "auth": authkey
        }, 1, callback=callback)

    def encrypt(self, message):
        if self.cipher_key:
            message = json.dumps(self.pc.encrypt(
                self.cipher_key, json.dumps(message)).replace('\n', ''))
        else:
            message = json.dumps(message)

        return message

    def decrypt(self, message):
        if self.cipher_key:
            message = self.pc.decrypt(self.cipher_key, message)

        return message

    def _return_wrapped_callback(self, callback=None):
        def _new_format_callback(response):
            if 'payload' in response:
                if (callback is not None):
                    callback({'message': response['message'],
                              'payload': response['payload']})
            else:
                if (callback is not None):
                    callback(response)
        if (callback is not None):
            return _new_format_callback
        else:
            return None

    def publish(channel, message, callback=None, error=None):
        """
        #**
        #* Publish
        #*
        #* Send a message to a channel.
        #*
        #* @param array args with channel and message.
        #* @return array success information.
        #**

        ## Publish Example
        info = pubnub.publish({
            'channel' : 'hello_world',
            'message' : {
                'some_text' : 'Hello my World'
            }
        })
        print(info)

        """

        message = self.encrypt(message)

        ## Send Message
        return self._request({"urlcomponents": [
            'publish',
            self.publish_key,
            self.subscribe_key,
            '0',
            channel,
            '0',
            message
        ], 'urlparams': {'auth': self.auth_key}},
            callback=self._return_wrapped_callback(callback),
            error=self._return_wrapped_callback(error))

    def presence(self, channel, callback, error=None):
        """
        #**
        #* presence
        #*
        #* This is BLOCKING.
        #* Listen for presence events on a channel.
        #*
        #* @param array args with channel and callback.
        #* @return false on fail, array on success.
        #**

        ## Presence Example
        def pres_event(message) :
            print(message)
            return True

        pubnub.presence({
            'channel'  : 'hello_world',
            'callback' : receive
        })
        """
        return self.subscribe({
            'channel': channel + '-pnpres',
            'subscribe_key': self.subscribe_key,
            'callback': self._return_wrapped_callback(callback)})

    def here_now(self, channel, callback, error=None):
        """
        #**
        #* Here Now
        #*
        #* Load current occupancy from a channel.
        #*
        #* @param array args with 'channel'.
        #* @return mixed false on fail, array on success.
        #*

        ## Presence Example
        here_now = pubnub.here_now({
            'channel' : 'hello_world',
        })
        print(here_now['occupancy'])
        print(here_now['uuids'])

        """

        ## Get Presence Here Now
        return self._request({"urlcomponents": [
            'v2', 'presence',
            'sub_key', self.subscribe_key,
            'channel', channel
        ], 'urlparams': {'auth': self.auth_key}},
            callback=self._return_wrapped_callback(callback),
            error=self._return_wrapped_callback(error))

    def history(self, channel, count=100, reverse=False,
                start=None, end=None, callback=None, error=None):
        """
        #**
        #* History
        #*
        #* Load history from a channel.
        #*

        ## History Example
        history = pubnub.detailedHistory({
            'channel' : 'hello_world',
            'count'   : 5
        })
        print(history)

        """

        params = dict()

        params['count'] = count
        params['reverse'] = reverse
        params['start'] = start
        params['end'] = end

        ## Get History
        return self._request({'urlcomponents': [
            'v2',
            'history',
            'sub-key',
            self.subscribe_key,
            'channel',
            channel,
        ], 'urlparams': {'auth': self.auth_key}},
            callback=self._return_wrapped_callback(callback),
            error=self._return_wrapped_callback(error))

    def time(self, callback=None):
        """
        #**
        #* Time
        #*
        #* Timestamp from PubNub Cloud.
        #*
        #* @return int timestamp.
        #*

        ## PubNub Server Time Example
        timestamp = pubnub.time()
        print(timestamp)

        """

        time = self._request({'urlcomponents': [
            'time',
            '0'
        ]}, callback)
        if time is not None:
            return time[0]

    def _encode(self, request):
        return [
            "".join([' ~`!@#$%^&*()+=[]\\{}|;\':",./<>?'.find(ch) > -1 and
                     hex(ord(ch)).replace('0x', '%').upper() or
                     ch for ch in list(bit)
                     ]) for bit in request]

    def getUrl(self, request):
        ## Build URL
        url = self.origin + '/' + "/".join([
            "".join([' ~`!@#$%^&*()+=[]\\{}|;\':",./<>?'.find(ch) > -1 and
                     hex(ord(ch)).replace('0x', '%').upper() or
                     ch for ch in list(bit)
                     ]) for bit in request["urlcomponents"]])
        if ("urlparams" in request):
            url = url + '?' + "&".join([x + "=" + str(y) for x, y in request[
                "urlparams"].items() if y is not None])
        return url


try:
    from hashlib import sha256
    digestmod = sha256
except ImportError:
    import Crypto.Hash.SHA256 as digestmod
    sha256 = digestmod.new
import hmac


class EmptyLock():
    def __enter__(self):
        pass

    def __exit__(self, a, b, c):
        pass

empty_lock = EmptyLock()


class PubnubCoreAsync(PubnubBase):

    def start(self):
        pass

    def stop(self):
        pass

    def __init__(
        self,
        publish_key,
        subscribe_key,
        secret_key=False,
        cipher_key=False,
        auth_key=None,
        ssl_on=False,
        origin='pubsub.pubnub.com',
        uuid=None,
        _tt_lock=empty_lock,
        _channel_list_lock=empty_lock
    ):
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
        self.timetoken = 0
        self.last_timetoken = 0
        self.version = '3.3.4'
        self.accept_encoding = 'gzip'
        self.SUB_RECEIVER = None
        self._connect = None
        self._tt_lock = _tt_lock
        self._channel_list_lock = _channel_list_lock
        self._connect = lambda: None

    def get_channel_list(self, channels):
        channel = ''
        first = True
        with self._channel_list_lock:
            for ch in channels:
                if not channels[ch]['subscribed']:
                    continue
                if not first:
                    channel += ','
                else:
                    first = False
                channel += ch
        return channel

    def get_channel_array(self):
        channels = self.subscriptions
        channel = []
        with self._channel_list_lock:
            for ch in channels:
                if not channels[ch]['subscribed']:
                    continue
                channel.append(ch)
        return channel

    def each(l, func):
        if func is None:
            return
        for i in l:
            func(i)

    def subscribe(self, channel, callback, error=None,
                  connect=None, disconnect=None, reconnect=None, sync=False):
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

        with self._tt_lock:
            self.last_timetoken = self.timetoken if self.timetoken != 0 \
                else self.last_timetoken
            self.timetoken = 0

        if sync is True and self.susbcribe_sync is not None:
            self.susbcribe_sync(args)
            return

        def _invoke(func, msg=None):
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
                            _invoke(chobj['connect'], chobj['name'])

        def _invoke_error(channel_list=None, err=None):
            if channel_list is None:
                for ch in self.subscriptions:
                    chobj = self.subscriptions[ch]
                    _invoke(chobj['error'], err)
            else:
                for ch in channel_list:
                    chobj = self.subscriptions[ch]
                    _invoke(chobj['error'], err)

        def _get_channel():
            for ch in self.subscriptions:
                chobj = self.subscriptions[ch]
                if chobj['subscribed'] is True:
                    return chobj

        ## New Channel?
        if not channel in self.subscriptions or \
                self.subscriptions[channel]['subscribed'] is False:
                with self._channel_list_lock:
                    self.subscriptions[channel] = {
                        'name': channel,
                        'first': False,
                        'connected': False,
                        'subscribed': True,
                        'callback': callback,
                        'connect': connect,
                        'disconnect': disconnect,
                        'reconnect': reconnect,
                        'error': error
                    }

        ## return if already connected to channel
        if channel in self.subscriptions and \
            'connected' in self.subscriptions[channel] and \
                self.subscriptions[channel]['connected'] is True:
                    _invoke(error, "Already Connected")
                    return

        ## SUBSCRIPTION RECURSION
        def _connect():

            self._reset_offline()

            def sub_callback(response):
                ## ERROR ?
                if not response or \
                    ('message' in response and
                        response['message'] == 'Forbidden'):
                            _invoke_error(response['payload'][
                                'channels'], response['message'])
                            _connect()
                            return

                _invoke_connect()

                with self._tt_lock:
                    self.timetoken = \
                        self.last_timetoken if self.timetoken == 0 and \
                        self.last_timetoken != 0 else response[1]
                    if len(response) > 2:
                        channel_list = response[2].split(',')
                        response_list = response[0]
                        for ch in enumerate(channel_list):
                            if ch[1] in self.subscriptions:
                                chobj = self.subscriptions[ch[1]]
                                _invoke(chobj['callback'],
                                        self.decrypt(response_list[ch[0]]))
                    else:
                        response_list = response[0]
                        chobj = _get_channel()
                        for r in response_list:
                            if chobj:
                                _invoke(chobj['callback'], self.decrypt(r))

                    _connect()

            channel_list = self.get_channel_list(self.subscriptions)
            if len(channel_list) <= 0:
                return

            ## CONNECT TO PUBNUB SUBSCRIBE SERVERS
            #try:
            self.SUB_RECEIVER = self._request({"urlcomponents": [
                'subscribe',
                self.subscribe_key,
                channel_list,
                '0',
                str(self.timetoken)
            ], "urlparams": {"uuid": self.uuid, "auth": self.auth_key}},
                sub_callback,
                sub_callback,
                single=True)
            '''
            except Exception as e:
                print(e)
                self.timeout(1, _connect)
                return
            '''

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

    def unsubscribe(self, channel):

        if channel in self.subscriptions is False:
            return False

        ## DISCONNECT
        with self._channel_list_lock:
            if channel in self.subscriptions:
                self.subscriptions[channel]['connected'] = 0
                self.subscriptions[channel]['subscribed'] = False
                self.subscriptions[channel]['timetoken'] = 0
                self.subscriptions[channel]['first'] = False
        self.CONNECT()


try:
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

    from twisted.python.compat import (
        _PY3, unicode, intToBytes, networkString, nativeString)

    pnconn_pool = HTTPConnectionPool(reactor, persistent=True)
    pnconn_pool.maxPersistentPerHost = 100000
    pnconn_pool.cachedConnectionTimeout = 15
    pnconn_pool.retryAutomatically = True
except ImportError:
    pass

from hashlib import sha256
import time
import json

import traceback




class PubnubTwisted(PubnubCoreAsync):

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


import tornado.httpclient

try:
    from hashlib import sha256
    digestmod = sha256
except ImportError:
    import Crypto.Hash.SHA256 as digestmod
    sha256 = digestmod.new

try:
    import hmac
    import tornado.ioloop
    from tornado.stack_context import ExceptionStackContext
    ioloop = tornado.ioloop.IOLoop.instance()
except ImportError:
    pass


class PubnubTornado(PubnubCoreAsync):

    def stop(self):
        ioloop.stop()

    def start(self):
        ioloop.start()

    def timeout(self, delay, callback):
        ioloop.add_timeout(time.time() + float(delay), callback)

    def __init__(
        self,
        publish_key,
        subscribe_key,
        secret_key=False,
        cipher_key=False,
        auth_key=False,
        ssl_on=False,
        origin='pubsub.pubnub.com'
    ):
        super(PubnubTornado, self).__init__(
            publish_key=publish_key,
            subscribe_key=subscribe_key,
            secret_key=secret_key,
            cipher_key=cipher_key,
            auth_key=auth_key,
            ssl_on=ssl_on,
            origin=origin,
        )
        self.headers = {}
        self.headers['User-Agent'] = 'Python-Tornado'
        self.headers['Accept-Encoding'] = self.accept_encoding
        self.headers['V'] = self.version
        self.http = tornado.httpclient.AsyncHTTPClient(max_clients=1000)
        self.id = None

    def _request(self, request, callback=None, error=None,
                 single=False, read_timeout=5, connect_timeout=5):

        def _invoke(func, data):
            if func is not None:
                func(data)

        url = self.getUrl(request)
        request = tornado.httpclient.HTTPRequest(
            url, 'GET',
            self.headers,
            connect_timeout=connect_timeout,
            request_timeout=read_timeout)
        if single is True:
            id = time.time()
            self.id = id

        def responseCallback(response):
            if single is True:
                if not id == self.id:
                    return None

            body = response._get_body()

            if body is None:
                return

            def handle_exc(*args):
                return True
            if response.error is not None:
                with ExceptionStackContext(handle_exc):
                    if response.code in [403, 401]:
                        response.rethrow()
                    else:
                        _invoke(error, {"message": response.reason})
                    return

            try:
                data = json.loads(body)
            except TypeError as e:
                try:
                    data = json.loads(body.decode("utf-8"))
                except ValueError as ve:
                    _invoke(error, {'error': 'json decode error'})

            if 'error' in data and 'status' in data and 'status' != 200:
                _invoke(error, data)
            else:
                _invoke(callback, data)

        self.http.fetch(
            request=request,
            callback=responseCallback
        )

        def abort():
            pass

        return abort

