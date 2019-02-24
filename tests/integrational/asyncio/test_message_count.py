import asyncio
import pytest

from pubnub.pnconfiguration import PNConfiguration
from pubnub.pubnub_asyncio import PubNubAsyncio, AsyncioEnvelope
from pubnub.models.consumer.message_count import PNMessageCountResult
from pubnub.models.consumer.common import PNStatus


@pytest.fixture
def pn(event_loop):
    config = PNConfiguration()
    config.publish_key = 'demo-36'
    config.subscribe_key = 'demo-36'
    config.origin = 'balancer1g.bronze.aws-pdx-1.ps.pn'
    config.enable_subscribe = False
    pn = PubNubAsyncio(config, custom_event_loop=event_loop)
    yield pn
    pn.stop()


@pytest.mark.asyncio
async def test_single_channel(pn):
    chan = 'unique_asyncio'
    envelope = await pn.publish().channel(chan).message('bla').future()
    time = envelope.result.timetoken - 1
    envelope = await pn.message_count().channel(chan).channel_timetokens([time]).future()

    assert(isinstance(envelope, AsyncioEnvelope))
    assert not envelope.status.is_error()
    assert envelope.result.channels[chan] == 1
    assert isinstance(envelope.result, PNMessageCountResult)
    assert isinstance(envelope.status, PNStatus)


@pytest.mark.asyncio
async def test_multiple_channels(pn):
    chan_1 = 'unique_asyncio_1'
    chan_2 = 'unique_asyncio_2'
    chans = ','.join([chan_1, chan_2])
    envelope = await pn.publish().channel(chan_1).message('something').future()
    time = envelope.result.timetoken - 1
    envelope = await pn.message_count().channel(chans).channel_timetokens([time, time]).future()

    assert(isinstance(envelope, AsyncioEnvelope))
    assert not envelope.status.is_error()
    assert envelope.result.channels[chan_1] == 1
    assert envelope.result.channels[chan_2] == 0
    assert isinstance(envelope.result, PNMessageCountResult)
    assert isinstance(envelope.status, PNStatus)
