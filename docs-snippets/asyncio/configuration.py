"""Docs page: configuration (asyncio). Source: docs/sdks/asyncio/api-reference/configuration.md.

The initialization samples use made up keys, so each step overwrites the keys on the same config object after the
sample ran and then proves the client works against the service. Validation branches replace the network call of the
request handler with a counter, so they prove that no request was sent.
"""
import asyncio
import re
from os import environ
from unittest import mock

from pubnub.pubnub_asyncio import AsyncioSubscriptionManager, PubNubAsyncio
from pubnub.request_handlers.async_httpx import AsyncHttpxRequestHandler

from harness import assertions as a
from harness import names, world
from harness.listeners import alisten
from harness.step import step
from harness.wait import aeventually

USER_ID_ERROR = 'UUID missing or invalid type'  # pubnub/pnconfiguration.py, validate_not_empty_string
UNREACHABLE = '127.0.0.1:1'


def real_keys(config):
    """Copy the keyset of the open role onto a config the sample built with made up keys."""
    real = world.config('open')
    config.subscribe_key = real.subscribe_key
    config.publish_key = real.publish_key


async def works(aclients, pubnub, config):
    """Overwrite the made up keys and prove the client talks to the service. Returns the time() envelope."""
    aclients._made.append(pubnub)
    real_keys(config)
    envelope = await pubnub.time().future()
    a.ok(not envelope.status.is_error(), 'time() succeeded')
    a.timetoken(str(envelope.result))
    return envelope


class RequestCounter:
    """Replaces the network call of the request handler so that a validation branch can prove nothing was sent."""

    def __init__(self):
        self.calls = 0

    async def __call__(self, *args, **kwargs):
        self.calls += 1
        raise RuntimeError('a request was sent')


@step('configuration_full', role='open')
async def test_full_configuration(aclients):
    real = world.config('open')
    saved = {k: environ.get(k) for k in ('PUBNUB_SUBSCRIBE_KEY', 'PUBNUB_PUBLISH_KEY', 'PUBNUB_USER_ID')}
    environ.update({'PUBNUB_SUBSCRIBE_KEY': real.subscribe_key, 'PUBNUB_PUBLISH_KEY': real.publish_key,
                    'PUBNUB_USER_ID': names.with_suffix('configured_user')})
    try:
        # snippet.configuration_full
        import os
        from pubnub.pnconfiguration import PNConfiguration
        from pubnub.enums import PNHeartbeatNotificationOptions

        # Configuration for the client instance
        pn_configuration = PNConfiguration()

        # Set configuration values
        pn_configuration.subscribe_key = os.getenv('PUBNUB_SUBSCRIBE_KEY', 'demo')  # required
        pn_configuration.publish_key = os.getenv('PUBNUB_PUBLISH_KEY', 'demo')  # only required if publishing
        pn_configuration.secret_key = os.getenv('PUBNUB_SECRET_KEY', 'my_secret_key')  # optional
        pn_configuration.user_id = os.getenv('PUBNUB_USER_ID', 'my_custom_user_id')  # must be set
        pn_configuration.auth_key = os.getenv('PUBNUB_AUTH_KEY', 'my_auth_key')  # optional
        pn_configuration.ssl = True
        pn_configuration.filter_expression = "such == 'wow'"
        pn_configuration.heartbeat_notification_options = PNHeartbeatNotificationOptions.ALL

        # Adding the requested parameters
        pn_configuration.enable_subscribe = True  # required if you want to subscribe
        pn_configuration.enable_presence_heartbeat = True  # sends presence heartbeats for subscribed channels

        # The configuration is ready to pass to PubNub
        # Simply create a PubNub instance using it:
        pubnub = PubNubAsyncio(pn_configuration)

        print("Configuration set up complete.")
        # snippet.end
    finally:
        for key, value in saved.items():
            if value is None:
                environ.pop(key, None)
            else:
                environ[key] = value
    aclients._made.append(pubnub)
    a.eq(pn_configuration.subscribe_key, real.subscribe_key, 'keys come from the environment')
    a.eq(pubnub.uuid, names.with_suffix('configured_user'))
    a.eq(pn_configuration.heartbeat_notification_options, PNHeartbeatNotificationOptions.ALL)
    a.eq((pn_configuration.enable_subscribe, pn_configuration.enable_presence_heartbeat), (True, True))
    a.eq((pn_configuration.auth_key, pn_configuration.filter_expression), ('my_auth_key', "such == 'wow'"))

    # The configured client publishes, and a plain client on the same channel reads the message
    channel = names.with_suffix('my_channel')
    seen = await alisten(aclients.asyncio('open', 'config_reader'), channel)
    envelope = await pubnub.publish().channel(channel).message({'configured': True}).future()
    a.timetoken(envelope.result.timetoken)

    async def received():
        a.eq([m.message for m in seen.messages], [{'configured': True}], 'reader received')
    await aeventually(received)


