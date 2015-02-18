
## www.pubnub.com - PubNub Real-time push service in the cloud.
# coding=utf8

## PubNub Real-time Push APIs and Notifications Framework
## Copyright (c) 2014-15 Stephen Blum
## http://www.pubnub.com/

## -----------------------------------
## PubNub 3.7.1 Real-time Push Cloud API
## -----------------------------------


try:
    import json
except ImportError:
    import simplejson as json

import time
import hashlib
import uuid as uuid_lib
import random
import sys
from base64 import urlsafe_b64encode
from base64 import encodestring, decodestring
import hmac
from Crypto.Cipher import AES
from Crypto.Hash import MD5


try:
    from hashlib import sha256
    digestmod = sha256
except ImportError:
    import Crypto.Hash.SHA256 as digestmod
    sha256 = digestmod.new


##### vanilla python imports #####
try:
    from urllib.parse import quote
except ImportError:
    from urllib2 import quote
try:
    import urllib.request
except ImportError:
    import urllib2

try:
    import requests
    from requests.adapters import HTTPAdapter
except ImportError:
    pass

import socket
import sys
import threading
from threading import current_thread

try:
    import urllib3.HTTPConnection
    default_socket_options = urllib3.HTTPConnection.default_socket_options
except:
    default_socket_options = []

default_socket_options += [
    # Enable TCP keepalive
    (socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)
]

if sys.platform.startswith("linux"):
    default_socket_options += [
        # Send first keepalive packet 200 seconds after last data packet
        (socket.IPPROTO_TCP, socket.TCP_KEEPIDLE, 200),
        # Resend keepalive packets every second, when unanswered
        (socket.IPPROTO_TCP, socket.TCP_KEEPINTVL, 1),
        # Close the socket after 5 unanswered keepalive packets
        (socket.IPPROTO_TCP, socket.TCP_KEEPCNT, 5)
    ]
elif sys.platform.startswith("darwin"):
    # From /usr/include/netinet/tcp.h
    socket.TCP_KEEPALIVE = 0x10 # idle time used when SO_KEEPALIVE is enabled

    default_socket_options += [
        # Send first keepalive packet 200 seconds after last data packet
        (socket.IPPROTO_TCP, socket.TCP_KEEPALIVE, 200),
        # Resend keepalive packets every second, when unanswered
        (socket.IPPROTO_TCP, socket.TCP_KEEPINTVL, 1),
        # Close the socket after 5 unanswered keepalive packets
        (socket.IPPROTO_TCP, socket.TCP_KEEPCNT, 5)
    ]
"""
# The Windows code is currently untested
elif sys.platform.startswith("win"):
    import struct
    from urllib3.connectionpool import HTTPConnectionPool, HTTPSConnectionPool

    def patch_socket_keepalive(conn):
        conn.sock.ioctl(socket.SIO_KEEPALIVE_VALS, (
            # Enable TCP keepalive
            1,
            # Send first keepalive packet 200 seconds after last data packet
            200,
            # Resend keepalive packets every second, when unanswered
            1
        ))

    class PubnubHTTPConnectionPool(HTTPConnectionPool):
        def _validate_conn(self, conn):
            super(PubnubHTTPConnectionPool, self)._validate_conn(conn)

    class PubnubHTTPSConnectionPool(HTTPSConnectionPool):
        def _validate_conn(self, conn):
            super(PubnubHTTPSConnectionPool, self)._validate_conn(conn)

    import urllib3.poolmanager
    urllib3.poolmanager.pool_classes_by_scheme = {
        'http'  : PubnubHTTPConnectionPool,
        'https' : PubnubHTTPSConnectionPool
    }
"""

##################################


##### Tornado imports and globals #####
try:
    import tornado.httpclient
    import tornado.ioloop
    from tornado.stack_context import ExceptionStackContext
    ioloop = tornado.ioloop.IOLoop.instance()
except ImportError:
    pass

#######################################


##### Twisted imports and globals #####
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
except ImportError:
    pass


#######################################


def get_data_for_user(data):
    try:
        if 'message' in data and 'payload' in data:
            return {'message': data['message'], 'payload': data['payload']}
        else:
            return data
    except TypeError:
        return data


class PubnubCrypto2():

    def pad(self, msg, block_size=16):

        padding = block_size - (len(msg) % block_size)
        return msg + chr(padding) * padding

    def depad(self, msg):

        return msg[0:-ord(msg[-1])]

    def getSecret(self, key):

        return hashlib.sha256(key).hexdigest()

    def encrypt(self, key, msg):
        secret = self.getSecret(key)
        Initial16bytes = '0123456789012345'
        cipher = AES.new(secret[0:32], AES.MODE_CBC, Initial16bytes)
        enc = encodestring(cipher.encrypt(self.pad(msg)))
        return enc

    def decrypt(self, key, msg):

        try:
            secret = self.getSecret(key)
            Initial16bytes = '0123456789012345'
            cipher = AES.new(secret[0:32], AES.MODE_CBC, Initial16bytes)
            plain = self.depad(cipher.decrypt(decodestring(msg)))
        except:
            return msg
        try:
            return eval(plain)
        except SyntaxError:
            return plain

