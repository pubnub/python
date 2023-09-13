import logging
import asyncio
import pytest
import pubnub as pn

from unittest.mock import patch
from pubnub.models.consumer.pubsub import PNMessageResult
from pubnub.pubnub_asyncio import PubNubAsyncio, AsyncioEnvelope, SubscribeListener
from tests.helper import pnconf_env_copy, pnconf_enc_env_copy
from tests.integrational.vcr_asyncio_sleeper import get_sleeper, VCR599Listener, VCR599ReconnectionManager
from tests.integrational.vcr_helper import pn_vcr


pn.set_stream_logger('pubnub', logging.DEBUG)


async def patch_pubnub(pubnub):
    pubnub._subscription_manager._reconnection_manager = VCR599ReconnectionManager(pubnub)


@pn_vcr.use_cassette('tests/integrational/fixtures/asyncio/subscription/sub_unsub.json',
                     filter_query_parameters=['uuid', 'pnsdk'], serializer='pn_json')
@pytest.mark.asyncio
async def test_subscribe_unsubscribe(event_loop):
    channel = "test-subscribe-asyncio-ch"

    pubnub = PubNubAsyncio(pnconf_env_copy(), custom_event_loop=event_loop)

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

    # await callback.wait_for_disconnect()
    assert channel not in pubnub.get_subscribed_channels()
    assert len(pubnub.get_subscribed_channels()) == 0

    await pubnub.stop()


@pn_vcr.use_cassette('tests/integrational/fixtures/asyncio/subscription/sub_pub_unsub.json',
                     filter_query_parameters=['pnsdk'], serializer='pn_json')
@pytest.mark.asyncio
async def test_subscribe_publish_unsubscribe(event_loop):
    pubnub_sub = PubNubAsyncio(pnconf_env_copy(), custom_event_loop=event_loop)
    pubnub_pub = PubNubAsyncio(pnconf_env_copy(), custom_event_loop=event_loop)

    await patch_pubnub(pubnub_sub)
    await patch_pubnub(pubnub_pub)

    pubnub_sub.config.uuid = 'test-subscribe-asyncio-uuid-sub'
    pubnub_pub.config.uuid = 'test-subscribe-asyncio-uuid-pub'

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
    # await callback.wait_for_disconnect()

    await pubnub_pub.stop()
    await pubnub_sub.stop()


@pn_vcr.use_cassette('tests/integrational/fixtures/asyncio/subscription/sub_pub_unsub_enc.json',
                     filter_query_parameters=['pnsdk'], serializer='pn_json')
@pytest.mark.asyncio
async def test_encrypted_subscribe_publish_unsubscribe(event_loop):
    pubnub = PubNubAsyncio(pnconf_enc_env_copy(), custom_event_loop=event_loop)
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
        await callback.wait_for_disconnect()

    await pubnub.stop()


@pn_vcr.use_cassette('tests/integrational/fixtures/asyncio/subscription/join_leave.json',
                     filter_query_parameters=['pnsdk', 'l_cg'], serializer='pn_json')
@pytest.mark.asyncio
async def test_join_leave(event_loop):
    channel = "test-subscribe-asyncio-join-leave-ch"

    pubnub = PubNubAsyncio(pnconf_env_copy(), custom_event_loop=event_loop)
    pubnub_listener = PubNubAsyncio(pnconf_env_copy(), custom_event_loop=event_loop)

    await patch_pubnub(pubnub)
    await patch_pubnub(pubnub_listener)

    pubnub.config.uuid = "test-subscribe-asyncio-messenger"
    pubnub_listener.config.uuid = "test-subscribe-asyncio-listener"

    callback_presence = VCR599Listener(1)
    callback_messages = VCR599Listener(1)

    pubnub_listener.add_listener(callback_presence)
    pubnub_listener.subscribe().channels(channel).with_presence().execute()

    await callback_presence.wait_for_connect()

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
    await callback_messages.wait_for_disconnect()

    envelope = await callback_presence.wait_for_presence_on(channel)

    assert envelope.channel == channel
    assert envelope.event == 'leave'
    assert envelope.uuid == pubnub.uuid

    pubnub_listener.unsubscribe().channels(channel).execute()
    await callback_presence.wait_for_disconnect()

    await pubnub.stop()
    await pubnub_listener.stop()


@get_sleeper('tests/integrational/fixtures/asyncio/subscription/cg_sub_unsub.json')
@pn_vcr.use_cassette('tests/integrational/fixtures/asyncio/subscription/cg_sub_unsub.json',
                     filter_query_parameters=['uuid', 'pnsdk', 'l_cg', 'l_pres'], serializer='pn_json')
