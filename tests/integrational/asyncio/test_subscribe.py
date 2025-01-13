import logging
import asyncio
import pytest
import pubnub as pn

from unittest.mock import patch
from pubnub.callbacks import SubscribeCallback
from pubnub.models.consumer.common import PNStatus
from pubnub.models.consumer.pubsub import PNMessageResult
from pubnub.models.envelopes import AsyncioEnvelope
from pubnub.pubnub_asyncio import AsyncioSubscriptionManager, PubNubAsyncio, SubscribeListener
from tests.helper import gen_channel, pnconf_enc_env_copy, pnconf_env_copy, pnconf_sub_copy
from tests.integrational.vcr_asyncio_sleeper import VCR599Listener, VCR599ReconnectionManager
from pubnub.enums import PNReconnectionPolicy, PNStatusCategory
from pubnub.managers import LinearDelay, ExponentialDelay
# from tests.integrational.vcr_helper import pn_vcr

pn.set_stream_logger('pubnub', logging.DEBUG)


async def patch_pubnub(pubnub):
    pubnub._subscription_manager._reconnection_manager = VCR599ReconnectionManager(pubnub)


class TestCallback(SubscribeCallback):
    message_result = None
    status_result = None
    presence_result = None

    def status(self, pubnub, status):
        self.status_result = status

    def message(self, pubnub, message):
        self.message_result = message

    def presence(self, pubnub, presence):
        self.presence_result = presence


# TODO: refactor cassette
# @pn_vcr.use_cassette('tests/integrational/fixtures/asyncio/subscription/sub_unsub.json', serializer='pn_json',
#                      filter_query_parameters=['pnsdk', 'ee', 'tr'])
@pytest.mark.asyncio
async def test_subscribe_unsubscribe():
    channel = "test-subscribe-asyncio-ch"
    config = pnconf_env_copy(enable_subscribe=True, enable_presence_heartbeat=False)
    pubnub = PubNubAsyncio(config)

    callback = SubscribeListener()
    pubnub.add_listener(callback)

    pubnub.subscribe().channels(channel).execute()
    assert channel in pubnub.get_subscribed_channels()
    assert len(pubnub.get_subscribed_channels()) == 1

    await callback.wait_for_connect()
    assert channel in pubnub.get_subscribed_channels()
    assert len(pubnub.get_subscribed_channels()) == 1

    pubnub.unsubscribe().channels(channel).execute()
    assert channel not in pubnub.get_subscribed_channels()
    assert len(pubnub.get_subscribed_channels()) == 0

    # with EE you don't have to wait for disconnect
    if isinstance(pubnub._subscription_manager, AsyncioSubscriptionManager):
        await callback.wait_for_disconnect()
    assert channel not in pubnub.get_subscribed_channels()
    assert len(pubnub.get_subscribed_channels()) == 0

    await pubnub.stop()
    await asyncio.sleep(3)


# @pn_vcr.use_cassette('tests/integrational/fixtures/asyncio/subscription/sub_pub_unsub.json', serializer='pn_json',
#                      filter_query_parameters=['pnsdk', 'ee', 'tr'])
@pytest.mark.asyncio
async def test_subscribe_publish_unsubscribe():
    sub_config = pnconf_env_copy(enable_subscribe=True, enable_presence_heartbeat=False)
    pub_config = pnconf_env_copy(enable_subscribe=True, enable_presence_heartbeat=False)
    sub_config.uuid = 'test-subscribe-asyncio-uuid-sub'
    pub_config.uuid = 'test-subscribe-asyncio-uuid-pub'
    pubnub_sub = PubNubAsyncio(sub_config)
    pubnub_pub = PubNubAsyncio(pub_config)

    await patch_pubnub(pubnub_sub)
    await patch_pubnub(pubnub_pub)

    callback = VCR599Listener(1)
    channel = "test-subscribe-asyncio-ch"
    message = "hey"
    pubnub_sub.add_listener(callback)
    pubnub_sub.subscribe().channels(channel).execute()

    await callback.wait_for_connect()

    publish_future = asyncio.ensure_future(pubnub_pub.publish().channel(channel).message(message).future())
    subscribe_message_future = asyncio.ensure_future(callback.wait_for_message_on(channel))

    await asyncio.wait([
        publish_future,
        subscribe_message_future
    ])

    publish_envelope = publish_future.result()
    subscribe_envelope = subscribe_message_future.result()

    assert isinstance(subscribe_envelope, PNMessageResult)
    assert subscribe_envelope.channel == channel
    assert subscribe_envelope.subscription is None
    assert subscribe_envelope.message == message
    assert subscribe_envelope.timetoken > 0

    assert isinstance(publish_envelope, AsyncioEnvelope)
    assert publish_envelope.result.timetoken > 0
    assert publish_envelope.status.original_response[0] == 1

    pubnub_sub.unsubscribe().channels(channel).execute()
    # with EE you don't have to wait for disconnect
    if isinstance(pubnub_sub._subscription_manager, AsyncioSubscriptionManager):
        await callback.wait_for_disconnect()

    await pubnub_pub.stop()
    await pubnub_sub.stop()


