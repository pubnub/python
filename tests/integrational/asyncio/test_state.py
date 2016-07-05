import pytest

from pubnub.pubnub_asyncio import PubNubAsyncio
from tests import helper
from tests.helper import pnconf


@pytest.mark.asyncio
async def test_single_channel(event_loop):
    pubnub = PubNubAsyncio(pnconf, custom_event_loop=event_loop)
    ch = helper.gen_channel("herenow-unit")
    state = {"name": "Alex", "count": 5}

    env = await pubnub.set_state() \
        .channels(ch) \
        .state(state) \
        .future()

    assert env.result.state['name'] == "Alex"
    assert env.result.state['count'] == 5

    env = await pubnub.get_state() \
        .channels(ch) \
        .future()

    assert env.result.channels[ch]['name'] == "Alex"
    assert env.result.channels[ch]['count'] == 5

    pubnub.stop()


@pytest.mark.asyncio
async def test_multiple_channels(event_loop):
    pubnub = PubNubAsyncio(pnconf, custom_event_loop=event_loop)
    ch1 = helper.gen_channel("herenow-unit")
    ch2 = helper.gen_channel("herenow-unit")
    state = {"name": "Alex", "count": 5}

    env = await pubnub.set_state() \
        .channels([ch1, ch2]) \
        .state(state) \
        .future()

    assert env.result.state['name'] == "Alex"
    assert env.result.state['count'] == 5

    env = await pubnub.get_state() \
        .channels([ch1, ch2]) \
        .future()

    assert env.result.channels[ch1]['name'] == "Alex"
    assert env.result.channels[ch2]['name'] == "Alex"
    assert env.result.channels[ch1]['count'] == 5
    assert env.result.channels[ch2]['count'] == 5

    pubnub.stop()