@pytest.mark.asyncio
async def test_cg_subscribe_unsubscribe(event_loop, sleeper=asyncio.sleep):
    ch = "test-subscribe-asyncio-channel"
    gr = "test-subscribe-asyncio-group"

    pubnub = PubNubAsyncio(pnconf_env_copy(), custom_event_loop=event_loop)

    envelope = await pubnub.add_channel_to_channel_group().channel_group(gr).channels(ch).future()
    assert envelope.status.original_response['status'] == 200

    await sleeper(3)

    callback_messages = SubscribeListener()
    pubnub.add_listener(callback_messages)
    pubnub.subscribe().channel_groups(gr).execute()
    await callback_messages.wait_for_connect()

    pubnub.unsubscribe().channel_groups(gr).execute()
    await callback_messages.wait_for_disconnect()

    envelope = await pubnub.remove_channel_from_channel_group().channel_group(gr).channels(ch).future()
    assert envelope.status.original_response['status'] == 200

    await pubnub.stop()


@get_sleeper('tests/integrational/fixtures/asyncio/subscription/cg_sub_pub_unsub.json')
@pn_vcr.use_cassette('tests/integrational/fixtures/asyncio/subscription/cg_sub_pub_unsub.json',
                     filter_query_parameters=['uuid', 'pnsdk', 'l_cg', 'l_pres', 'l_pub'], serializer='pn_json')
@pytest.mark.asyncio
async def test_cg_subscribe_publish_unsubscribe(event_loop, sleeper=asyncio.sleep):
    ch = "test-subscribe-asyncio-channel"
    gr = "test-subscribe-asyncio-group"
    message = "hey"

    pubnub = PubNubAsyncio(pnconf_env_copy(), custom_event_loop=event_loop)

    envelope = await pubnub.add_channel_to_channel_group().channel_group(gr).channels(ch).future()
    assert envelope.status.original_response['status'] == 200

    await sleeper(1)

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
    await callback_messages.wait_for_disconnect()

    envelope = await pubnub.remove_channel_from_channel_group().channel_group(gr).channels(ch).future()
    assert envelope.status.original_response['status'] == 200

    await pubnub.stop()


@get_sleeper('tests/integrational/fixtures/asyncio/subscription/cg_join_leave.json')
@pn_vcr.use_cassette('tests/integrational/fixtures/asyncio/subscription/cg_join_leave.json',
                     filter_query_parameters=['pnsdk', 'l_cg', 'l_pres'], serializer='pn_json')
@pytest.mark.asyncio
async def test_cg_join_leave(event_loop, sleeper=asyncio.sleep):
    pubnub = PubNubAsyncio(pnconf_env_copy(), custom_event_loop=event_loop)
    pubnub_listener = PubNubAsyncio(pnconf_env_copy(), custom_event_loop=event_loop)

    pubnub.config.uuid = "test-subscribe-asyncio-messenger"
    pubnub_listener.config.uuid = "test-subscribe-asyncio-listener"

    ch = "test-subscribe-asyncio-join-leave-cg-channel"
    gr = "test-subscribe-asyncio-join-leave-cg-group"

    envelope = await pubnub.add_channel_to_channel_group().channel_group(gr).channels(ch).future()
    assert envelope.status.original_response['status'] == 200

    await sleeper(1)

    callback_messages = VCR599Listener(1)
    callback_presence = VCR599Listener(1)

    pubnub_listener.add_listener(callback_presence)
    pubnub_listener.subscribe().channel_groups(gr).with_presence().execute()
    await callback_presence.wait_for_connect()

    prs_envelope = await callback_presence.wait_for_presence_on(ch)
    assert prs_envelope.event == 'join'
    assert prs_envelope.uuid == pubnub_listener.uuid
    assert prs_envelope.channel == ch
    assert prs_envelope.subscription == gr

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
    await callback_presence.wait_for_disconnect()

    envelope = await pubnub.remove_channel_from_channel_group().channel_group(gr).channels(ch).future()
    assert envelope.status.original_response['status'] == 200

    await pubnub.stop()
    await pubnub_listener.stop()


@get_sleeper('tests/integrational/fixtures/asyncio/subscription/unsubscribe_all.json')
@pn_vcr.use_cassette('tests/integrational/fixtures/asyncio/subscription/unsubscribe_all.json',
                     filter_query_parameters=['pnsdk', 'l_cg', 'l_pres'], serializer='pn_json',
                     match_on=['method', 'scheme', 'host', 'port', 'string_list_in_path', 'string_list_in_query'])