class PubnubCrypto3():

    def pad(self, msg, block_size=16):

        padding = block_size - (len(msg) % block_size)
        return msg + (chr(padding) * padding).encode('utf-8')

    def depad(self, msg):

        return msg[0:-ord(msg[-1])]

    def getSecret(self, key):

        return hashlib.sha256(key.encode("utf-8")).hexdigest()

    def encrypt(self, key, msg):

        secret = self.getSecret(key)
        Initial16bytes = '0123456789012345'
        cipher = AES.new(secret[0:32], AES.MODE_CBC, Initial16bytes)
        return encodestring(
            cipher.encrypt(self.pad(msg.encode('utf-8')))).decode('utf-8')

    def decrypt(self, key, msg):

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
        uuid=None
    ):
        """Pubnub Class

        Provides methods to communicate with Pubnub cloud

        Attributes:
            publish_key: Publish Key
            subscribe_key: Subscribe Key
            secret_key: Secret Key
            cipher_key: Cipher Key
            auth_key: Auth Key (used with Pubnub Access Manager i.e. PAM)
            ssl: SSL enabled ? 
            origin: Origin
        """

        self.origin = origin
        self.version = '3.7.1'
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

        self.uuid = uuid or str(uuid_lib.uuid4())

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
            raise AttributeError("uuid must be a string")

    def _pam_sign(self, msg):

        return urlsafe_b64encode(hmac.new(
            self.secret_key.encode("utf-8"),
            msg.encode("utf-8"),
            sha256
        ).digest())

    def set_u(self, u=False):
        self.u = u

    def _pam_auth(self, query, apicode=0, callback=None, error=None):

        if 'timestamp' not in query:
            query['timestamp'] = int(time.time())

        ## Global Grant?
        if 'auth' in query and not query['auth']:
            del query['auth']

        if 'channel' in query and not query['channel']:
            del query['channel']

        if 'channel-group' in query and not query['channel-group']:
            del query['channel-group']


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
            self._return_wrapped_callback(callback),
            self._return_wrapped_callback(error))

    def get_origin(self):
        return self.origin

    def set_auth_key(self, auth_key):
        self.auth_key = auth_key

    def get_auth_key(self):
        return self.auth_key

    def grant(self, channel=None, channel_group=None, auth_key=False, read=False,
              write=False, manage=False, ttl=5, callback=None, error=None):
        """Method for granting permissions.

        This function establishes subscribe and/or write permissions for
        PubNub Access Manager (PAM) by setting the read or write attribute
        to true. A grant with read or write set to false (or not included)
        will revoke any previous grants with read or write set to true.

        Permissions can be applied to any one of three levels:
            1. Application level privileges are based on subscribe_key applying to all associated channels.
            2. Channel level privileges are based on a combination of subscribe_key and channel name.
            3. User level privileges are based on the combination of subscribe_key, channel and auth_key.

        Args:
            channel:    (string) (optional)
                        Specifies channel name to grant permissions to.
                        If channel/channel_group is not specified, the grant applies to all
                        channels associated with the subscribe_key. If auth_key
                        is not specified, it is possible to grant permissions to
                        multiple channels simultaneously by specifying the channels
                        as a comma separated list.
            channel_group:    (string) (optional)
                        Specifies channel group name to grant permissions to.
                        If channel/channel_group is not specified, the grant applies to all
                        channels associated with the subscribe_key. If auth_key
                        is not specified, it is possible to grant permissions to
                        multiple channel groups simultaneously by specifying the channel groups
                        as a comma separated list.

            auth_key:   (string) (optional) 
                        Specifies auth_key to grant permissions to.
                        It is possible to specify multiple auth_keys as comma
                        separated list in combination with a single channel name.
                        If auth_key is provided as the special-case value "null" 
                        (or included in a comma-separated list, eg. "null,null,abc"), 
                        a new auth_key will be generated and returned for each "null" value.

            read:       (boolean) (default: True)
                        Read permissions are granted by setting to True.
                        Read permissions are removed by setting to False.

            write:      (boolean) (default: True)
                        Write permissions are granted by setting to true.
                        Write permissions are removed by setting to false.
            manage:      (boolean) (default: True)
                        Manage permissions are granted by setting to true.
                        Manage permissions are removed by setting to false.

            ttl:        (int) (default: 1440 i.e 24 hrs)
                        Time in minutes for which granted permissions are valid.
                        Max is 525600 , Min is 1.
                        Setting ttl to 0 will apply the grant indefinitely.

            callback:   (function) (optional)
                        A callback method can be passed to the method.
                        If set, the api works in async mode. 
                        Required argument when working with twisted or tornado 

            error:      (function) (optional)
                        An error method can be passed to the method.
                        If set, the api works in async mode. 
                        Required argument when working with twisted or tornado .

        Returns:
            Returns a dict in sync mode i.e. when callback argument is not given
            The dict returned contains values with keys 'message' and 'payload'

            Sample Response:
            {
                "message":"Success",
                "payload":{
                    "ttl":5,
                    "auths":{
                        "my_ro_authkey":{"r":1,"w":0}
                    },
                    "subscribe_key":"my_subkey",
                    "level":"user",
                    "channel":"my_channel"
                }
            }
        """

        return self._pam_auth({
            'channel'   : channel,
            'channel-group'   : channel_group,
            'auth'      : auth_key,
            'r'         : read and 1 or 0,
            'w'         : write and 1 or 0,
            'm'         : manage and 1 or 0,
            'ttl'       : ttl,
            'pnsdk'     : self.pnsdk
        }, callback=callback, error=error)

    def revoke(self, channel=None, channel_group=None, auth_key=None, ttl=1, callback=None, error=None):
        """Method for revoking permissions.

        Args:
            channel:    (string) (optional)
                        Specifies channel name to revoke permissions to.
                        If channel/channel_group is not specified, the revoke applies to all
                        channels associated with the subscribe_key. If auth_key
                        is not specified, it is possible to grant permissions to
                        multiple channels simultaneously by specifying the channels
                        as a comma separated list.

            channel_group:    (string) (optional)
                        Specifies channel group name to revoke permissions to.
                        If channel/channel_group is not specified, the grant applies to all
                        channels associated with the subscribe_key. If auth_key
                        is not specified, it is possible to revoke permissions to
                        multiple channel groups simultaneously by specifying the channel groups
                        as a comma separated list.

            auth_key:   (string) (optional) 
                        Specifies auth_key to revoke permissions to.
                        It is possible to specify multiple auth_keys as comma
                        separated list in combination with a single channel name.
                        If auth_key is provided as the special-case value "null" 
                        (or included in a comma-separated list, eg. "null,null,abc"), 
                        a new auth_key will be generated and returned for each "null" value.

            ttl:        (int) (default: 1440 i.e 24 hrs)
                        Time in minutes for which granted permissions are valid.
                        Max is 525600 , Min is 1.
                        Setting ttl to 0 will apply the grant indefinitely.

            callback:   (function) (optional)
                        A callback method can be passed to the method.
                        If set, the api works in async mode. 
                        Required argument when working with twisted or tornado 

            error:      (function) (optional)
                        An error method can be passed to the method.
                        If set, the api works in async mode. 
                        Required argument when working with twisted or tornado .

        Returns:
            Returns a dict in sync mode i.e. when callback argument is not given
            The dict returned contains values with keys 'message' and 'payload'

            Sample Response:
            {
                "message":"Success",
                "payload":{
                    "ttl":5,
                    "auths":{
                        "my_authkey":{"r":0,"w":0}
                    },
                    "subscribe_key":"my_subkey",
                    "level":"user",
                    "channel":"my_channel"
                }
            }

        """

        return self._pam_auth({
            'channel'   : channel,
            'channel-group' : channel_group,
            'auth'      : auth_key,
            'r'         : 0,
            'w'         : 0,
            'ttl'       : ttl,
            'pnsdk'     : self.pnsdk
        }, callback=callback, error=error)

    def audit(self, channel=None, channel_group=None, auth_key=None, callback=None, error=None):
        """Method for fetching permissions from pubnub servers.

        This method provides a mechanism to reveal existing PubNub Access Manager attributes
        for any combination of subscribe_key, channel and auth_key.

        Args:
            channel:    (string) (optional)
                        Specifies channel name to return PAM 
                        attributes optionally in combination with auth_key.
                        If channel/channel_group is not specified, results for all channels
                        associated with subscribe_key are returned.
                        If auth_key is not specified, it is possible to return
                        results for a comma separated list of channels.
            channel_group:    (string) (optional)
                        Specifies channel group name to return PAM 
                        attributes optionally in combination with auth_key.
                        If channel/channel_group is not specified, results for all channels
                        associated with subscribe_key are returned.
                        If auth_key is not specified, it is possible to return
                        results for a comma separated list of channels.

            auth_key:   (string) (optional) 
                        Specifies the auth_key to return PAM attributes for.
                        If only a single channel is specified, it is possible to return
                        results for a comma separated list of auth_keys.

            callback:   (function) (optional) 
                        A callback method can be passed to the method.
                        If set, the api works in async mode. 
                        Required argument when working with twisted or tornado 

            error:      (function) (optional)
                        An error method can be passed to the method.
                        If set, the api works in async mode. 
                        Required argument when working with twisted or tornado .

        Returns:
            Returns a dict in sync mode i.e. when callback argument is not given
            The dict returned contains values with keys 'message' and 'payload'

            Sample Response
            {
                "message":"Success",
                "payload":{
                    "channels":{
                        "my_channel":{
                            "auths":{"my_ro_authkey":{"r":1,"w":0},
                            "my_rw_authkey":{"r":0,"w":1},
                            "my_admin_authkey":{"r":1,"w":1}
                        }
                    }
                },
            }

        Usage:

             pubnub.audit ('my_channel');  # Sync Mode 

        """

        return self._pam_auth({
            'channel'   : channel,
            'channel-group' : channel_group,
            'auth'      : auth_key,
            'pnsdk'     : self.pnsdk
        }, 1, callback=callback, error=error)

    def encrypt(self, message):
        """Method for encrypting data.

        This method takes plaintext as input and returns encrypted data.
        This need not be called directly as enncryption/decryption is
        taken care of transparently by Pubnub class if cipher key is 
        provided at time of initializing pubnub object

        Args:
            message: Message to be encrypted.

        Returns:
            Returns encrypted message if cipher key is set
        """
        if self.cipher_key:
            message = json.dumps(self.pc.encrypt(
                self.cipher_key, json.dumps(message)).replace('\n', ''))
        else:
            message = json.dumps(message)

        return message

    def decrypt(self, message):
        """Method for decrypting data.

        This method takes ciphertext as input and returns decrypted data.
        This need not be called directly as enncryption/decryption is
        taken care of transparently by Pubnub class if cipher key is 
        provided at time of initializing pubnub object

        Args:
            message: Message to be decrypted.

        Returns:
            Returns decrypted message if cipher key is set
        """
        if self.cipher_key:
            message = self.pc.decrypt(self.cipher_key, message)

        return message

    def _return_wrapped_callback(self, callback=None):
        def _new_format_callback(response):
            if 'payload' in response:
                if (callback is not None):
                    callback_data = dict()
                    callback_data['payload'] = response['payload']

                    if 'message' in response:
                        callback_data['message'] = response['message']
                        
                    callback(callback_data)
            else:
                if (callback is not None):
                    callback(response)
        if (callback is not None):
            return _new_format_callback
        else:
            return None

    def leave_channel(self, channel, callback=None, error=None):
        ## Send leave
        return self._request({"urlcomponents": [
            'v2', 'presence',
            'sub_key',
            self.subscribe_key,
            'channel',
            channel,
            'leave'
        ], 'urlparams': {'auth': self.auth_key, 'pnsdk' : self.pnsdk, "uuid": self.uuid,}},
            callback=self._return_wrapped_callback(callback),
            error=self._return_wrapped_callback(error))

    def leave_group(self, channel_group, callback=None, error=None):
        ## Send leave
        return self._request({"urlcomponents": [
            'v2', 'presence',
            'sub_key',
            self.subscribe_key,
            'channel',
            ',',
            'leave'
        ], 'urlparams': {'auth': self.auth_key, 'pnsdk' : self.pnsdk, 'channel-group' : channel_group, "uuid": self.uuid,}},
            callback=self._return_wrapped_callback(callback),
            error=self._return_wrapped_callback(error))


    def publish(self, channel, message, callback=None, error=None):
        """Publishes data on a channel.

        The publish() method is used to send a message to all subscribers of a channel.
        To publish a message you must first specify a valid publish_key at initialization.
        A successfully published message is replicated across the PubNub Real-Time Network
        and sent simultaneously to all subscribed clients on a channel.
            Messages in transit can be secured from potential eavesdroppers with SSL/TLS by
        setting ssl to True during initialization.

        Published messages can also be encrypted with AES-256 simply by specifying a cipher_key
        during initialization.

        Args:
            channel:    (string)
                        Specifies channel name to publish messages to.
            message:    (string/int/double/dict/list)
                        Message to be published
            callback:   (optional)
                        A callback method can be passed to the method.
                        If set, the api works in async mode. 
                        Required argument when working with twisted or tornado
            error:      (optional)
                        An error method can be passed to the method.
                        If set, the api works in async mode. 
                        Required argument when working with twisted or tornado

        Returns:
            Sync Mode  : list
            Async Mode : None

            The function returns the following formatted response:

                [ Number, "Status", "Time Token"]
            
            The output below demonstrates the response to a successful call:

                [1,"Sent","13769558699541401"]

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
        ], 'urlparams': {'auth': self.auth_key, 'pnsdk' : self.pnsdk}},
            callback=self._return_wrapped_callback(callback),
            error=self._return_wrapped_callback(error))

    def presence(self, channel, callback, error=None):
        """Subscribe to presence events on a channel.
           
           Only works in async mode

        Args:
            channel: Channel name ( string ) on which to listen for events
            callback: A callback method should be passed as parameter.
                      If passed, the api works in async mode. 
                      Required argument when working with twisted or tornado .
            error: Optional variable. An error method can be passed as parameter.
                      If set, the api works in async mode. 

        Returns:
            None
        """
        return self.subscribe(channel+'-pnpres', callback=callback)

    def presence_group(self, channel_group, callback, error=None):
        """Subscribe to presence events on a channel group.
           
           Only works in async mode

        Args:
            channel_group: Channel group name ( string )
            callback: A callback method should be passed to the method.
                      If passed, the api works in async mode. 
                      Required argument when working with twisted or tornado .
            error: Optional variable. An error method can be passed as parameter.
                      If passed, the api works in async mode. 

        Returns:
            None
        """
        return self.subscribe_group(channel_group+'-pnpres', callback=callback)

    def here_now(self, channel, callback=None, error=None):
        """Get here now data.

        You can obtain information about the current state of a channel including
        a list of unique user-ids currently subscribed to the channel and the total
        occupancy count of the channel by calling the here_now() function in your 
        application.


        Args:
            channel:    (string) (optional)
                        Specifies the channel name to return occupancy results.
                        If channel is not provided, here_now will return data for all channels.

            callback:   (optional)
                        A callback method should be passed to the method.
                        If set, the api works in async mode. 
                        Required argument when working with twisted or tornado .

            error:      (optional)
                        Optional variable. An error method can be passed to the method.
                        If set, the api works in async mode. 
                        Required argument when working with twisted or tornado .

        Returns:
            Sync  Mode: list
            Async Mode: None

            Response Format:

            The here_now() method returns a list of uuid s currently subscribed to the channel.

            uuids:["String","String", ... ,"String"] - List of UUIDs currently subscribed to the channel.

            occupancy: Number - Total current occupancy of the channel.

            Example Response:
            {
                occupancy: 4,
                uuids: [
                    '123123234t234f34fq3dq',
                    '143r34f34t34fq34q34q3',
                    '23f34d3f4rq34r34rq23q',
                    'w34tcw45t45tcw435tww3',
                ]
            }
        """

        urlcomponents = [
            'v2', 'presence',
            'sub_key', self.subscribe_key
        ]

        if (channel is not None and len(channel) > 0):
            urlcomponents.append('channel')
            urlcomponents.append(channel)

        ## Get Presence Here Now
        return self._request({"urlcomponents": urlcomponents,
            'urlparams': {'auth': self.auth_key, 'pnsdk' : self.pnsdk}},
            callback=self._return_wrapped_callback(callback),
            error=self._return_wrapped_callback(error))


    def history(self, channel, count=100, reverse=False,
                start=None, end=None, callback=None, error=None):
        """This method fetches historical messages of a channel.

        PubNub Storage/Playback Service provides real-time access to an unlimited
        history for all messages published to PubNub. Stored messages are replicated
        across multiple availability zones in several geographical data center
        locations. Stored messages can be encrypted with AES-256 message encryption
        ensuring that they are not readable while stored on PubNub's network.

        It is possible to control how messages are returned and in what order,
        for example you can:

            Return messages in the order newest to oldest (default behavior).

            Return messages in the order oldest to newest by setting reverse to true.

            Page through results by providing a start or end time token.

            Retrieve a "slice" of the time line by providing both a start and end time token.

            Limit the number of messages to a specific quantity using the count parameter.



        Args:
            channel:    (string)
                        Specifies channel to return history messages from

            count:      (int) (default: 100)
                        Specifies the number of historical messages to return

            callback:   (optional)
                        A callback method should be passed to the method.
                        If set, the api works in async mode. 
                        Required argument when working with twisted or tornado .

            error:      (optional)
                        An error method can be passed to the method.
                        If set, the api works in async mode. 
                        Required argument when working with twisted or tornado .

        Returns:
            Returns a list in sync mode i.e. when callback argument is not given

            Sample Response:
                [["Pub1","Pub2","Pub3","Pub4","Pub5"],13406746729185766,13406746845892666]
        """

        params = dict()

        params['count'] = count
        params['reverse'] = reverse
        params['start'] = start
        params['end'] = end
        params['auth_key'] = self.auth_key
        params['pnsdk'] = self.pnsdk

        ## Get History
        return self._request({'urlcomponents': [
            'v2',
            'history',
            'sub-key',
            self.subscribe_key,
            'channel',
            channel,
        ], 'urlparams': params},
            callback=self._return_wrapped_callback(callback),
            error=self._return_wrapped_callback(error))

    def time(self, callback=None):
        """This function will return a 17 digit precision Unix epoch.

        Args:

            callback:   (optional)
                        A callback method should be passed to the method.
                        If set, the api works in async mode. 
                        Required argument when working with twisted or tornado .

        Returns:
            Returns a 17 digit number in sync mode i.e. when callback argument is not given

            Sample:
                13769501243685161
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
 
        if self.u is True and "urlparams" in request:
            request['urlparams']['u'] = str(random.randint(1, 100000000000))
        ## Build URL
        url = self.origin + '/' + "/".join([
            "".join([' ~`!@#$%^&*()+=[]\\{}|;\':",./<>?'.find(ch) > -1 and
                     hex(ord(ch)).replace('0x', '%').upper() or
                     ch for ch in list(bit)
                     ]) for bit in request["urlcomponents"]])
        if ("urlparams" in request):
            url = url + '?' + "&".join([x + "=" + str(y) for x, y in request[
                "urlparams"].items() if y is not None and len(str(y)) > 0])

        return url

    def _channel_registry(self, url=None, params=None, callback=None, error=None):

        if (params is None):
            params = dict()

        urlcomponents = ['v1', 'channel-registration', 'sub-key', self.subscribe_key ]

        if (url is not None):
            urlcomponents += url

        params['auth']  = self.auth_key
        params['pnsdk'] = self.pnsdk

        ## Get History
        return self._request({'urlcomponents': urlcomponents, 'urlparams': params},
            callback=self._return_wrapped_callback(callback),
            error=self._return_wrapped_callback(error))

    def _channel_group(self, channel_group=None, channels=None, cloak=None,mode='add', callback=None, error=None):
        params = dict()
        url = []
        namespace = None

        if (channel_group is not None and len(channel_group) > 0):
            ns_ch_a = channel_group.split(':')

            if len(ns_ch_a) > 1:
                namespace = None if ns_ch_a[0] == '*' else ns_ch_a[0]
                channel_group = ns_ch_a[1]
            else:
                channel_group = ns_ch_a[0]

        if (namespace is not None):
            url.append('namespace')
            url.append(self._encode(namespace))

        url.append('channel-group')

        if channel_group is not None and channel_group != '*':
            url.append(channel_group)

        if (channels is not None):
            if (type(channels) is list):
                channels = ','.join(channels)
            params[mode] = channels
            #params['cloak'] = 'true' if CLOAK is True else 'false'
        else:
            if mode == 'remove':
                url.append('remove')

        return self._channel_registry(url=url, params=params, callback=callback, error=error)


    def channel_group_list_namespaces(self, callback=None, error=None):
        """Get list of namespaces.

        You can obtain list of namespaces for the subscribe key associated with PubNub
        object using this method.


        Args:
            callback:   (optional)
                        A callback method should be passed to the method.
                        If set, the api works in async mode. 
                        Required argument when working with twisted or tornado.

            error:      (optional)
                        Optional variable. An error method can be passed to the method.
                        If set, the api works in async mode. 
                        Required argument when working with twisted or tornado.

        Returns:
            Sync  Mode: dict
            channel_group_list_namespaces method returns a dict which contains list of namespaces
            in payload field
            {
                u'status': 200,
                u'payload': {
                    u'sub_key': u'demo',
                    u'namespaces': [u'dev', u'foo']
                }, 
                u'service': u'channel-registry',
                u'error': False
            }

            Async Mode: None (callback gets the response as parameter)

            Response Format:

            The callback passed to channel_group_list_namespaces gets the a dict containing list of namespaces
            under payload field

            {
                u'payload': {
                    u'sub_key': u'demo',
                    u'namespaces': [u'dev', u'foo']
                }
            }

            namespaces is the list of namespaces for the given subscribe key


        """

        url = ['namespace']
        return self._channel_registry(url=url, callback=callback, error=error)

    def channel_group_remove_namespace(self, namespace, callback=None, error=None):
        """Remove a namespace.

        A namespace can be deleted using this method.


        Args:
            namespace:  (string) namespace to be deleted
            callback:   (optional)
                        A callback method should be passed to the method.
                        If set, the api works in async mode. 
                        Required argument when working with twisted or tornado .

            error:      (optional)
                        Optional variable. An error method can be passed to the method.
                        If set, the api works in async mode. 
                        Required argument when working with twisted or tornado .

        Returns:
            Sync  Mode: dict
            channel_group_remove_namespace method returns a dict indicating status of the request

            {
                u'status': 200,
                u'message': 'OK', 
                u'service': u'channel-registry',
                u'error': False
            }

            Async Mode: None ( callback gets the response as parameter )

            Response Format:

            The callback passed to channel_group_list_namespaces gets the a dict indicating status of the request

            {
                u'status': 200,
                u'message': 'OK', 
                u'service': u'channel-registry',
                u'error': False
            }

        """
        url = ['namespace', self._encode(namespace), 'remove']
        return self._channel_registry(url=url, callback=callback, error=error)

    def channel_group_list_groups(self, namespace=None, callback=None, error=None):
        """Get list of groups.

        Using this method, list of groups for the subscribe key associated with PubNub
        object, can be obtained. If namespace is provided, groups within the namespace
        only are listed

        Args:
            namespace:  (string) (optional) namespace
            callback:   (optional)
                        A callback method should be passed to the method.
                        If set, the api works in async mode. 
                        Required argument when working with twisted or tornado .

            error:      (optional)
                        Optional variable. An error method can be passed to the method.
                        If set, the api works in async mode. 
                        Required argument when working with twisted or tornado .

        Returns:
            Sync  Mode: dict
            channel_group_list_groups method returns a dict which contains list of groups
            in payload field
            {
                u'status': 200,
                u'payload': {"namespace": "dev", "groups": ["abcd"]}, 
                u'service': u'channel-registry',
                u'error': False
            }

            Async Mode: None ( callback gets the response as parameter )

            Response Format:

            The callback passed to channel_group_list_namespaces gets the a dict containing list of groups
            under payload field

            {
                u'payload': {"namespace": "dev", "groups": ["abcd"]}
            }



        """

        if (namespace is not None and len(namespace) > 0):
            channel_group = namespace + ':*'
        else:
            channel_group = '*:*'

        return self._channel_group(channel_group=channel_group, callback=callback, error=error)

    def channel_group_list_channels(self, channel_group, callback=None, error=None):
        """Get list of channels for a group.

        Using this method, list of channels for a group, can be obtained. 

        Args:
            channel_group: (string) (optional) 
                        Channel Group name. It can also contain namespace.
                        If namespace is also specified, then the parameter
                        will be in format namespace:channel_group

            callback:   (optional)
                        A callback method should be passed to the method.
                        If set, the api works in async mode. 
                        Required argument when working with twisted or tornado.

            error:      (optional)
                        Optional variable. An error method can be passed to the method.
                        If set, the api works in async mode. 
                        Required argument when working with twisted or tornado.

        Returns:
            Sync  Mode: dict
            channel_group_list_channels method returns a dict which contains list of channels
            in payload field
            {
                u'status': 200,
                u'payload': {"channels": ["hi"], "group": "abcd"}, 
                u'service': u'channel-registry',
                u'error': False
            }

            Async Mode: None ( callback gets the response as parameter )

            Response Format:

            The callback passed to channel_group_list_channels gets the a dict containing list of channels
            under payload field

            {
                u'payload': {"channels": ["hi"], "group": "abcd"}
            }


        """
        return self._channel_group(channel_group=channel_group, callback=callback, error=error)

    def channel_group_add_channel(self, channel_group, channel, callback=None, error=None):
        """Add a channel to group.

        A channel can be added to group using this method.


        Args:
            channel_group:  (string) 
                        Channel Group name. It can also contain namespace.
                        If namespace is also specified, then the parameter
                        will be in format namespace:channel_group
            channel:        (string)
                            Can be a channel name, a list of channel names,
                            or a comma separated list of channel names
            callback:       (optional)
                            A callback method should be passed to the method.
                            If set, the api works in async mode. 
                            Required argument when working with twisted or tornado.

            error:      (optional)
                        Optional variable. An error method can be passed to the method.
                        If set, the api works in async mode. 
                        Required argument when working with twisted or tornado.

        Returns:
            Sync  Mode: dict
            channel_group_add_channel method returns a dict indicating status of the request

            {
                u'status': 200,
                u'message': 'OK', 
                u'service': u'channel-registry',
                u'error': False
            }

            Async Mode: None ( callback gets the response as parameter )

            Response Format:

            The callback passed to channel_group_add_channel gets the a dict indicating status of the request

            {
                u'status': 200,
                u'message': 'OK', 
                u'service': u'channel-registry',
                u'error': False
            }

        """

        return self._channel_group(channel_group=channel_group, channels=channel, mode='add', callback=callback, error=error)

    def channel_group_remove_channel(self, channel_group, channel, callback=None, error=None):
        """Remove channel.

        A channel can be removed from a group method.


        Args:
            channel_group:  (string)
                        Channel Group name. It can also contain namespace.
                        If namespace is also specified, then the parameter
                        will be in format namespace:channel_group
            channel:        (string)
                            Can be a channel name, a list of channel names,
                            or a comma separated list of channel names
            callback:   (optional)
                        A callback method should be passed to the method.
                        If set, the api works in async mode. 
                        Required argument when working with twisted or tornado .

            error:      (optional)
                        Optional variable. An error method can be passed to the method.
                        If set, the api works in async mode. 
                        Required argument when working with twisted or tornado .

        Returns:
            Sync  Mode: dict
            channel_group_remove_channel method returns a dict indicating status of the request

            {
                u'status': 200,
                u'message': 'OK', 
                u'service': u'channel-registry',
                u'error': False
            }

            Async Mode: None ( callback gets the response as parameter )

            Response Format:

            The callback passed to channel_group_remove_channel gets the a dict indicating status of the request

            {
                u'status': 200,
                u'message': 'OK', 
                u'service': u'channel-registry',
                u'error': False
            }

        """

        return self._channel_group(channel_group=channel_group, channels=channel, mode='remove', callback=callback, error=error)

    def channel_group_remove_group(self, channel_group, callback=None, error=None):
        """Remove channel group.

        A channel group can be removed using this method.


        Args:
            channel_group:  (string)
                        Channel Group name. It can also contain namespace.
                        If namespace is also specified, then the parameter
                        will be in format namespace:channel_group
            callback:   (optional)
                        A callback method should be passed to the method.
                        If set, the api works in async mode. 
                        Required argument when working with twisted or tornado.

            error:      (optional)
                        Optional variable. An error method can be passed to the method.
                        If set, the api works in async mode. 
                        Required argument when working with twisted or tornado.

        Returns:
            Sync  Mode: dict
            channel_group_remove_group method returns a dict indicating status of the request

            {
                u'status': 200,
                u'message': 'OK', 
                u'service': u'channel-registry',
                u'error': False
            }

            Async Mode: None ( callback gets the response as parameter )

            Response Format:

            The callback passed to channel_group_remove_group gets the a dict indicating status of the request

            {
                u'status': 200,
                u'message': 'OK', 
                u'service': u'channel-registry',
                u'error': False
            }

        """

        return self._channel_group(channel_group=channel_group, mode='remove', callback=callback, error=error)



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
        secret_key=None,
        cipher_key=None,
        auth_key=None,
        ssl_on=False,
        origin='pubsub.pubnub.com',
        uuid=None,
        _tt_lock=empty_lock,
        _channel_list_lock=empty_lock,
        _channel_group_list_lock=empty_lock
    ):

        super(PubnubCoreAsync, self).__init__(
            publish_key=publish_key,
            subscribe_key=subscribe_key,
            secret_key=secret_key,
            cipher_key=cipher_key,
            auth_key=auth_key,
            ssl_on=ssl_on,
            origin=origin,
            uuid=uuid
        )

        self.subscriptions = {}
        self.subscription_groups = {}
        self.timetoken = 0
        self.last_timetoken = 0
        self.accept_encoding = 'gzip'
        self.SUB_RECEIVER = None
        self._connect = None
        self._tt_lock = _tt_lock
        self._channel_list_lock = _channel_list_lock
        self._channel_group_list_lock = _channel_group_list_lock
        self._connect = lambda: None
        self.u = None

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

    def get_channel_group_list(self, channel_groups):
        channel_group = ''
        first = True
        with self._channel_group_list_lock:
            for ch in channel_groups:
                if not channel_groups[ch]['subscribed']:
                    continue
                if not first:
                    channel_group += ','
                else:
                    first = False
                channel_group += ch
        return channel_group


    def get_channel_array(self):
        """Get List of currently subscribed channels

        Returns:
            Returns a list containing names of channels subscribed

            Sample return value:
                ["a","b","c]
        """
        channels = self.subscriptions
        channel = []
        with self._channel_list_lock:
            for ch in channels:
                if not channels[ch]['subscribed']:
                    continue
                channel.append(ch)
        return channel

    def get_channel_group_array(self):
        """Get List of currently subscribed channel groups

        Returns:
            Returns a list containing names of channel groups subscribed

            Sample return value:
                ["a","b","c]
        """
        channel_groups = self.subscription_groups
        channel_group = []
        with self._channel_group_list_lock:
            for ch in channel_groups:
                if not channel_groups[ch]['subscribed']:
                    continue
                channel_group.append(ch)
        return channel_group

    def each(l, func):
        if func is None:
            return
        for i in l:
            func(i)

    def subscribe(self, channels, callback, error=None,
                  connect=None, disconnect=None, reconnect=None, sync=False):
        """Subscribe to data on a channel.

        This function causes the client to create an open TCP socket to the
        PubNub Real-Time Network and begin listening for messages on a specified channel.
        To subscribe to a channel the client must send the appropriate subscribe_key at
        initialization.
        
        Only works in async mode

        Args:
            channel:    (string/list)
                        Specifies the channel to subscribe to. It is possible to specify
                        multiple channels as a comma separated list or andarray.

            callback:   (function)
                        This callback is called on receiving a message from the channel.

            error:      (function) (optional)
                        This callback is called on an error event

            connect:    (function) (optional)
                        This callback is called on a successful connection to the PubNub cloud

            disconnect: (function) (optional)
                        This callback is called on client disconnect from the PubNub cloud
            
            reconnect:  (function) (optional)
                        This callback is called on successfully re-connecting to the PubNub cloud
        
        Returns:
            None
        """

        return self._subscribe(channels=channels, callback=callback, error=error,
            connect=connect, disconnect=disconnect, reconnect=reconnect, sync=sync)

    def subscribe_group(self, channel_groups, callback, error=None,
                  connect=None, disconnect=None, reconnect=None, sync=False):
        """Subscribe to data on a channel group.

        This function causes the client to create an open TCP socket to the
        PubNub Real-Time Network and begin listening for messages on a specified channel.
        To subscribe to a channel group the client must send the appropriate subscribe_key at
        initialization.
        
        Only works in async mode

        Args:
            channel_groups:    (string/list)
                        Specifies the channel groups to subscribe to. It is possible to specify
                        multiple channel groups as a comma separated list or andarray.

            callback:   (function)
                        This callback is called on receiving a message from the channel.

            error:      (function) (optional)
                        This callback is called on an error event

            connect:    (function) (optional)
                        This callback is called on a successful connection to the PubNub cloud

            disconnect: (function) (optional)
                        This callback is called on client disconnect from the PubNub cloud
            
            reconnect:  (function) (optional)
                        This callback is called on successfully re-connecting to the PubNub cloud
        
        Returns:
            None
        """

        return self._subscribe(channel_groups=channel_groups, callback=callback, error=error,
            connect=connect, disconnect=disconnect, reconnect=reconnect, sync=sync)

    def _subscribe(self, channels=None, channel_groups=None, callback=None, error=None,
                  connect=None, disconnect=None, reconnect=None, sync=False):

        with self._tt_lock:
            self.last_timetoken = self.timetoken if self.timetoken != 0 \
                else self.last_timetoken
            self.timetoken = 0

        if sync is True and self.subscribe_sync is not None:
            self.subscribe_sync(args)
            return

        def _invoke(func, msg=None, channel=None, real_channel=None):
            if func is not None:
                if msg is not None and channel is not None and real_channel is not None:
                    try:
                        func(get_data_for_user(msg), channel, real_channel)
                    except:
                        func(get_data_for_user(msg), channel)
                elif msg is not None and channel is not None:
                    func(get_data_for_user(msg), channel)
                elif msg is not None:
                    func(get_data_for_user(msg))
                else:
                    func()

        def _invoke_connect():
            if self._channel_list_lock:
                with self._channel_list_lock:
                    for ch in self.subscriptions:
                        chobj = self.subscriptions[ch]
                        if chobj['connected'] is False:
                            chobj['connected'] = True
                            chobj['disconnected'] = False
                            _invoke(chobj['connect'], chobj['name'])
                        else:
                            if chobj['disconnected'] is True:
                                chobj['disconnected'] = False
                                _invoke(chobj['reconnect'], chobj['name'])

            if self._channel_group_list_lock:
                with self._channel_group_list_lock:
                    for ch in self.subscription_groups:
                        chobj = self.subscription_groups[ch]
                        if chobj['connected'] is False:
                            chobj['connected'] = True
                            chobj['disconnected'] = False
                            _invoke(chobj['connect'], chobj['name'])
                        else:
                            if chobj['disconnected'] is True:
                                chobj['disconnected'] = False
                                _invoke(chobj['reconnect'], chobj['name'])


        def _invoke_disconnect():
            if self._channel_list_lock:
                with self._channel_list_lock:
                    for ch in self.subscriptions:
                        chobj = self.subscriptions[ch]
                        if chobj['connected'] is True:
                            if chobj['disconnected'] is False:
                                chobj['disconnected'] = True
                                _invoke(chobj['disconnect'], chobj['name'])
            if self._channel_group_list_lock:
                with self._channel_group_list_lock:
                    for ch in self.subscription_groups:
                        chobj = self.subscription_groups[ch]
                        if chobj['connected'] is True:
                            if chobj['disconnected'] is False:
                                chobj['disconnected'] = True
                                _invoke(chobj['disconnect'], chobj['name'])


        def _invoke_error(channel_list=None, error=None):
            if channel_list is None:
                for ch in self.subscriptions:
                    chobj = self.subscriptions[ch]
                    _invoke(chobj['error'], error)
            else:
                for ch in channel_list:
                    chobj = self.subscriptions[ch]
                    _invoke(chobj['error'], error)

        def _get_channel():
            for ch in self.subscriptions:
                chobj = self.subscriptions[ch]
                if chobj['subscribed'] is True:
                    return chobj

        if channels is not None:
            channels = channels if isinstance(
                channels, list) else channels.split(",")
            for channel in channels:
                ## New Channel?
                if len(channel) > 0 and \
                        (not channel in self.subscriptions or
                         self.subscriptions[channel]['subscribed'] is False):
                        with self._channel_list_lock:
                            self.subscriptions[channel] = {
                                'name': channel,
                                'first': False,
                                'connected': False,
                                'disconnected': True,
                                'subscribed': True,
                                'callback': callback,
                                'connect': connect,
                                'disconnect': disconnect,
                                'reconnect': reconnect,
                                'error': error
                            }
        
        if channel_groups is not None:
            channel_groups = channel_groups if isinstance(
                channel_groups, list) else channel_groups.split(",")

            for channel_group in channel_groups:
                ## New Channel?
                if len(channel_group) > 0 and \
                        (not channel_group in self.subscription_groups or
                         self.subscription_groups[channel_group]['subscribed'] is False):
                        with self._channel_group_list_lock:
                            self.subscription_groups[channel_group] = {
                                'name': channel_group,
                                'first': False,
                                'connected': False,
                                'disconnected': True,
                                'subscribed': True,
                                'callback': callback,
                                'connect': connect,
                                'disconnect': disconnect,
                                'reconnect': reconnect,
                                'error': error
                            }

        '''
        ## return if already connected to channel
        if channel in self.subscriptions and \
            'connected' in self.subscriptions[channel] and \
                self.subscriptions[channel]['connected'] is True:
                    _invoke(error, "Already Connected")
                    return
        '''
        ## SUBSCRIPTION RECURSION
        def _connect():

            self._reset_offline()

            def error_callback(response):
                ## ERROR ?
                if not response or \
                    ('message' in response and
                        response['message'] == 'Forbidden'):
                            _invoke_error(channel_list=response['payload'][
                                'channels'], error=response['message'])
                            self.timeout(1, _connect)
                            return
                if 'message' in response:
                    _invoke_error(error=response['message'])
                else:
                    _invoke_disconnect()
                    self.timetoken = 0
                    self.timeout(1, _connect)

            def sub_callback(response):
                ## ERROR ?
                if not response or \
                    ('message' in response and
                        response['message'] == 'Forbidden'):
                            _invoke_error(channel_list=response['payload'][
                                'channels'], error=response['message'])
                            _connect()
                            return

                _invoke_connect()

                with self._tt_lock:
                    self.timetoken = \
                        self.last_timetoken if self.timetoken == 0 and \
                        self.last_timetoken != 0 else response[1]

                    if len(response) > 3:
                        channel_list = response[2].split(',')
                        channel_list_2 = response[3].split(',')
                        response_list = response[0]
                        for ch in enumerate(channel_list):
                            if ch[1] in self.subscription_groups or ch[1] in self.subscriptions:
                                try:
                                    chobj = self.subscription_groups[ch[1]]
                                except KeyError as k:
                                    chobj = self.subscriptions[ch[1]]
                                _invoke(chobj['callback'],
                                        self.decrypt(response_list[ch[0]]),
                                        chobj['name'].split('-pnpres')[0], channel_list_2[ch[0]].split('-pnpres')[0])                    
                    elif len(response) > 2:
                        channel_list = response[2].split(',')
                        response_list = response[0]
                        for ch in enumerate(channel_list):
                            if ch[1] in self.subscriptions:
                                chobj = self.subscriptions[ch[1]]
                                _invoke(chobj['callback'],
                                        self.decrypt(response_list[ch[0]]),
                                        chobj['name'].split('-pnpres')[0])
                    else:
                        response_list = response[0]
                        chobj = _get_channel()
                        for r in response_list:
                            if chobj:
                                _invoke(chobj['callback'], self.decrypt(r),
                                        chobj['name'].split('-pnpres')[0])

                    _connect()

            channel_list = self.get_channel_list(self.subscriptions)
            channel_group_list = self.get_channel_group_list(self.subscription_groups)

            if len(channel_list) <= 0 and len(channel_group_list) <= 0:
                return

            if len(channel_list) <= 0:
                channel_list = ','

            ## CONNECT TO PUBNUB SUBSCRIBE SERVERS
            #try:
            self.SUB_RECEIVER = self._request({"urlcomponents": [
                'subscribe',
                self.subscribe_key,
                channel_list,
                '0',
                str(self.timetoken)
            ], "urlparams": {"uuid": self.uuid, "auth": self.auth_key,
            'pnsdk' : self.pnsdk, 'channel-group' : channel_group_list}},
                sub_callback,
                error_callback,
                single=True, timeout=320)
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
        """Unsubscribe from channel .
           Only works in async mode

        Args:
            channel: Channel name ( string ) 
        """
        if channel in self.subscriptions is False:
            return False

        ## DISCONNECT
        with self._channel_list_lock:
            if channel in self.subscriptions:
                self.subscriptions[channel]['connected'] = 0
                self.subscriptions[channel]['subscribed'] = False
                self.subscriptions[channel]['timetoken'] = 0
                self.subscriptions[channel]['first'] = False
                self.leave_channel(channel=channel)
        self.CONNECT()

    def unsubscribe_group(self, channel_group):
        """Unsubscribe from channel group.
           Only works in async mode

        Args:
            channel_group: Channel group name ( string )
        """
        if channel_group in self.subscription_groups is False:
            return False

        ## DISCONNECT
        with self._channel_group_list_lock:
            if channel_group in self.subscription_groups:
                self.subscription_groups[channel_group]['connected'] = 0
                self.subscription_groups[channel_group]['subscribed'] = False
                self.subscription_groups[channel_group]['timetoken'] = 0
                self.subscription_groups[channel_group]['first'] = False
                self.leave_group(channel_group=channel_group)
        self.CONNECT()