# @pn_vcr.use_cassette(
#     'tests/integrational/fixtures/asyncio/subscription/sub_pub_unsub_enc.yaml',
#     filter_query_parameters=['pnsdk']
# )
@pytest.mark.asyncio
async def test_encrypted_subscribe_publish_unsubscribe():

    pubnub = PubNubAsyncio(pnconf_enc_env_copy(enable_subscribe=True))
    pubnub.config.uuid = 'test-subscribe-asyncio-uuid'

    with patch("pubnub.crypto.PubNubCryptodome.get_initialization_vector", return_value="knightsofni12345"):
        callback = VCR599Listener(1)
        channel = "test-subscribe-asyncio-ch"
        message = "hey"
        pubnub.add_listener(callback)
        pubnub.subscribe().channels(channel).execute()

        await callback.wait_for_connect()

        publish_future = asyncio.ensure_future(pubnub.publish().channel(channel).message(message).future())
        subscribe_message_future = asyncio.ensure_future(callback.wait_for_message_on(channel))

        await asyncio.wait([
            publish_future,
            subscribe_message_future
        ])

        publish_envelope = publish_future.result()
        subscribe_envelope = subscribe_message_future.result()

        assert isinstance(subscribe_envelope, PNMessageResult)
        assert subscribe_envelope.channel == channel
        assert subscribe_envelope.subscription is None
        assert subscribe_envelope.message == message
        assert subscribe_envelope.timetoken > 0

        assert isinstance(publish_envelope, AsyncioEnvelope)
        assert publish_envelope.result.timetoken > 0
        assert publish_envelope.status.original_response[0] == 1

        pubnub.unsubscribe().channels(channel).execute()
        # with EE you don't have to wait for disconnect
        if isinstance(pubnub._subscription_manager, AsyncioSubscriptionManager):
            await callback.wait_for_disconnect()

    await pubnub.stop()


# @pn_vcr.use_cassette('tests/integrational/fixtures/asyncio/subscription/join_leave.yaml',
#                      filter_query_parameters=['pnsdk', 'l_cg', 'ee'])
@pytest.mark.asyncio
async def test_join_leave():
    channel = gen_channel("test-subscribe-asyncio-join-leave-ch")
    pubnub_config = pnconf_sub_copy()
    pubnub_config.uuid = "test-subscribe-asyncio-messenger"
    pubnub = PubNubAsyncio(pubnub_config)

    listener_config = pnconf_sub_copy()
    listener_config.uuid = "test-subscribe-asyncio-listener"
    pubnub_listener = PubNubAsyncio(listener_config)

    await patch_pubnub(pubnub)
    await patch_pubnub(pubnub_listener)

    callback_presence = SubscribeListener()
    callback_messages = SubscribeListener()

    pubnub_listener.add_listener(callback_presence)
    pubnub_listener.subscribe().channels(channel).with_presence().execute()

    await callback_presence.wait_for_connect()

    await asyncio.sleep(1)
    envelope = await callback_presence.wait_for_presence_on(channel)

    assert envelope.channel == channel
    assert envelope.event == 'join'
    assert envelope.uuid == pubnub_listener.uuid

    pubnub.add_listener(callback_messages)
    pubnub.subscribe().channels(channel).execute()
    await callback_messages.wait_for_connect()

    envelope = await callback_presence.wait_for_presence_on(channel)
    assert envelope.channel == channel
    assert envelope.event == 'join'
    assert envelope.uuid == pubnub.uuid

    pubnub.unsubscribe().channels(channel).execute()
    # with EE you don't have to wait for disconnect
    if isinstance(pubnub._subscription_manager, AsyncioSubscriptionManager):
        await callback_messages.wait_for_disconnect()

    envelope = await callback_presence.wait_for_presence_on(channel)
    assert envelope.channel == channel
    assert envelope.event == 'leave'
    assert envelope.uuid == pubnub.uuid

    pubnub_listener.unsubscribe().channels(channel).execute()
    # with EE you don't have to wait for disconnect
    if isinstance(pubnub._subscription_manager, AsyncioSubscriptionManager):
        await callback_presence.wait_for_disconnect()

    await pubnub.stop()
    await pubnub_listener.stop()