@pytest.mark.asyncio
async def test_unsubscribe_all(event_loop, sleeper=asyncio.sleep):
    pubnub = PubNubAsyncio(pnconf_env_copy(), custom_event_loop=event_loop)

    pubnub.config.uuid = "test-subscribe-asyncio-messenger"

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

    await sleeper(1)

    callback_messages = VCR599Listener(1)
    pubnub.add_listener(callback_messages)

    pubnub.subscribe().channels([ch1, ch2, ch3]).channel_groups([gr1, gr2]).execute()
    await callback_messages.wait_for_connect()

    assert len(pubnub.get_subscribed_channels()) == 3
    assert len(pubnub.get_subscribed_channel_groups()) == 2

    pubnub.unsubscribe_all()

    await callback_messages.wait_for_disconnect()

    assert len(pubnub.get_subscribed_channels()) == 0
    assert len(pubnub.get_subscribed_channel_groups()) == 0

    envelope = await pubnub.remove_channel_from_channel_group().channel_group(gr1).channels(ch).future()
    assert envelope.status.original_response['status'] == 200
    envelope = await pubnub.remove_channel_from_channel_group().channel_group(gr2).channels(ch).future()
    assert envelope.status.original_response['status'] == 200

    await pubnub.stop()


@get_sleeper('tests/integrational/fixtures/asyncio/subscription/publish_space_id.json')
@pn_vcr.use_cassette(
    'tests/integrational/fixtures/asyncio/subscription/publish_space_id.json', serializer='pn_json',
    filter_query_parameters=['pnsdk', 'l_cg', 'l_pres'],
    match_on=['method', 'scheme', 'host', 'port', 'string_list_in_path', 'string_list_in_query'],
)
@pytest.mark.asyncio
async def test_subscribe_publish_space_id(event_loop, sleeper=asyncio.sleep):
    pubnub_sub = PubNubAsyncio(pnconf_env_copy(), custom_event_loop=event_loop)
    pubnub_pub = PubNubAsyncio(pnconf_env_copy(), custom_event_loop=event_loop)

    await patch_pubnub(pubnub_sub)
    await patch_pubnub(pubnub_pub)

    pubnub_sub.config.uuid = 'test-subscribe-asyncio-uuid-sub'
    pubnub_pub.config.uuid = 'test-subscribe-asyncio-uuid-pub'

    callback = VCR599Listener(1)
    channel = "test-subscribe-asyncio-ch"
    message = "hey"
    space_id = "HelloSpace"
    pubnub_sub.add_listener(callback)
    pubnub_sub.subscribe().channels(channel).execute()

    await callback.wait_for_connect()

    publish_future = asyncio.ensure_future(
        pubnub_pub.publish().channel(channel).message(message).space_id(space_id).future()
    )
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
    assert subscribe_envelope.space_id == space_id
    assert subscribe_envelope.timetoken > 0

    assert isinstance(publish_envelope, AsyncioEnvelope)
    assert publish_envelope.result.timetoken > 0
    assert publish_envelope.status.original_response[0] == 1

    pubnub_sub.unsubscribe().channels(channel).execute()
    # await callback.wait_for_disconnect()

    await pubnub_pub.stop()
    await pubnub_sub.stop()


@get_sleeper('tests/integrational/fixtures/asyncio/subscription/publish_message_type.json')
@pn_vcr.use_cassette(
    'tests/integrational/fixtures/asyncio/subscription/publish_message_type.json', serializer='pn_json',
    filter_query_parameters=['pnsdk', 'l_cg', 'l_pres'],
    match_on=['method', 'scheme', 'host', 'port', 'string_list_in_path', 'string_list_in_query'],
)
@pytest.mark.asyncio
async def test_subscribe_publish_message_type(event_loop, sleeper=asyncio.sleep):
    pubnub_sub = PubNubAsyncio(pnconf_env_copy(), custom_event_loop=event_loop)
    pubnub_pub = PubNubAsyncio(pnconf_env_copy(), custom_event_loop=event_loop)

    await patch_pubnub(pubnub_sub)
    await patch_pubnub(pubnub_pub)

    pubnub_sub.config.uuid = 'test-subscribe-asyncio-uuid-sub'
    pubnub_pub.config.uuid = 'test-subscribe-asyncio-uuid-pub'

    callback = VCR599Listener(1)
    channel = "test-subscribe-asyncio-ch"
    message = "hey"
    message_type = "MyOwnCustomMessageType"
    pubnub_sub.add_listener(callback)
    pubnub_sub.subscribe().channels(channel).execute()

    await callback.wait_for_connect()

    publish_future = asyncio.ensure_future(
        pubnub_pub.publish().channel(channel).message(message).message_type(message_type).future()
    )
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

    assert isinstance(subscribe_envelope.type, str)
    assert str(subscribe_envelope.type) == message_type
    assert subscribe_envelope.timetoken > 0

    assert isinstance(publish_envelope, AsyncioEnvelope)
    assert publish_envelope.result.timetoken > 0
    assert publish_envelope.status.original_response[0] == 1

    pubnub_sub.unsubscribe().channels(channel).execute()
    # await callback.wait_for_disconnect()

    await pubnub_pub.stop()
    await pubnub_sub.stop()
