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

from support import assertions as a
from support.clients import config as client_config
from support.listen import alisten
from support.wait import aeventually
from shared.configuration import (
    RequestCounter_async as RequestCounter, UNREACHABLE, USER_ID_ERROR, real_keys, works_async as works,
)


async def test_configuration_full(aclients):
    """Snippet: configuration_full."""
    real = client_config('open')
    saved = {k: environ.get(k) for k in ('PUBNUB_SUBSCRIBE_KEY', 'PUBNUB_PUBLISH_KEY', 'PUBNUB_USER_ID')}
    environ.update({'PUBNUB_SUBSCRIBE_KEY': real.subscribe_key, 'PUBNUB_PUBLISH_KEY': real.publish_key,
                    'PUBNUB_USER_ID': 'configured_user'})
    try:
        # snippet.configuration_full
        import os
        from pubnub.pnconfiguration import PNConfiguration
        from pubnub.enums import PNHeartbeatNotificationOptions
        from pubnub.pubnub_asyncio import PubNubAsyncio

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
    a.eq(pubnub.uuid, 'configured_user')
    a.eq(pn_configuration.heartbeat_notification_options, PNHeartbeatNotificationOptions.ALL)
    a.eq((pn_configuration.enable_subscribe, pn_configuration.enable_presence_heartbeat), (True, True))
    a.eq((pn_configuration.auth_key, pn_configuration.filter_expression), ('my_auth_key', "such == 'wow'"))

    # The configured client publishes, and a plain client on the same channel reads the message
    channel = 'my_channel'
    seen = await alisten(aclients.asyncio('open', 'config_reader'), channel)
    envelope = await pubnub.publish().channel(channel).message({'configured': True}).future()
    a.timetoken(envelope.result.timetoken)

    async def received():
        a.eq([m.message for m in seen.messages], [{'configured': True}], 'reader received')
    await aeventually(received)


async def test_initialize_pubnub(aclients):
    """Snippets: initialize_pubnub, initialize_non_secure, initialize_ssl, initialize_custom_user_id."""
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


async def test_initialize_custom_request_handler(aclients):
    """Snippet: initialize_custom_request_handler."""
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


async def test_initialize_read_only(aclients):
    """Snippet: initialize_read_only."""
    channel = 'my_channel'

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
    pnconfig.origin = client_config('open').origin
    pnconfig.subscribe_key = client_config('open').subscribe_key
    seen = await alisten(pubnub, channel)
    await aclients.asyncio('open', 'writer').publish().channel(channel).message('read-me').future()

    async def received():
        a.eq([m.message for m in seen.messages], ['read-me'], 'the read-only client received')
    await aeventually(received)


async def test_initialize_access_manager(aclients):
    """Snippet: initialize_access_manager."""
    # The sample reads the secret key from PUBNUB_SECRET_KEY. The live tier sets it from the PAM keyset.
    environ.setdefault('PUBNUB_SECRET_KEY', client_config('pam', 'configurer').secret_key)
    # snippet.initialize_access_manager
    import os
    from pubnub.pnconfiguration import PNConfiguration
    from pubnub.pubnub_asyncio import PubNubAsyncio

    pnconfig = PNConfiguration()
    pnconfig.subscribe_key = "my_subkey"
    pnconfig.publish_key = "my_pubkey"
    pnconfig.secret_key = os.environ["PUBNUB_SECRET_KEY"]
    pnconfig.user_id = "my_custom_user_id"
    pnconfig.ssl = True

    pubnub = PubNubAsyncio(pnconfig)
    # snippet.end
    # a.ok, not a.eq: a.eq puts both values in the failure message, and the secret must not reach the CI log
    a.ok(pnconfig.secret_key == environ['PUBNUB_SECRET_KEY'], 'the sample sets the secret key from the environment')
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


async def test_initialize_custom_event_loop(aclients):
    """Snippet: initialize_custom_event_loop."""
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


async def test_set_filter_expression(aclients):
    """Snippets: set_filter_expression, get_filter_expression."""
    channel = 'my_channel'

    # snippet.set_filter_expression
    from pubnub.pnconfiguration import PNConfiguration

    pnconfig = PNConfiguration()
    pnconfig.filter_expression = "such == 'wow'"
    # snippet.end
    real_keys(pnconfig)
    pnconfig.user_id = 'filtered'
    # The default subscribe loop (EventEngineSubscriptionManager) ignores filter_expression (SDK bug, see the report),
    # so this step uses the documented subscription_manager argument of the constructor to select the loop that sends
    # the filter.
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
    a.eq(client_config('open').filter_expression, None, 'the default is no filter')