# @pn_vcr.use_cassette('tests/integrational/fixtures/asyncio/subscription/cg_sub_unsub.yaml',
#                      filter_query_parameters=['uuid', 'pnsdk', 'l_cg', 'l_pres'])
@pytest.mark.asyncio
async def test_cg_subscribe_unsubscribe():
    ch = "test-subscribe-asyncio-channel"
    gr = "test-subscribe-asyncio-group"

    pubnub = PubNubAsyncio(pnconf_env_copy(enable_subscribe=True))

    envelope = await pubnub.add_channel_to_channel_group().channel_group(gr).channels(ch).future()
    assert envelope.status.original_response['status'] == 200

    await asyncio.sleep(3)

    callback_messages = SubscribeListener()
    pubnub.add_listener(callback_messages)
    pubnub.subscribe().channel_groups(gr).execute()
    await callback_messages.wait_for_connect()

    pubnub.unsubscribe().channel_groups(gr).execute()
    # with EE you don't have to wait for disconnect
    if isinstance(pubnub._subscription_manager, AsyncioSubscriptionManager):
        await callback_messages.wait_for_disconnect()

    envelope = await pubnub.remove_channel_from_channel_group().channel_group(gr).channels(ch).future()
    assert envelope.status.original_response['status'] == 200

    await pubnub.stop()


# @get_sleeper('tests/integrational/fixtures/asyncio/subscription/cg_sub_pub_unsub.yaml')
# @pn_vcr.use_cassette('tests/integrational/fixtures/asyncio/subscription/cg_sub_pub_unsub.yaml',
#                      filter_query_parameters=['uuid', 'pnsdk', 'l_cg', 'l_pres', 'l_pub'])
@pytest.mark.asyncio
async def test_cg_subscribe_publish_unsubscribe():
    ch = "test-subscribe-asyncio-channel"
    gr = "test-subscribe-asyncio-group"
    message = "hey"

    pubnub = PubNubAsyncio(pnconf_env_copy(enable_subscribe=True))

    envelope = await pubnub.add_channel_to_channel_group().channel_group(gr).channels(ch).future()
    assert envelope.status.original_response['status'] == 200

    await asyncio.sleep(1)

    callback_messages = VCR599Listener(1)
    pubnub.add_listener(callback_messages)
    pubnub.subscribe().channel_groups(gr).execute()
    await callback_messages.wait_for_connect()

    subscribe_future = asyncio.ensure_future(callback_messages.wait_for_message_on(ch))
    publish_future = asyncio.ensure_future(pubnub.publish().channel(ch).message(message).future())
    await asyncio.wait([subscribe_future, publish_future])

    sub_envelope = subscribe_future.result()
    pub_envelope = publish_future.result()

    assert pub_envelope.status.original_response[0] == 1
    assert pub_envelope.status.original_response[1] == 'Sent'

    assert sub_envelope.channel == ch
    assert sub_envelope.subscription == gr
    assert sub_envelope.message == message

    pubnub.unsubscribe().channel_groups(gr).execute()
    # with EE you don't have to wait for disconnect
    if isinstance(pubnub._subscription_manager, AsyncioSubscriptionManager):
        await callback_messages.wait_for_disconnect()

    envelope = await pubnub.remove_channel_from_channel_group().channel_group(gr).channels(ch).future()
    assert envelope.status.original_response['status'] == 200

    await pubnub.stop()