@step('initialize_pubnub', 'initialize_non_secure', 'initialize_ssl', 'initialize_custom_user_id', role='open')
async def test_initialize(aclients):
    # snippet.initialize_pubnub
    from pubnub.pnconfiguration import PNConfiguration
    from pubnub.pubnub_asyncio import PubNubAsyncio

    pnconfig = PNConfiguration()
    pnconfig.subscribe_key = "my_subkey"
    pnconfig.publish_key = "my_pubkey"
    pnconfig.ssl = True
    pnconfig.user_id = "my_custom_user_id"
    pubnub = PubNubAsyncio(pnconfig)
    # snippet.end
    a.eq((pubnub.uuid, pnconfig.ssl), ('my_custom_user_id', True))
    a.ok((await works(aclients, pubnub, pnconfig)).status.tls_enabled, 'requests use TLS')

    # snippet.initialize_non_secure
    from pubnub.pnconfiguration import PNConfiguration
    from pubnub.pubnub_asyncio import PubNubAsyncio

    pnconfig = PNConfiguration()
    pnconfig.subscribe_key = "my_subkey"
    pnconfig.publish_key = "my_pubkey"
    pnconfig.ssl = False
    pnconfig.user_id = "my_custom_user_id"
    pubnub = PubNubAsyncio(pnconfig)
    # snippet.end
    a.eq(pnconfig.scheme(), 'http')
    a.eq((await works(aclients, pubnub, pnconfig)).status.tls_enabled, False, 'requests are plain http')

    # snippet.initialize_ssl
    from pubnub.pnconfiguration import PNConfiguration
    from pubnub.pubnub_asyncio import PubNubAsyncio

    pnconfig = PNConfiguration()
    pnconfig.subscribe_key = "my_subkey"
    pnconfig.publish_key = "my_pubkey"
    pnconfig.ssl = True
    pnconfig.user_id = "my_custom_user_id"
    pubnub = PubNubAsyncio(pnconfig)
    # snippet.end
    a.eq(pnconfig.scheme_and_host(), 'https://ps.pndsn.com')
    a.ok((await works(aclients, pubnub, pnconfig)).status.tls_enabled, 'requests use TLS')

    # snippet.initialize_custom_user_id
    from pubnub.pnconfiguration import PNConfiguration
    from pubnub.pubnub_asyncio import PubNubAsyncio

    pnconfig = PNConfiguration()

    pnconfig.subscribe_key = 'mySubscribeKey'
    pnconfig.publish_key = 'myPublishKey'
    pnconfig.user_id = "my_custom_user_id"

    pubnub = PubNubAsyncio(pnconfig)
    # snippet.end
    a.eq(pubnub.uuid, 'my_custom_user_id')
    a.eq(pnconfig.user_id, pnconfig.uuid, 'user_id and the deprecated uuid are the same value')
    await works(aclients, pubnub, pnconfig)

    # The user ID is mandatory. The branches below never reach the network.
    counter = RequestCounter()
    with mock.patch.object(AsyncHttpxRequestHandler, '_request_with_wall_clock_deadline', counter):
        missing = PNConfiguration()
        missing.subscribe_key = 'mySubscribeKey'
        missing.origin = UNREACHABLE
        a.raises(AssertionError, PubNubAsyncio, missing, match=re.escape(USER_ID_ERROR))
        for bad in ('', '   ', None, 42):
            a.raises(AssertionError, setattr, missing, 'user_id', bad, match=re.escape(USER_ID_ERROR))
        a.eq(missing.user_id, None, 'a rejected user_id is not stored')
    a.eq(counter.calls, 0, 'no request was sent')


@step('initialize_custom_request_handler', role='open')
async def test_initialize_custom_request_handler(aclients):
    # snippet.initialize_custom_request_handler
    from pubnub.pnconfiguration import PNConfiguration
    from pubnub.pubnub_asyncio import PubNubAsyncio
    from pubnub.request_handlers.async_aiohttp import AsyncAiohttpRequestHandler

    pnconfig = PNConfiguration()
    pnconfig.subscribe_key = "my_subkey"
    pnconfig.publish_key = "my_pubkey"
    pnconfig.ssl = True
    pnconfig.user_id = "my_custom_user_id"
    pubnub = PubNubAsyncio(pnconfig, custom_request_handler=AsyncAiohttpRequestHandler)
    # snippet.end
    a.ok(isinstance(pubnub._request_handler, AsyncAiohttpRequestHandler), 'the custom handler is in use')
    a.ok(not isinstance(pubnub._request_handler, AsyncHttpxRequestHandler), 'the default handler is replaced')
    await works(aclients, pubnub, pnconfig)
    a.raises(Exception, PubNubAsyncio, pnconfig, custom_request_handler=dict, match='subclass of BaseRequestHandler')


