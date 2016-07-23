import asyncio
import pytest

from pubnub.pubnub_asyncio import PubNubAsyncio, SubscribeListener
from tests import helper
from tests.helper import pnconf_sub_copy


@pytest.mark.asyncio
async def test_single_channel(event_loop):
    pubnub = PubNubAsyncio(pnconf_sub_copy(), custom_event_loop=event_loop)
    ch = helper.gen_channel("wherenow-asyncio-channel")
    uuid = helper.gen_channel("wherenow-asyncio-uuid")
    pubnub.config.uuid = uuid

    callback = SubscribeListener()
    pubnub.add_listener(callback)
    pubnub.subscribe().channels(ch).execute()

    await callback.wait_for_connect()

    await asyncio.sleep(2)

    env = await pubnub.where_now() \
        .uuid(uuid) \
        .future()

    channels = env.result.channels

    assert len(channels) == 1
    assert channels[0] == ch

    pubnub.unsubscribe().channels(ch).execute()
    await callback.wait_for_disconnect()

    pubnub.stop()


@pytest.mark.asyncio
async def test_multiple_channels(event_loop):
    pubnub = PubNubAsyncio(pnconf_sub_copy(), custom_event_loop=event_loop)

    ch1 = helper.gen_channel("here-now")
    ch2 = helper.gen_channel("here-now")
    uuid = helper.gen_channel("wherenow-asyncio-uuid")
    pubnub.config.uuid = uuid

    callback = SubscribeListener()
    pubnub.add_listener(callback)
    pubnub.subscribe().channels([ch1, ch2]).execute()

    await callback.wait_for_connect()

    await asyncio.sleep(5)

    env = await pubnub.where_now() \
        .uuid(uuid) \
        .future()

    channels = env.result.channels

    assert len(channels) == 2
    assert ch1 in channels
    assert ch2 in channels

    pubnub.unsubscribe().channels([ch1, ch2]).execute()
    await callback.wait_for_disconnect()

    pubnub.stop()