class PubnubCore(PubnubCoreAsync):
    def __init__(
        self,
        publish_key,
        subscribe_key,
        secret_key=None,
        cipher_key=None,
        auth_key=None,
        ssl_on=False,
        origin='pubsub.pubnub.com',
        uuid=None,
        _tt_lock=None,
        _channel_list_lock=None,
        _channel_group_list_lock=None

    ):
        super(PubnubCore, self).__init__(
            publish_key=publish_key,
            subscribe_key=subscribe_key,
            secret_key=secret_key,
            cipher_key=cipher_key,
            auth_key=auth_key,
            ssl_on=ssl_on,
            origin=origin,
            uuid=uuid,
            _tt_lock=_tt_lock,
            _channel_list_lock=_channel_list_lock,
            _channel_group_list_lock=_channel_group_list_lock
        )

        self.subscriptions = {}
        self.timetoken = 0
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
                ], "urlparams": {"uuid": self.uuid, 'pnsdk' : self.pnsdk}})

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


class HTTPClient:
    def __init__(self, pubnub, url, urllib_func=None,
                 callback=None, error=None, id=None, timeout=5):
        self.url = url
        self.id = id
        self.callback = callback
        self.error = error
        self.stop = False
        self._urllib_func = urllib_func
        self.timeout = timeout
        self.pubnub = pubnub

    def cancel(self):
        self.stop = True
        self.callback = None
        self.error = None

    def run(self):

        def _invoke(func, data):
            if func is not None:
                func(get_data_for_user(data))

        if self._urllib_func is None:
            return

        resp = self._urllib_func(self.url, timeout=self.timeout)
        data = resp[0]
        code = resp[1]

        if self.stop is True:
            return
        if self.callback is None:
            with self.pubnub.latest_sub_callback_lock:
                if self.pubnub.latest_sub_callback['id'] != self.id:
                    return
                else:
                    if self.pubnub.latest_sub_callback['callback'] is not None:
                        self.pubnub.latest_sub_callback['id'] = 0
                        try:
                            data = json.loads(data)
                        except ValueError as e:
                            _invoke(self.pubnub.latest_sub_callback['error'],
                                    {'error': 'json decoding error'})
                            return
                        if code != 200:
                            _invoke(self.pubnub.latest_sub_callback['error'], data)
                        else:
                            _invoke(self.pubnub.latest_sub_callback['callback'], data)
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