# @pn_vcr.use_cassette('tests/integrational/fixtures/asyncio/subscription/cg_join_leave.json', serializer='pn_json',
#                      filter_query_parameters=['pnsdk', 'l_cg', 'l_pres', 'ee', 'tr'])
@pytest.mark.asyncio
async def test_cg_join_leave():
    config = pnconf_sub_copy()
    config.uuid = "test-subscribe-asyncio-messenger"
    pubnub = PubNubAsyncio(config)

    config_listener = pnconf_sub_copy()
    config_listener.uuid = "test-subscribe-asyncio-listener"
    pubnub_listener = PubNubAsyncio(config_listener)

    ch = gen_channel("test-subscribe-asyncio-join-leave-cg-channel")
    gr = gen_channel("test-subscribe-asyncio-join-leave-cg-group")

    envelope = await pubnub.add_channel_to_channel_group().channel_group(gr).channels(ch).future()
    assert envelope.status.original_response['status'] == 200
    await asyncio.sleep(1)

    callback_messages = SubscribeListener()
    callback_presence = SubscribeListener()

    pubnub_listener.add_listener(callback_presence)
    pubnub_listener.subscribe().channel_groups(gr).with_presence().execute()
    await callback_presence.wait_for_connect()

    prs_envelope = await callback_presence.wait_for_presence_on(ch)
    assert prs_envelope.event == 'join'
    assert prs_envelope.uuid == pubnub_listener.uuid
    assert prs_envelope.channel == ch
    assert prs_envelope.subscription == gr
    await asyncio.sleep(2)

    pubnub.add_listener(callback_messages)
    pubnub.subscribe().channel_groups(gr).execute()

    callback_messages_future = asyncio.ensure_future(callback_messages.wait_for_connect())
    presence_messages_future = asyncio.ensure_future(callback_presence.wait_for_presence_on(ch))
    await asyncio.wait([callback_messages_future, presence_messages_future])
    prs_envelope = presence_messages_future.result()

    assert prs_envelope.event == 'join'
    assert prs_envelope.uuid == pubnub.uuid
    assert prs_envelope.channel == ch
    assert prs_envelope.subscription == gr
    await asyncio.sleep(2)

    pubnub.unsubscribe().channel_groups(gr).execute()

    callback_messages_future = asyncio.ensure_future(callback_messages.wait_for_disconnect())
    presence_messages_future = asyncio.ensure_future(callback_presence.wait_for_presence_on(ch))
    await asyncio.wait([callback_messages_future, presence_messages_future])
    prs_envelope = presence_messages_future.result()

    assert prs_envelope.event == 'leave'
    assert prs_envelope.uuid == pubnub.uuid
    assert prs_envelope.channel == ch
    assert prs_envelope.subscription == gr

    pubnub_listener.unsubscribe().channel_groups(gr).execute()
    await asyncio.sleep(2)

    # with EE you don't have to wait for disconnect
    if isinstance(pubnub._subscription_manager, AsyncioSubscriptionManager):
        await callback_presence.wait_for_disconnect()

    envelope = await pubnub.remove_channel_from_channel_group().channel_group(gr).channels(ch).future()
    assert envelope.status.original_response['status'] == 200

    await pubnub.stop()
    await pubnub_listener.stop()