@step('initialize_read_only', role='open')
async def test_initialize_read_only(aclients):
    channel = names.with_suffix('my_channel')

    # snippet.initialize_read_only
    from pubnub.pnconfiguration import PNConfiguration
    from pubnub.pubnub_asyncio import PubNubAsyncio

    pnconfig = PNConfiguration()
    pnconfig.subscribe_key = "my_subkey"
    pnconfig.user_id = "my_custom_user_id"

    pubnub = PubNubAsyncio(pnconfig)
    # snippet.end
    aclients._made.append(pubnub)
    a.eq(pnconfig.publish_key, None, 'no publish key')

    counter = RequestCounter()
    pnconfig.origin = UNREACHABLE
    with mock.patch.object(AsyncHttpxRequestHandler, '_request_with_wall_clock_deadline', counter):
        failed = await pubnub.publish().channel(channel).message('x').future()
    a.ok(failed.is_error(), 'publishing without a publish key fails')
    a.eq(str(failed.status.error_data.exception), 'Publish key not configured', 'exact error text')
    a.eq(counter.calls, 0, 'no request was sent')

    # It still reads: the same config with the real subscribe key receives a message another client published
    pnconfig.origin = world.config('open').origin
    pnconfig.subscribe_key = world.config('open').subscribe_key
    seen = await alisten(pubnub, channel)
    await aclients.asyncio('open', 'writer').publish().channel(channel).message('read-me').future()

    async def received():
        a.eq([m.message for m in seen.messages], ['read-me'], 'the read-only client received')
    await aeventually(received)


@step('initialize_access_manager', role='open')
async def test_initialize_access_manager(aclients):
    # snippet.initialize_access_manager
    from pubnub.pnconfiguration import PNConfiguration
    from pubnub.pubnub_asyncio import PubNubAsyncio

    pnconfig = PNConfiguration()
    pnconfig.subscribe_key = "my_subkey"
    pnconfig.publish_key = "my_pubkey"
    pnconfig.secret_key = "my_secretkey"
    pnconfig.user_id = "my_custom_user_id"
    pnconfig.ssl = True

    pubnub = PubNubAsyncio(pnconfig)
    # snippet.end
    a.eq(pnconfig.secret_key, 'my_secretkey')
    aclients._made.append(pubnub)

    counter = RequestCounter()
    pnconfig.origin = UNREACHABLE
    with mock.patch.object(AsyncHttpxRequestHandler, '_request_with_wall_clock_deadline', counter):
        with mock.patch('warnings.warn'):
            with_secret = await pubnub.grant().channels('x').read(True).future()
            a.eq(counter.calls, 1, 'the grant call reaches the network layer once the secret key is configured')
            a.ok(with_secret.is_error(), 'the stand-in refused the request')
            keyless = aclients.asyncio('open', 'no_secret')
            without = await keyless.grant().channels('x').read(True).future()
    a.eq(str(without.status.error_data.exception), 'Secret key is not configured', 'exact error text')
    a.eq(counter.calls, 1, 'without a secret key no request is built')


@step('initialize_custom_event_loop', role='open')
async def test_initialize_custom_event_loop(aclients):
    my_event_loop = asyncio.get_running_loop()

    # snippet.initialize_custom_event_loop
    from pubnub.pnconfiguration import PNConfiguration
    from pubnub.pubnub_asyncio import PubNubAsyncio

    pnconfig = PNConfiguration()
    pnconfig.subscribe_key = "my_subkey"
    pnconfig.publish_key = "my_pubkey"
    pnconfig.user_id = "my_custom_user_id"

    pubnub = PubNubAsyncio(pnconfig, custom_event_loop=my_event_loop)
    # snippet.end
    a.ok(pubnub.event_loop is my_event_loop, 'the client runs on the given loop')
    await works(aclients, pubnub, pnconfig)


@step('set_filter_expression', 'get_filter_expression', role='open')
async def test_filter_expression(aclients):
    channel = names.with_suffix('my_channel')

    # snippet.set_filter_expression
    from pubnub.pnconfiguration import PNConfiguration

    pnconfig = PNConfiguration()
    pnconfig.filter_expression = "such == 'wow'"
    # snippet.end
    real_keys(pnconfig)
    pnconfig.user_id = names.with_suffix('filtered')
    # The default event engine subscribe loop ignores filter_expression (SDK bug, see the report), so this step uses the
    # documented subscription_manager argument of the constructor to select the loop that sends the filter.
    filtered = PubNubAsyncio(pnconfig, subscription_manager=AsyncioSubscriptionManager)
    aclients._made.append(filtered)
    seen = await alisten(filtered, channel)
    publisher = aclients.asyncio('open', 'filter_publisher')
    await publisher.publish().channel(channel).message('no-meta').future()
    await publisher.publish().channel(channel).message('other').meta({'such': 'meh'}).future()
    await publisher.publish().channel(channel).message('matching').meta({'such': 'wow'}).future()

    async def only_matching():
        a.eq([m.message for m in seen.messages], ['matching'], 'only the matching message arrived')
    await aeventually(only_matching)

    # snippet.get_filter_expression
    filter = pnconfig.filter_expression
    # snippet.end
    a.eq(filter, "such == 'wow'")
    a.eq(world.config('open').filter_expression, None, 'the default is no filter')
