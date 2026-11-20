"""Docs page: configuration (sync). Source: docs/sdks/python/api-reference/configuration.md.

The initialization samples use made up keys, so each step overwrites the keys on the same config object after the
sample ran and then proves the client works against the service. Validation branches run against an unreachable origin
with the request handler replaced by a counter, so they prove that no request was sent.
"""
import re
from os import environ
from unittest import mock

from pubnub.exceptions import PubNubException
from pubnub.pubnub import PubNub
from pubnub.request_handlers.httpx import HttpxRequestHandler

from harness import assertions as a
from harness import names, world
from harness.listeners import listen
from harness.step import step
from harness.wait import eventually

USER_ID_ERROR = 'UUID missing or invalid type'  # pubnub/pnconfiguration.py, validate_not_empty_string
UNREACHABLE = '127.0.0.1:1'


def real_keys(config):
    """Copy the keyset of the open role onto a config the sample built with made up keys."""
    real = world.config('open')
    config.subscribe_key = real.subscribe_key
    config.publish_key = real.publish_key


def works(clients, pubnub, config):
    """Overwrite the made up keys and prove the client talks to the service. Returns the time() envelope."""
    clients._made.append(pubnub)
    real_keys(config)
    config.daemon = True
    envelope = pubnub.time().sync()
    a.timetoken(str(envelope.result))
    return envelope


class RequestCounter:
    """Replaces the request handler call so that a validation branch can prove no request was sent."""

    def __init__(self):
        self.calls = 0

    def __call__(self, *args, **kwargs):
        self.calls += 1
        raise RuntimeError('a request was sent')


@step('configuration_full', role='open')
def test_full_configuration(clients):
    channel = names.with_suffix('my_channel')
    real = world.config('open')
    saved = {k: environ.get(k) for k in ('SUBSCRIBE_KEY', 'PUBLISH_KEY', 'USER_ID')}
    environ.update({'SUBSCRIBE_KEY': real.subscribe_key, 'PUBLISH_KEY': real.publish_key,
                    'USER_ID': names.with_suffix('configured_user')})
    try:
        # snippet.configuration_full
        import os
        from pubnub.pnconfiguration import PNConfiguration
        from pubnub.enums import PNHeartbeatNotificationOptions
        from pubnub.pubnub import PubNub
        from pubnub.crypto import AesCbcCryptoModule

        # Configuration for PubNub instance
        pn_configuration = PNConfiguration()

        # Set configuration values
        pn_configuration.subscribe_key = os.getenv('SUBSCRIBE_KEY', 'demo')  # required
        pn_configuration.publish_key = os.getenv('PUBLISH_KEY', 'demo')  # only required if publishing
        pn_configuration.secret_key = os.getenv('SECRET_KEY', 'my_secret_key')  # optional
        pn_configuration.cipher_key = os.getenv('CIPHER_KEY', 'my_cipher_key')  # for encryption/decryption
        pn_configuration.crypto_module = AesCbcCryptoModule(pn_configuration)  # for encryption/decryption
        pn_configuration.user_id = os.getenv('USER_ID', 'my_custom_user_id')  # must be set
        pn_configuration.auth_key = os.getenv('AUTH_KEY', 'my_auth_key')  # optional
        pn_configuration.ssl = True
        pn_configuration.connect_timeout = 100
        pn_configuration.subscribe_request_timeout = 310
        pn_configuration.non_subscribe_request_timeout = 300
        pn_configuration.filter_expression = "such == 'wow'"
        pn_configuration.heartbeat_notification_options = PNHeartbeatNotificationOptions.ALL

        # Initialize the PubNub client
        pubnub = PubNub(pn_configuration)

        print("Configuration set up complete and PubNub client initialized.")
        # snippet.end
    finally:
        for key, value in saved.items():
            if value is None:
                environ.pop(key, None)
            else:
                environ[key] = value
    clients._made.append(pubnub)
    a.eq(pn_configuration.subscribe_key, real.subscribe_key, 'keys come from the environment')
    a.eq(pubnub.uuid, names.with_suffix('configured_user'))
    a.eq((pn_configuration.connect_timeout, pn_configuration.subscribe_request_timeout,
          pn_configuration.non_subscribe_request_timeout), (100, 310, 300), 'timeouts')
    a.eq(pn_configuration.heartbeat_notification_options, PNHeartbeatNotificationOptions.ALL)
    a.eq((pn_configuration.auth_key, pn_configuration.filter_expression), ('my_auth_key', "such == 'wow'"))

    # The same crypto module on a reader: a message published with the sample client is readable
    reader_config = world.config('open', 'config_reader')
    reader_config.cipher_key = 'my_cipher_key'
    reader_config.crypto_module = pn_configuration.crypto_module.__class__(reader_config)
    reader = PubNub(reader_config)
    clients._made.append(reader)
    seen = listen(reader, channel)
    envelope = pubnub.publish().channel(channel).message({'configured': True}).sync()
    a.timetoken(envelope.result.timetoken)
    eventually(lambda: a.eq([m.message for m in seen.messages], [{'configured': True}], 'reader decrypts'))