def _urllib_request_2(url, timeout=5):
    try:
        resp = urllib2.urlopen(url, timeout=timeout)
    except urllib2.HTTPError as http_error:
        resp = http_error
    except urllib2.URLError as error:
        msg = {"message": str(error.reason)}
        return (json.dumps(msg), 0)

    return (resp.read(), resp.code)

class PubnubHTTPAdapter(HTTPAdapter):
    def init_poolmanager(self, *args, **kwargs):
        kwargs.setdefault('socket_options', default_socket_options)

        super(PubnubHTTPAdapter, self).init_poolmanager(*args, **kwargs)

s = requests.Session()
#s.mount('http://', PubnubHTTPAdapter(max_retries=1))
#s.mount('https://', PubnubHTTPAdapter(max_retries=1))
#s.mount('http://pubsub.pubnub.com', HTTPAdapter(max_retries=1))
#s.mount('https://pubsub.pubnub.com', HTTPAdapter(max_retries=1))


def _requests_request(url, timeout=5):
    try:
        resp = s.get(url, timeout=timeout)
    except requests.exceptions.HTTPError as http_error:
        resp = http_error
    except requests.exceptions.ConnectionError as error:
        msg = str(error)
        return (json.dumps(msg), 0)
    except requests.exceptions.Timeout as error:
        msg = str(error)
        return (json.dumps(msg), 0)
    return (resp.text, resp.status_code)


