import logging

import asyncio
import pytest
import pubnub as pn
from pubnub.models.consumer.pubsub import PNMessageResult
from pubnub.pubnub_asyncio import PubNubAsyncio, AsyncioEnvelope
from tests import helper
from tests.helper import pnconf_sub_copy
from tests.integrational.native.native_helper import SubscribeListener

pn.set_stream_logger('pubnub', logging.DEBUG)


@pytest.mark.asyncio
async def test_subscribe_unsubscribe(event_loop):
    channel = helper.gen_channel("test-sub-unsub")

    pubnub = PubNubAsyncio(pnconf_sub_copy(), custom_event_loop=event_loop)

    callback = SubscribeListener()
    pubnub.add_listener(callback)
    pubnub.subscribe().channels(channel).execute()

    await callback.wait_for_connect()

    pubnub.unsubscribe().channels(channel).execute()
    await callback.wait_for_disconnect()

    pubnub.stop()


@pytest.mark.asyncio
async def test_subscribe_publish_unsubscribe(event_loop):
    pubnub = PubNubAsyncio(pnconf_sub_copy(), custom_event_loop=event_loop)

    callback = SubscribeListener()
    channel = helper.gen_channel("test-sub-pub-unsub")
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
    assert subscribe_envelope.actual_channel == channel
    assert subscribe_envelope.subscribed_channel == channel
    assert subscribe_envelope.message == message
    assert subscribe_envelope.timetoken > 0

    assert isinstance(publish_envelope, AsyncioEnvelope)
    assert publish_envelope.result.timetoken > 0
    assert publish_envelope.status.original_response[0] == 1

    pubnub.unsubscribe().channels(channel).execute()
    await callback.wait_for_disconnect()

    pubnub.stop()


@pytest.mark.asyncio
async def test_join_leave(event_loop):
    channel = helper.gen_channel("test-subscribe-join-leave")
    presence_channel = "%s-pnpres" % channel

    pubnub = PubNubAsyncio(pnconf_sub_copy(), custom_event_loop=event_loop)
    pubnub_listener = PubNubAsyncio(pnconf_sub_copy(), custom_event_loop=event_loop)

    pubnub.config.uuid = helper.gen_channel("messenger")
    pubnub_listener.config.uuid = helper.gen_channel("listener")

    callback_presence = SubscribeListener()
    callback_messages = SubscribeListener()

    pubnub_listener.add_listener(callback_presence)
    pubnub_listener.subscribe().channels(channel).with_presence().execute()

    await callback_presence.wait_for_connect()

    envelope = await callback_presence.wait_for_presence_on(channel)
    assert envelope.actual_channel == presence_channel
    assert envelope.event == 'join'
    assert envelope.uuid == pubnub_listener.uuid

    pubnub.add_listener(callback_messages)
    pubnub.subscribe().channels(channel).execute()
    await callback_messages.wait_for_connect()

    envelope = await callback_presence.wait_for_presence_on(channel)
    assert envelope.actual_channel == presence_channel
    assert envelope.event == 'join'
    assert envelope.uuid == pubnub.uuid

    pubnub.unsubscribe().channels(channel).execute()
    await callback_messages.wait_for_disconnect()

    envelope = await callback_presence.wait_for_presence_on(channel)
    assert envelope.actual_channel == presence_channel
    assert envelope.event == 'leave'
    assert envelope.uuid == pubnub.uuid

    pubnub_listener.unsubscribe().channels(channel).execute()
    await callback_presence.wait_for_disconnect()

    pubnub.stop()
    pubnub_listener.stop()


