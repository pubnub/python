import asyncio
import pytest

from pubnub.pubnub_asyncio import PubNubAsyncio, SubscribeListener
from tests import helper
from tests.helper import pnconf_sub_copy


@pytest.mark.asyncio
async def test_single_channel(event_loop):
    pubnub = PubNubAsyncio(pnconf_sub_copy(), custom_event_loop=event_loop)
    ch = helper.gen_channel("herenow-unit")

    callback = SubscribeListener()
    pubnub.add_listener(callback)
    pubnub.subscribe().channels(ch).execute()

    await callback.wait_for_connect()

    await asyncio.sleep(2)

    env = await pubnub.here_now() \
        .channels(ch) \
        .include_uuids(True) \
        .future()

    assert env.result.total_channels == 1
    assert env.result.total_occupancy >= 1

    channels = env.result.channels

    assert len(channels) == 1
    assert channels[0].occupancy == 1
    assert channels[0].occupants[0].uuid == pubnub.uuid

    pubnub.unsubscribe().channels(ch).execute()
    await callback.wait_for_disconnect()

    pubnub.stop()


@pytest.mark.asyncio
async def test_multiple_channels(event_loop):
    pubnub = PubNubAsyncio(pnconf_sub_copy(), custom_event_loop=event_loop)

    ch1 = helper.gen_channel("here-now")
    ch2 = helper.gen_channel("here-now")

    callback = SubscribeListener()
    pubnub.add_listener(callback)
    pubnub.subscribe().channels([ch1, ch2]).execute()

    await callback.wait_for_connect()

    await asyncio.sleep(4)
    env = await pubnub.here_now() \
        .channels([ch1, ch2]) \
        .future()

    assert env.result.total_channels == 2
    assert env.result.total_occupancy >= 1

    channels = env.result.channels

    assert len(channels) == 2
    assert channels[0].occupancy == 1
    assert channels[0].occupants[0].uuid == pubnub.uuid
    assert channels[1].occupancy == 1
    assert channels[1].occupants[0].uuid == pubnub.uuid

    pubnub.unsubscribe().channels([ch1, ch2]).execute()
    await callback.wait_for_disconnect()

    pubnub.stop()


@pytest.mark.asyncio
async def test_global(event_loop):
    pubnub = PubNubAsyncio(pnconf_sub_copy(), custom_event_loop=event_loop)

    ch1 = helper.gen_channel("here-now")
    ch2 = helper.gen_channel("here-now")

    callback = SubscribeListener()
    pubnub.add_listener(callback)
    pubnub.subscribe().channels([ch1, ch2]).execute()

    await callback.wait_for_connect()

    await asyncio.sleep(2)

    env = await pubnub.here_now().future()

    assert env.result.total_channels >= 2
    assert env.result.total_occupancy >= 1

    pubnub.unsubscribe().channels([ch1, ch2]).execute()
    await callback.wait_for_disconnect()

    pubnub.stop()
