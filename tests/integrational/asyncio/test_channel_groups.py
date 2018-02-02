import asyncio
import pytest

from pubnub.models.consumer.channel_group import PNChannelGroupsAddChannelResult, PNChannelGroupsListResult, \
    PNChannelGroupsRemoveChannelResult, PNChannelGroupsRemoveGroupResult
from pubnub.pubnub_asyncio import PubNubAsyncio
from tests.helper import pnconf, pnconf_copy, pnconf_pam_copy
from tests.integrational.vcr_asyncio_sleeper import get_sleeper
from tests.integrational.vcr_helper import pn_vcr


@get_sleeper('tests/integrational/fixtures/asyncio/groups/add_remove_single_channel.yaml')
@pn_vcr.use_cassette('tests/integrational/fixtures/asyncio/groups/add_remove_single_channel.yaml',
                     filter_query_parameters=['uuid', 'pnsdk', 'l_cg', 'l_pub'])
@pytest.mark.asyncio
def test_add_remove_single_channel(event_loop, sleeper=asyncio.sleep):
    pubnub = PubNubAsyncio(pnconf_copy(), custom_event_loop=event_loop)
    pubnub.config.uuid = 'test-channel-group-asyncio-uuid1'

    ch = "test-channel-groups-asyncio-ch"
    gr = "test-channel-groups-asyncio-cg"

    yield from pubnub.publish().channel(ch).message("hey").future()
    # add
    env = yield from pubnub.add_channel_to_channel_group() \
        .channels(ch).channel_group(gr).future()

    assert isinstance(env.result, PNChannelGroupsAddChannelResult)

    yield from sleeper(1)

    # list
    env = yield from pubnub.list_channels_in_channel_group().channel_group(gr).future()
    assert isinstance(env.result, PNChannelGroupsListResult)
    assert len(env.result.channels) == 1
    assert env.result.channels[0] == ch

    # remove
    env = yield from pubnub.remove_channel_from_channel_group() \
        .channels(ch).channel_group(gr).future()

    assert isinstance(env.result, PNChannelGroupsRemoveChannelResult)

    yield from sleeper(1)

    # change uuid to let vcr to distinguish list requests
    pubnub.config.uuid = 'test-channel-group-asyncio-uuid2'

    # list
    env = yield from pubnub.list_channels_in_channel_group().channel_group(gr).future()
    assert isinstance(env.result, PNChannelGroupsListResult)
    assert len(env.result.channels) == 0

    pubnub.stop()


@get_sleeper('tests/integrational/fixtures/asyncio/groups/add_remove_multiple_channels.yaml')
@pn_vcr.use_cassette('tests/integrational/fixtures/asyncio/groups/add_remove_multiple_channels.yaml',
                     filter_query_parameters=['uuid', 'pnsdk', 'l_cg', 'l_pub'])
@pytest.mark.asyncio
def test_add_remove_multiple_channels(event_loop, sleeper=asyncio.sleep):
    pubnub = PubNubAsyncio(pnconf, custom_event_loop=event_loop)

    ch1 = "channel-groups-tornado-ch1"
    ch2 = "channel-groups-tornado-ch2"
    gr = "channel-groups-tornado-cg"

    # add
    env = yield from pubnub.add_channel_to_channel_group() \
        .channels([ch1, ch2]).channel_group(gr).future()

    assert isinstance(env.result, PNChannelGroupsAddChannelResult)

    yield from sleeper(1)

    # list
    env = yield from pubnub.list_channels_in_channel_group().channel_group(gr).future()
    assert isinstance(env.result, PNChannelGroupsListResult)
    assert len(env.result.channels) == 2
    assert ch1 in env.result.channels
    assert ch2 in env.result.channels

    # remove
    env = yield from pubnub.remove_channel_from_channel_group() \
        .channels([ch1, ch2]).channel_group(gr).future()

    assert isinstance(env.result, PNChannelGroupsRemoveChannelResult)

    yield from sleeper(1)

    # list
    env = yield from pubnub.list_channels_in_channel_group().channel_group(gr).future()
    assert isinstance(env.result, PNChannelGroupsListResult)
    assert len(env.result.channels) == 0

    pubnub.stop()


@get_sleeper('tests/integrational/fixtures/asyncio/groups/add_channel_remove_group.yaml')
@pn_vcr.use_cassette('tests/integrational/fixtures/asyncio/groups/add_channel_remove_group.yaml',
                     filter_query_parameters=['uuid', 'pnsdk', 'l_cg', 'l_pub'])
@pytest.mark.asyncio
def test_add_channel_remove_group(event_loop, sleeper=asyncio.sleep):
    pubnub = PubNubAsyncio(pnconf, custom_event_loop=event_loop)

    ch = "channel-groups-tornado-ch"
    gr = "channel-groups-tornado-cg"

    # add
    env = yield from pubnub.add_channel_to_channel_group() \
        .channels(ch).channel_group(gr).future()

    assert isinstance(env.result, PNChannelGroupsAddChannelResult)

    yield from sleeper(1)

    # list
    env = yield from pubnub.list_channels_in_channel_group().channel_group(gr).future()
    assert isinstance(env.result, PNChannelGroupsListResult)
    assert len(env.result.channels) == 1
    assert env.result.channels[0] == ch

    # remove group
    env = yield from pubnub.remove_channel_group().channel_group(gr).future()

    assert isinstance(env.result, PNChannelGroupsRemoveGroupResult)

    yield from sleeper(1)

    # list
    env = yield from pubnub.list_channels_in_channel_group().channel_group(gr).future()
    assert isinstance(env.result, PNChannelGroupsListResult)
    assert len(env.result.channels) == 0

    pubnub.stop()


@pytest.mark.asyncio
def test_super_call(event_loop):
    pubnub = PubNubAsyncio(pnconf_pam_copy(), custom_event_loop=event_loop)

    ch = "channel-groups-torna|do-ch"
    gr = "channel-groups-torna|do-cg"
    pubnub.config.auth = "h.e|l%l,0"

    # add
    env = yield from pubnub.add_channel_to_channel_group() \
        .channels(ch).channel_group(gr).future()

    assert isinstance(env.result, PNChannelGroupsAddChannelResult)

    # list
    env = yield from pubnub.list_channels_in_channel_group().channel_group(gr).future()
    assert isinstance(env.result, PNChannelGroupsListResult)

    # remove channel
    env = yield from pubnub.remove_channel_from_channel_group().channel_group(gr).channels(ch).future()
    assert isinstance(env.result, PNChannelGroupsRemoveChannelResult)

    # remove group
    env = yield from pubnub.remove_channel_group().channel_group(gr).future()
    assert isinstance(env.result, PNChannelGroupsRemoveGroupResult)

    # list
    env = yield from pubnub.list_channels_in_channel_group().channel_group(gr).future()
    assert isinstance(env.result, PNChannelGroupsListResult)

    pubnub.stop()
