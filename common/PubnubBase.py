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
except:
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

        message = self.encrypt(args['message'])

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
        channel = str(args['channel'])

        callback = args['callback'] if 'callback' in args else None
        error = args['error'] if 'error' in args else None

        ## Fail if bad input.
        if not channel:
            raise Exception('Missing Channel')
            return False

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