@step('initialize_pubnub', 'initialize_non_secure', 'initialize_ssl', 'initialize_custom_user_id', role='open')
def test_initialize(clients):
    # snippet.initialize_pubnub
    from pubnub.pnconfiguration import PNConfiguration
    from pubnub.pubnub import PubNub

    pnconfig = PNConfiguration()
    pnconfig.subscribe_key = "my_subkey"
    pnconfig.publish_key = "my_pubkey"
    pnconfig.ssl = True
    pnconfig.user_id = "my_custom_user_id"
    pubnub = PubNub(pnconfig)
    # snippet.end
    a.eq((pubnub.uuid, pnconfig.ssl), ('my_custom_user_id', True))
    a.ok(works(clients, pubnub, pnconfig).status.tls_enabled, 'requests use TLS')

    # snippet.initialize_non_secure
    from pubnub.pnconfiguration import PNConfiguration
    from pubnub.pubnub import PubNub

    pnconfig = PNConfiguration()
    pnconfig.subscribe_key = "my_subkey"
    pnconfig.publish_key = "my_pubkey"
    pnconfig.ssl = False
    pnconfig.user_id = "my_custom_user_id"
    pubnub = PubNub(pnconfig)
    # snippet.end
    a.eq(pnconfig.scheme(), 'http')
    a.eq(works(clients, pubnub, pnconfig).status.tls_enabled, False, 'requests are plain http')

    # snippet.initialize_ssl
    from pubnub.pnconfiguration import PNConfiguration
    from pubnub.pubnub import PubNub

    pnconfig = PNConfiguration()
    pnconfig.subscribe_key = "my_subkey"
    pnconfig.publish_key = "my_pubkey"
    pnconfig.ssl = True
    pnconfig.user_id = "my_custom_user_id"
    pubnub = PubNub(pnconfig)
    # snippet.end
    a.eq(pnconfig.scheme_and_host(), 'https://ps.pndsn.com')
    a.ok(works(clients, pubnub, pnconfig).status.tls_enabled, 'requests use TLS')

    # snippet.initialize_custom_user_id
    from pubnub.pnconfiguration import PNConfiguration
    from pubnub.pubnub import PubNub

    pnconfig = PNConfiguration()

    pnconfig.subscribe_key = 'mySubscribeKey'
    pnconfig.publish_key = 'myPublishKey'
    pnconfig.user_id = "my_custom_user_id"

    pubnub = PubNub(pnconfig)
    # snippet.end
    a.eq(pubnub.uuid, 'my_custom_user_id')
    a.eq(pnconfig.user_id, pnconfig.uuid, 'user_id and the deprecated uuid are the same value')
    works(clients, pubnub, pnconfig)

    # The user ID is mandatory. The branches below never reach the network.
    counter = RequestCounter()
    with mock.patch.object(HttpxRequestHandler, 'sync_request', counter):
        missing = PNConfiguration()
        missing.subscribe_key = 'mySubscribeKey'
        missing.origin = UNREACHABLE
        a.raises(AssertionError, PubNub, missing, match=re.escape(USER_ID_ERROR))
        for bad in ('', '   ', None, 42):
            a.raises(AssertionError, setattr, missing, 'user_id', bad, match=re.escape(USER_ID_ERROR))
        a.eq(missing.user_id, None, 'a rejected user_id is not stored')
    a.eq(counter.calls, 0, 'no request was sent')