def _urllib_request_3(url, timeout=5):
    try:
        resp = urllib.request.urlopen(url, timeout=timeout)
    except (urllib.request.HTTPError, urllib.request.URLError) as http_error:
        resp = http_error
    r = resp.read().decode("utf-8")
    return (r, resp.code)

_urllib_request = None


#  Pubnub

class Pubnub(PubnubCore):
    def __init__(
        self,
        publish_key,
        subscribe_key,
        secret_key=None,
        cipher_key=None,
        auth_key=None,
        ssl_on=False,
        origin='pubsub.pubnub.com',
        uuid=None,
        pooling=True,
        daemon=False,
        pres_uuid=None,
        azure=False
    ):
        super(Pubnub, self).__init__(
            publish_key=publish_key,
            subscribe_key=subscribe_key,
            secret_key=secret_key,
            cipher_key=cipher_key,
            auth_key=auth_key,
            ssl_on=ssl_on,
            origin=origin,
            uuid=uuid or pres_uuid,
            _tt_lock=threading.RLock(),
            _channel_list_lock=threading.RLock(),
            _channel_group_list_lock=threading.RLock()
        )
        global _urllib_request
        if self.python_version == 2:
            _urllib_request = _urllib_request_2
        else:
            _urllib_request = _urllib_request_3

        if pooling is True:
            _urllib_request = _requests_request

        self.latest_sub_callback_lock = threading.RLock()
        self.latest_sub_callback = {'id': None, 'callback': None}
        self.pnsdk = 'PubNub-Python' + '/' + self.version
        self.daemon = daemon
        
        if azure is False:
            s.mount('http://pubsub.pubnub.com', HTTPAdapter(max_retries=1))
            s.mount('https://pubsub.pubnub.com', HTTPAdapter(max_retries=1))
        else:
            s.mount('http://', PubnubHTTPAdapter(max_retries=1))
            s.mount('https://', PubnubHTTPAdapter(max_retries=1))         

    def timeout(self, interval, func):
        def cb():
            time.sleep(interval)
            func()
        thread = threading.Thread(target=cb)
        thread.daemon = self.daemon
        thread.start()

    def _request_async(self, request, callback=None, error=None, single=False, timeout=5):
        global _urllib_request
        ## Build URL
        url = self.getUrl(request)
        if single is True:
            id = time.time()
            client = HTTPClient(self, url=url, urllib_func=_urllib_request,
                                callback=None, error=None, id=id, timeout=timeout)
            with self.latest_sub_callback_lock:
                self.latest_sub_callback['id'] = id
                self.latest_sub_callback['callback'] = callback
                self.latest_sub_callback['error'] = error
        else:
            client = HTTPClient(self, url=url, urllib_func=_urllib_request,
                                callback=callback, error=error, timeout=timeout)

        thread = threading.Thread(target=client.run)
        thread.daemon = self.daemon
        thread.start()

        def abort():
            client.cancel()
        return abort

    def _request_sync(self, request, timeout=5):
        global _urllib_request
        ## Build URL
        url = self.getUrl(request)
        ## Send Request Expecting JSONP Response
        response = _urllib_request(url, timeout=timeout)
        try:
            resp_json = json.loads(response[0])
        except ValueError:
            return [0, "JSON Error"]

        if response[1] != 200 and 'message' in resp_json and 'payload' in resp_json:
            return {'message': resp_json['message'],
                    'payload': resp_json['payload']}

        if response[1] == 0:
            return [0, resp_json]

        return resp_json

    def _request(self, request, callback=None, error=None, single=False, timeout=5):
        if callback is None:
            return get_data_for_user(self._request_sync(request, timeout=timeout))
        else:
            self._request_async(request, callback, error, single=single, timeout=timeout)

# Pubnub Twisted

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
        secret_key=None,
        cipher_key=None,
        auth_key=None,
        ssl_on=False,
        origin='pubsub.pubnub.com'
    ):
        super(PubnubTwisted, self).__init__(
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
        self.headers['V'] = [self.version]
        self.pnsdk = 'PubNub-Python-' + 'Twisted' + '/' + self.version

    def _request(self, request, callback=None, error=None, single=False, timeout=5):
        global pnconn_pool

        def _invoke(func, data):
            if func is not None:
                func(get_data_for_user(data))

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
                _invoke(error, {"message": "Not Found"})
                return

            finished = Deferred()
            if response.code in [401, 403]:
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


# PubnubTornado
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
        self.pnsdk = 'PubNub-Python-' + 'Tornado' + '/' + self.version

    def _request(self, request, callback=None, error=None,
                 single=False, timeout=5, connect_timeout=5):

        def _invoke(func, data):
            if func is not None:
                func(get_data_for_user(data))

        url = self.getUrl(request)
        request = tornado.httpclient.HTTPRequest(
            url, 'GET',
            self.headers,
            connect_timeout=connect_timeout,
            request_timeout=timeout)
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