# @pn_vcr.use_cassette(
#     'tests/integrational/fixtures/asyncio/subscription/unsubscribe_all.yaml',
#     filter_query_parameters=['pnsdk', 'l_cg', 'l_pres'],
#     match_on=['method', 'scheme', 'host', 'port', 'string_list_in_path', 'string_list_in_query'],
# )
@pytest.mark.asyncio
async def test_unsubscribe_all():
    config = pnconf_env_copy(enable_subscribe=True, uuid="test-subscribe-asyncio-messenger")
    pubnub = PubNubAsyncio(config)

    ch = "test-subscribe-asyncio-unsubscribe-all-ch"
    ch1 = "test-subscribe-asyncio-unsubscribe-all-ch1"
    ch2 = "test-subscribe-asyncio-unsubscribe-all-ch2"
    ch3 = "test-subscribe-asyncio-unsubscribe-all-ch3"
    gr1 = "test-subscribe-asyncio-unsubscribe-all-gr1"
    gr2 = "test-subscribe-asyncio-unsubscribe-all-gr2"

    envelope = await pubnub.add_channel_to_channel_group().channel_group(gr1).channels(ch).future()
    assert envelope.status.original_response['status'] == 200
    envelope = await pubnub.add_channel_to_channel_group().channel_group(gr2).channels(ch).future()
    assert envelope.status.original_response['status'] == 200

    await asyncio.sleep(1)

    callback_messages = VCR599Listener(1)
    pubnub.add_listener(callback_messages)

    pubnub.subscribe().channels([ch1, ch2, ch3]).channel_groups([gr1, gr2]).execute()
    await callback_messages.wait_for_connect()

    assert len(pubnub.get_subscribed_channels()) == 3
    assert len(pubnub.get_subscribed_channel_groups()) == 2

    pubnub.unsubscribe_all()
    # with EE you don't have to wait for disconnect
    if isinstance(pubnub._subscription_manager, AsyncioSubscriptionManager):
        await callback_messages.wait_for_disconnect()

    assert len(pubnub.get_subscribed_channels()) == 0
    assert len(pubnub.get_subscribed_channel_groups()) == 0

    envelope = await pubnub.remove_channel_from_channel_group().channel_group(gr1).channels(ch).future()
    assert envelope.status.original_response['status'] == 200
    envelope = await pubnub.remove_channel_from_channel_group().channel_group(gr2).channels(ch).future()
    assert envelope.status.original_response['status'] == 200

    await pubnub.stop()


@pytest.mark.asyncio
async def test_subscribe_failing_reconnect_policy_none():
    config = pnconf_env_copy(enable_subscribe=True,
                             uuid="test-subscribe-failing-reconnect-policy-none",
                             reconnect_policy=PNReconnectionPolicy.NONE,
                             origin='127.0.0.1')
    pubnub = PubNubAsyncio(config)

    listener = TestCallback()
    pubnub.add_listener(listener)
    pubnub.subscribe().channels("my_channel").execute()
    while True:
        if isinstance(listener.status_result, PNStatus) \
           and listener.status_result.category == PNStatusCategory.PNDisconnectedCategory:
            break
        await asyncio.sleep(1)


@pytest.mark.asyncio
async def test_subscribe_failing_reconnect_policy_none():
    config = pnconf_env_copy(enable_subscribe=True,
                             uuid="test-subscribe-failing-reconnect-policy-none",
                             reconnect_policy=PNReconnectionPolicy.NONE,
                             origin='127.0.0.1')
    pubnub = PubNubAsyncio(config)

    listener = TestCallback()
    pubnub.add_listener(listener)
    pubnub.subscribe().channels("my_channel_none").execute()
    while True:
        if isinstance(listener.status_result, PNStatus) \
           and listener.status_result.category == PNStatusCategory.PNDisconnectedCategory:
            break
        await asyncio.sleep(0.5)


@pytest.mark.asyncio
async def test_subscribe_failing_reconnect_policy_linear():
    # we don't test the actual delay calculation here, just everything around it
    def mock_calculate(*args, **kwargs):
        return 0.2

    with patch('pubnub.managers.LinearDelay.calculate', wraps=mock_calculate) as calculate_mock:
        config = pnconf_env_copy(enable_subscribe=True,
                                 uuid="test-subscribe-failing-reconnect-policy-linear",
                                 reconnect_policy=PNReconnectionPolicy.LINEAR,
                                 origin='127.0.0.1')
        pubnub = PubNubAsyncio(config)

        listener = TestCallback()
        pubnub.add_listener(listener)
        pubnub.subscribe().channels("my_channel_linear").execute()
        while True:
            if isinstance(listener.status_result, PNStatus) \
               and listener.status_result.category == PNStatusCategory.PNDisconnectedCategory:
                break
            await asyncio.sleep(0.5)
        assert calculate_mock.call_count == LinearDelay.MAX_RETRIES


