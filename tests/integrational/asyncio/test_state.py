import pytest

from pubnub.pubnub_asyncio import PubNubAsyncio
from tests import helper
from tests.helper import pnconf, pnconf_copy
from tests.integrational.vcr_helper import pn_vcr


@pn_vcr.use_cassette(
        'tests/integrational/fixtures/asyncio/state/single_channel.yaml',
        filter_query_parameters=['uuid'],
        match_on=['method', 'host', 'path', 'state_object_in_query'])
@pytest.mark.asyncio
def test_single_channel(event_loop):
    pubnub = PubNubAsyncio(pnconf_copy(), custom_event_loop=event_loop)
    ch = 'test-state-asyncio-ch'
    pubnub.config.uuid = 'test-state-asyncio-uuid'
    state = {"name": "Alex", "count": 5}

    env = yield from pubnub.set_state() \
        .channels(ch) \
        .state(state) \
        .future()

    assert env.result.state['name'] == "Alex"
    assert env.result.state['count'] == 5

    env = yield from pubnub.get_state() \
        .channels(ch) \
        .future()

    assert env.result.channels[ch]['name'] == "Alex"
    assert env.result.channels[ch]['count'] == 5

    pubnub.stop()


@pn_vcr.use_cassette(
        'tests/integrational/fixtures/asyncio/state/multiple_channel.yaml',
        filter_query_parameters=['uuid'],
        match_on=['method', 'host', 'path', 'state_object_in_query'])
@pytest.mark.asyncio
def test_multiple_channels(event_loop):
    pubnub = PubNubAsyncio(pnconf, custom_event_loop=event_loop)
    ch1 = 'test-state-asyncio-ch1'
    ch2 = 'test-state-asyncio-ch2'
    pubnub.config.uuid = 'test-state-asyncio-uuid'
    state = {"name": "Alex", "count": 5}

    env = yield from pubnub.set_state() \
        .channels([ch1, ch2]) \
        .state(state) \
        .future()

    assert env.result.state['name'] == "Alex"
    assert env.result.state['count'] == 5

    env = yield from pubnub.get_state() \
        .channels([ch1, ch2]) \
        .future()

    assert env.result.channels[ch1]['name'] == "Alex"
    assert env.result.channels[ch2]['name'] == "Alex"
    assert env.result.channels[ch1]['count'] == 5
    assert env.result.channels[ch2]['count'] == 5

    pubnub.stop()
