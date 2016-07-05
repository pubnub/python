import asyncio
import pytest

from pubnub.models.consumer.channel_group import PNChannelGroupsAddChannelResult, PNChannelGroupsListResult, \
    PNChannelGroupsRemoveChannelResult, PNChannelGroupsRemoveGroupResult
from pubnub.pubnub_asyncio import PubNubAsyncio
from tests import helper
from tests.helper import pnconf


@pytest.mark.asyncio
async def test_add_remove_single_channel(event_loop):
    pubnub = PubNubAsyncio(pnconf, custom_event_loop=event_loop)

    ch = helper.gen_channel("herenow-unit")
    gr = helper.gen_channel("herenow-unit")

    # add
    env = await pubnub.add_channel_to_channel_group() \
        .channels(ch).channel_group(gr).future()

    assert isinstance(env.result, PNChannelGroupsAddChannelResult)

    await asyncio.sleep(1)

    # list
    env = await pubnub.list_channels_in_channel_group().channel_group(gr).future()
    assert isinstance(env.result, PNChannelGroupsListResult)
    assert len(env.result.channels) == 1
    assert env.result.channels[0] == ch

    # remove
    env = await pubnub.remove_channel_from_channel_group() \
        .channels(ch).channel_group(gr).future()

    assert isinstance(env.result, PNChannelGroupsRemoveChannelResult)

    await asyncio.sleep(1)

    # list
    env = await pubnub.list_channels_in_channel_group().channel_group(gr).future()
    assert isinstance(env.result, PNChannelGroupsListResult)
    assert len(env.result.channels) == 0

    pubnub.stop()


@pytest.mark.asyncio
async def test_add_remove_multiple_channels(event_loop):
    pubnub = PubNubAsyncio(pnconf, custom_event_loop=event_loop)

    ch1 = helper.gen_channel("herenow-unit")
    ch2 = helper.gen_channel("herenow-unit")
    gr = helper.gen_channel("herenow-unit")

    # add
    env = await pubnub.add_channel_to_channel_group() \
        .channels([ch1, ch2]).channel_group(gr).future()

    assert isinstance(env.result, PNChannelGroupsAddChannelResult)

    await asyncio.sleep(1)

    # list
    env = await pubnub.list_channels_in_channel_group().channel_group(gr).future()
    assert isinstance(env.result, PNChannelGroupsListResult)
    assert len(env.result.channels) == 2
    assert ch1 in env.result.channels
    assert ch2 in env.result.channels

    # remove
    env = await pubnub.remove_channel_from_channel_group() \
        .channels([ch1, ch2]).channel_group(gr).future()

    assert isinstance(env.result, PNChannelGroupsRemoveChannelResult)

    await asyncio.sleep(1)

    # list
    env = await pubnub.list_channels_in_channel_group().channel_group(gr).future()
    assert isinstance(env.result, PNChannelGroupsListResult)
    assert len(env.result.channels) == 0

    pubnub.stop()


@pytest.mark.asyncio
async def test_add_channel_remove_group(event_loop):
    pubnub = PubNubAsyncio(pnconf, custom_event_loop=event_loop)

    ch = helper.gen_channel("herenow-unit")
    gr = helper.gen_channel("herenow-unit")

    # add
    env = await pubnub.add_channel_to_channel_group() \
        .channels(ch).channel_group(gr).future()

    assert isinstance(env.result, PNChannelGroupsAddChannelResult)

    await asyncio.sleep(1)

    # list
    env = await pubnub.list_channels_in_channel_group().channel_group(gr).future()
    assert isinstance(env.result, PNChannelGroupsListResult)
    assert len(env.result.channels) == 1
    assert env.result.channels[0] == ch

    # remove group
    env = await pubnub.remove_channel_group().channel_group(gr).future()

    assert isinstance(env.result, PNChannelGroupsRemoveGroupResult)

    await asyncio.sleep(1)

    # list
    env = await pubnub.list_channels_in_channel_group().channel_group(gr).future()
    assert isinstance(env.result, PNChannelGroupsListResult)
    assert len(env.result.channels) == 0

    pubnub.stop()