@pytest.mark.asyncio
async def test_subscribe_failing_reconnect_policy_exponential():
    # we don't test the actual delay calculation here, just everything around it
    def mock_calculate(*args, **kwargs):
        return 0.2

    with patch('pubnub.managers.ExponentialDelay.calculate', wraps=mock_calculate) as calculate_mock:
        config = pnconf_env_copy(enable_subscribe=True,
                                 uuid="test-subscribe-failing-reconnect-policy-exponential",
                                 reconnect_policy=PNReconnectionPolicy.EXPONENTIAL,
                                 origin='127.0.0.1')
        pubnub = PubNubAsyncio(config)

        listener = TestCallback()
        pubnub.add_listener(listener)
        pubnub.subscribe().channels("my_channel_exponential").execute()
        while True:
            if isinstance(listener.status_result, PNStatus) \
               and listener.status_result.category == PNStatusCategory.PNDisconnectedCategory:
                break
            await asyncio.sleep(0.5)
        assert calculate_mock.call_count == ExponentialDelay.MAX_RETRIES


@pytest.mark.asyncio
async def test_subscribe_failing_reconnect_policy_linear_with_max_retries():
    # we don't test the actual delay calculation here, just everything around it
    def mock_calculate(*args, **kwargs):
        return 0.2

    with patch('pubnub.managers.LinearDelay.calculate', wraps=mock_calculate) as calculate_mock:
        config = pnconf_env_copy(enable_subscribe=True, maximum_reconnection_retries=3,
                                 uuid="test-subscribe-failing-reconnect-policy-linear-with-max-retries",
                                 reconnect_policy=PNReconnectionPolicy.LINEAR,
                                 origin='127.0.0.1')
        pubnub = PubNubAsyncio(config)

        listener = TestCallback()
        pubnub.add_listener(listener)
        pubnub.subscribe().channels("my_channel_linear").execute()
        while True:
            if isinstance(listener.status_result, PNStatus) \
               and listener.status_result.category == PNStatusCategory.PNDisconnectedCategory:
                break
            await asyncio.sleep(0.5)
        assert calculate_mock.call_count == 3


@pytest.mark.asyncio
async def test_subscribe_failing_reconnect_policy_exponential_with_max_retries():
    # we don't test the actual delay calculation here, just everything around it
    def mock_calculate(*args, **kwargs):
        return 0.2

    with patch('pubnub.managers.ExponentialDelay.calculate', wraps=mock_calculate) as calculate_mock:
        config = pnconf_env_copy(enable_subscribe=True, maximum_reconnection_retries=3,
                                 uuid="test-subscribe-failing-reconnect-policy-exponential-with-max-retries",
                                 reconnect_policy=PNReconnectionPolicy.EXPONENTIAL,
                                 origin='127.0.0.1')
        pubnub = PubNubAsyncio(config)

        listener = TestCallback()
        pubnub.add_listener(listener)
        pubnub.subscribe().channels("my_channel_exponential").execute()
        while True:
            if isinstance(listener.status_result, PNStatus) \
               and listener.status_result.category == PNStatusCategory.PNDisconnectedCategory:
                break
            await asyncio.sleep(0.5)
        assert calculate_mock.call_count == 3


@pytest.mark.asyncio
async def test_subscribe_failing_reconnect_policy_linear_with_custom_interval():
    # we don't test the actual delay calculation here, just everything around it
    def mock_calculate(*args, **kwargs):
        return 0.2

    with patch('pubnub.managers.LinearDelay.calculate', wraps=mock_calculate) as calculate_mock:
        config = pnconf_env_copy(enable_subscribe=True, maximum_reconnection_retries=3, reconnection_interval=1,
                                 uuid="test-subscribe-failing-reconnect-policy-linear-with-max-retries",
                                 reconnect_policy=PNReconnectionPolicy.LINEAR,
                                 origin='127.0.0.1')
        pubnub = PubNubAsyncio(config)

        listener = TestCallback()
        pubnub.add_listener(listener)
        pubnub.subscribe().channels("my_channel_linear").execute()
        while True:
            if isinstance(listener.status_result, PNStatus) \
               and listener.status_result.category == PNStatusCategory.PNDisconnectedCategory:
                break
            await asyncio.sleep(0.5)
        assert calculate_mock.call_count == 0