@pytest.mark.asyncio
async def test_cg_subscribe_unsubscribe(event_loop):
    ch = helper.gen_channel("test-subscribe-unsubscribe-channel")
    gr = helper.gen_channel("test-subscribe-unsubscribe-group")

    pubnub = PubNubAsyncio(pnconf_sub_copy(), custom_event_loop=event_loop)

    envelope = await pubnub.add_channel_to_channel_group().channel_group(gr).channels(ch).future()
    assert envelope.status.original_response['status'] == 200

    await asyncio.sleep(1)

    callback_messages = SubscribeListener()
    pubnub.add_listener(callback_messages)
    pubnub.subscribe().channel_groups(gr).execute()
    await callback_messages.wait_for_connect()

    pubnub.unsubscribe().channel_groups(gr).execute()
    await callback_messages.wait_for_disconnect()

    envelope = await pubnub.remove_channel_from_channel_group().channel_group(gr).channels(ch).future()
    assert envelope.status.original_response['status'] == 200

    pubnub.stop()


@pytest.mark.asyncio
async def test_cg_subscribe_publish_unsubscribe(event_loop):
    ch = helper.gen_channel("test-subscribe-unsubscribe-channel")
    gr = helper.gen_channel("test-subscribe-unsubscribe-group")
    message = "hey"

    pubnub = PubNubAsyncio(pnconf_sub_copy(), custom_event_loop=event_loop)

    envelope = await pubnub.add_channel_to_channel_group().channel_group(gr).channels(ch).future()
    assert envelope.status.original_response['status'] == 200

    await asyncio.sleep(1)

    callback_messages = SubscribeListener()
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

    assert sub_envelope.actual_channel == ch
    assert sub_envelope.subscribed_channel == gr
    assert sub_envelope.message == message

    pubnub.unsubscribe().channel_groups(gr).execute()
    await callback_messages.wait_for_disconnect()

    envelope = await pubnub.remove_channel_from_channel_group().channel_group(gr).channels(ch).future()
    assert envelope.status.original_response['status'] == 200

    pubnub.stop()


@pytest.mark.asyncio
async def test_cg_join_leave(event_loop):
    pubnub = PubNubAsyncio(pnconf_sub_copy(), custom_event_loop=event_loop)
    pubnub_listener = PubNubAsyncio(pnconf_sub_copy(), custom_event_loop=event_loop)

    pubnub.config.uuid = helper.gen_channel("messenger")
    pubnub_listener.config.uuid = helper.gen_channel("listener")

    ch = helper.gen_channel("test-subscribe-unsubscribe-channel")
    gr = helper.gen_channel("test-subscribe-unsubscribe-group")

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
    assert prs_envelope.actual_channel == ch + "-pnpres"
    assert prs_envelope.subscribed_channel == gr + "-pnpres"

    pubnub.add_listener(callback_messages)
    pubnub.subscribe().channel_groups(gr).execute()

    callback_messages_future = asyncio.ensure_future(callback_messages.wait_for_connect())
    presence_messages_future= asyncio.ensure_future(callback_presence.wait_for_presence_on(ch))
    await asyncio.wait([callback_messages_future, presence_messages_future])
    prs_envelope = presence_messages_future.result()

    assert prs_envelope.event == 'join'
    assert prs_envelope.uuid == pubnub.uuid
    assert prs_envelope.actual_channel == ch + "-pnpres"
    assert prs_envelope.subscribed_channel == gr + "-pnpres"

    pubnub.unsubscribe().channel_groups(gr).execute()

    callback_messages_future = asyncio.ensure_future(callback_messages.wait_for_disconnect())
    presence_messages_future = asyncio.ensure_future(callback_presence.wait_for_presence_on(ch))
    await asyncio.wait([callback_messages_future, presence_messages_future])
    prs_envelope = presence_messages_future.result()

    assert prs_envelope.event == 'leave'
    assert prs_envelope.uuid == pubnub.uuid
    assert prs_envelope.actual_channel == ch + "-pnpres"
    assert prs_envelope.subscribed_channel == gr + "-pnpres"

    pubnub_listener.unsubscribe().channel_groups(gr).execute()
    await callback_presence.wait_for_disconnect()

    envelope = await pubnub.remove_channel_from_channel_group().channel_group(gr).channels(ch).future()
    assert envelope.status.original_response['status'] == 200

    pubnub.stop()
    pubnub_listener.stop()
