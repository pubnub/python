import asyncio
import pytest

from pubnub.models.consumer.presence import PNHereNowResult
from pubnub.pubnub_asyncio import PubNubAsyncio
from tests.helper import pnconf_sub_copy, pnconf_pam_copy
from tests.integrational.vcr_asyncio_sleeper import get_sleeper, VCR599Listener
from tests.integrational.vcr_helper import pn_vcr


@get_sleeper('tests/integrational/fixtures/asyncio/here_now/single_channel.yaml')
@pn_vcr.use_cassette('tests/integrational/fixtures/asyncio/here_now/single_channel.yaml',
                     filter_query_parameters=['tr', 'uuid', 'pnsdk', 'l_pres'])
@pytest.mark.asyncio
def test_single_channel(event_loop, sleeper=asyncio.sleep):
    pubnub = PubNubAsyncio(pnconf_sub_copy(), custom_event_loop=event_loop)
    pubnub.config.uuid = 'test-here-now-asyncio-uuid1'
    ch = "test-here-now-asyncio-ch"

    callback = VCR599Listener(1)
    pubnub.add_listener(callback)
    pubnub.subscribe().channels(ch).execute()

    yield from callback.wait_for_connect()

    yield from sleeper(5)

    env = yield from pubnub.here_now() \
        .channels(ch) \
        .include_uuids(True) \
        .future()

    assert env.result.total_channels == 1
    assert env.result.total_occupancy >= 1

    channels = env.result.channels

    assert len(channels) == 1
    assert channels[0].occupancy == 1
    assert channels[0].occupants[0].uuid == pubnub.uuid

    result = yield from pubnub.here_now() \
        .channels(ch) \
        .include_state(True) \
        .result()

    assert result.total_channels == 1
    assert result.total_occupancy == 1

    pubnub.unsubscribe().channels(ch).execute()
    yield from callback.wait_for_disconnect()

    pubnub.stop()


@get_sleeper('tests/integrational/fixtures/asyncio/here_now/multiple_channels.yaml')
@pn_vcr.use_cassette('tests/integrational/fixtures/asyncio/here_now/multiple_channels.yaml',
                     filter_query_parameters=['pnsdk', 'l_pres'],
                     match_on=['method', 'scheme', 'host', 'port', 'string_list_in_path', 'query'],
                     match_on_kwargs={
                         'string_list_in_path': {
                             'positions': [4, 6]
                         }
                     })
@pytest.mark.asyncio
def test_multiple_channels(event_loop, sleeper=asyncio.sleep):
    pubnub = PubNubAsyncio(pnconf_sub_copy(), custom_event_loop=event_loop)
    pubnub.config.uuid = 'test-here-now-asyncio-uuid1'

    ch1 = "test-here-now-asyncio-ch1"
    ch2 = "test-here-now-asyncio-ch2"

    callback = VCR599Listener(1)
    pubnub.add_listener(callback)
    pubnub.subscribe().channels([ch1, ch2]).execute()

    yield from callback.wait_for_connect()

    yield from sleeper(5)
    env = yield from pubnub.here_now() \
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

    result = yield from pubnub.here_now() \
        .channels([ch1, ch2]) \
        .include_state(True) \
        .result()

    assert result.total_channels == 2

    pubnub.unsubscribe().channels([ch1, ch2]).execute()
    yield from callback.wait_for_disconnect()

    pubnub.stop()


@get_sleeper('tests/integrational/fixtures/asyncio/here_now/global.yaml')
@pn_vcr.use_cassette('tests/integrational/fixtures/asyncio/here_now/global.yaml',
                     filter_query_parameters=['pnsdk', 'l_pres'],
                     match_on=['method', 'scheme', 'host', 'port', 'string_list_in_path', 'query'],
                     match_on_kwargs={
                         'string_list_in_path': {
                             'positions': [4]
                         }
                     })
@pytest.mark.asyncio
def test_global(event_loop, sleeper=asyncio.sleep):
    pubnub = PubNubAsyncio(pnconf_sub_copy(), custom_event_loop=event_loop)
    pubnub.config.uuid = 'test-here-now-asyncio-uuid1'

    ch1 = "test-here-now-asyncio-ch1"
    ch2 = "test-here-now-asyncio-ch2"

    callback = VCR599Listener(1)
    pubnub.add_listener(callback)
    pubnub.subscribe().channels([ch1, ch2]).execute()

    yield from callback.wait_for_connect()

    yield from sleeper(5)

    env = yield from pubnub.here_now().future()

    assert env.result.total_channels >= 2
    assert env.result.total_occupancy >= 1

    pubnub.unsubscribe().channels([ch1, ch2]).execute()
    yield from callback.wait_for_disconnect()

    pubnub.stop()


@pytest.mark.asyncio
def test_here_now_super_call(event_loop):
    pubnub = PubNubAsyncio(pnconf_pam_copy(), custom_event_loop=event_loop)
    pubnub.config.uuid = 'test-here-now-asyncio-uuid1'

    env = yield from pubnub.here_now().future()
    assert isinstance(env.result, PNHereNowResult)

    env = yield from pubnub.here_now().channel_groups("gr").include_uuids(True).include_state(True).future()
    assert isinstance(env.result, PNHereNowResult)

    env = yield from pubnub.here_now().channels('ch.bar*').channel_groups("gr.k").future()
    assert isinstance(env.result, PNHereNowResult)

    env = yield from pubnub.here_now().channels(['ch.bar*', 'ch2']).channel_groups("gr.k").future()
    assert isinstance(env.result, PNHereNowResult)

    pubnub.stop()