@step('initialize_custom_request_handler', role='open')
def test_initialize_custom_request_handler(clients):
    # snippet.initialize_custom_request_handler
    from pubnub.pnconfiguration import PNConfiguration
    from pubnub.pubnub import PubNub
    from pubnub.request_handlers.requests import RequestsRequestHandler

    pnconfig = PNConfiguration()
    pnconfig.subscribe_key = "my_subkey"
    pnconfig.publish_key = "my_pubkey"
    pnconfig.user_id = "my_custom_user_id"

    pubnub = PubNub(pnconfig, custom_request_handler=RequestsRequestHandler)
    # snippet.end
    a.ok(isinstance(pubnub._request_handler, RequestsRequestHandler), 'the custom handler is in use')
    a.ok(not isinstance(pubnub._request_handler, HttpxRequestHandler), 'the default handler is replaced')
    works(clients, pubnub, pnconfig)
    a.raises(Exception, PubNub, pnconfig, custom_request_handler=dict, match='subclass of BaseRequestHandler')


@step('initialize_read_only', role='open')
def test_initialize_read_only(clients):
    channel = names.with_suffix('my_channel')

    # snippet.initialize_read_only
    from pubnub.pnconfiguration import PNConfiguration
    from pubnub.pubnub import PubNub

    pnconfig = PNConfiguration()
    pnconfig.subscribe_key = "my_subkey"
    pnconfig.user_id = "my_custom_user_id"

    pubnub = PubNub(pnconfig)
    # snippet.end
    clients._made.append(pubnub)
    a.eq(pnconfig.publish_key, None, 'no publish key')

    counter = RequestCounter()
    pnconfig.origin = UNREACHABLE
    with mock.patch.object(HttpxRequestHandler, 'sync_request', counter):
        error = a.raises(PubNubException, pubnub.publish().channel(channel).message('x').sync,
                         match='Publish key not configured')
    a.eq(str(error), 'Publish key not configured', 'exact error text')
    a.eq(counter.calls, 0, 'no request was sent')

    # It still reads: the same config with the real subscribe key receives a message another client published
    pnconfig.origin = world.config('open').origin
    pnconfig.subscribe_key = world.config('open').subscribe_key
    pnconfig.daemon = True
    seen = listen(pubnub, channel)
    clients.sync('open', 'writer').publish().channel(channel).message('read-me').sync()
    eventually(lambda: a.eq([m.message for m in seen.messages], ['read-me'], 'the read-only client received'))


@step('initialize_access_manager', role='open')
def test_initialize_access_manager(clients):
    # snippet.initialize_access_manager
    from pubnub.pnconfiguration import PNConfiguration
    from pubnub.pubnub import PubNub

    pnconfig = PNConfiguration()
    pnconfig.subscribe_key = "my_subkey"
    pnconfig.publish_key = "my_pubkey"
    pnconfig.secret_key = "my_secretkey"
    pnconfig.user_id = "my_custom_user_id"
    pnconfig.ssl = True

    pubnub = PubNub(pnconfig)
    # snippet.end
    a.eq(pnconfig.secret_key, 'my_secretkey')
    clients._made.append(pubnub)

    counter = RequestCounter()
    pnconfig.origin = UNREACHABLE
    with mock.patch.object(HttpxRequestHandler, 'sync_request', counter):
        a.raises(RuntimeError, pubnub.grant().channels('x').read(True).sync, match='a request was sent')
        a.eq(counter.calls, 1, 'the grant call reaches the handler once the secret key is configured')
        keyless = PubNub(world.config('open', 'no_secret'))
        clients._made.append(keyless)
        a.raises(PubNubException, keyless.grant().channels('x').read(True).sync, match='Secret key is not configured')
        a.eq(counter.calls, 1, 'without a secret key no request is built')


@step('set_filter_expression', 'get_filter_expression', role='open')
def test_filter_expression(clients):
    channel = names.with_suffix('my_channel')

    # snippet.set_filter_expression
    from pubnub.pnconfiguration import PNConfiguration

    pnconfig = PNConfiguration()
    pnconfig.filter_expression = "such == 'wow'"
    # snippet.end
    real_keys(pnconfig)
    pnconfig.user_id = names.with_suffix('filtered')
    pnconfig.daemon = True
    filtered = PubNub(pnconfig)
    clients._made.append(filtered)
    seen = listen(filtered, channel)
    publisher = clients.sync('open', 'filter_publisher')
    publisher.publish().channel(channel).message('no-meta').sync()
    publisher.publish().channel(channel).message('other').meta({'such': 'meh'}).sync()
    publisher.publish().channel(channel).message('matching').meta({'such': 'wow'}).sync()
    eventually(lambda: a.eq([m.message for m in seen.messages], ['matching'], 'only the matching message arrived'))

    # snippet.get_filter_expression
    filter = pnconfig.filter_expression
    # snippet.end
    a.eq(filter, "such == 'wow'")
    a.eq(world.config('open').filter_expression, None, 'the default is no filter')
