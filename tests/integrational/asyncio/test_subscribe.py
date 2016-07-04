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
    pubnub = PubNubAsyncio(pnconf_sub_copy(), custom_event_loop=event_loop)

    callback = SubscribeListener()
    pubnub.add_listener(callback)
    pubnub.subscribe().channels("ch1").execute()

    await callback.wait_for_connect()

    pubnub.unsubscribe().channels("ch1").execute()
    await callback.wait_for_disconnect()

    pubnub.stop()


@pytest.mark.asyncio
async def test_subscribe_publish_unsubscribe(event_loop):
    pubnub = PubNubAsyncio(pnconf_sub_copy(), custom_event_loop=event_loop)

    callback = SubscribeListener()
    channel = "ch1"
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
    channel = "ch1"
    message = "hey"

    pubnub = PubNubAsyncio(pnconf_sub_copy(), custom_event_loop=event_loop)
    pubnub_listener = PubNubAsyncio(pnconf_sub_copy(), custom_event_loop=event_loop)

    pubnub.config.uuid = helper.gen_channel("messenger")
    pubnub_listener.config.uuid = helper.gen_channel("listener")

    callback_presence = SubscribeListener()
    callback_messages = SubscribeListener()

    pubnub_listener.add_listener(callback_presence)
    pubnub_listener.subscribe().channels("ch1").with_presence().execute()

    await callback_presence.wait_for_connect()

    envelope = await callback_presence.wait_for_presence_on("ch1")
    assert envelope.actual_channel == "ch1-pnpres"
    assert envelope.event == 'join'
    assert envelope.uuid == pubnub_listener.uuid

    pubnub.add_listener(callback_messages)
    pubnub.subscribe().channels("ch1").execute()
    await callback_messages.wait_for_connect()

    envelope = await callback_presence.wait_for_presence_on("ch1")
    assert envelope.actual_channel == "ch1-pnpres"
    assert envelope.event == 'join'
    assert envelope.uuid == pubnub.uuid

    pubnub.unsubscribe().channels("ch1").execute()
    await callback_messages.wait_for_disconnect()

    envelope = await callback_presence.wait_for_presence_on("ch1")
    assert envelope.actual_channel == "ch1-pnpres"
    assert envelope.event == 'leave'
    assert envelope.uuid == pubnub.uuid

    pubnub_listener.unsubscribe().channels("ch1").execute()
    await callback_presence.wait_for_disconnect()

    pubnub.stop()
