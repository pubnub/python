import pytest

from pubnub.pubnub_asyncio import PubNubAsyncio, AsyncioEnvelope
from pubnub.models.consumer.message_count import PNMessageCountResult
from pubnub.models.consumer.common import PNStatus
from tests.helper import pnconf_mc_copy
from tests.integrational.vcr_helper import pn_vcr


@pytest.fixture
def pn(event_loop):
    config = pnconf_mc_copy()
    config.enable_subscribe = False
    pn = PubNubAsyncio(config, custom_event_loop=event_loop)
    yield pn
    pn.stop()


@pn_vcr.use_cassette('tests/integrational/fixtures/asyncio/message_count/single.yaml',
                     filter_query_parameters=['uuid', 'seqn', 'pnsdk', 'l_cg', 'l_pub'])
@pytest.mark.asyncio
def test_single_channel(pn):
    chan = 'unique_asyncio'
    envelope = yield from pn.publish().channel(chan).message('bla').future()
    time = envelope.result.timetoken - 10
    envelope = yield from pn.message_counts().channel(chan).channel_timetokens([time]).future()

    assert(isinstance(envelope, AsyncioEnvelope))
    assert not envelope.status.is_error()
    assert envelope.result.channels[chan] == 1
    assert isinstance(envelope.result, PNMessageCountResult)
    assert isinstance(envelope.status, PNStatus)


@pn_vcr.use_cassette('tests/integrational/fixtures/asyncio/message_count/multi.yaml',
                     filter_query_parameters=['uuid', 'seqn', 'pnsdk', 'l_cg', 'l_pub'])
@pytest.mark.asyncio
def test_multiple_channels(pn):
    chan_1 = 'unique_asyncio_1'
    chan_2 = 'unique_asyncio_2'
    chans = ','.join([chan_1, chan_2])
    envelope = yield from pn.publish().channel(chan_1).message('something').future()
    time = envelope.result.timetoken - 10
    envelope = yield from pn.message_counts().channel(chans).channel_timetokens([time, time]).future()

    assert(isinstance(envelope, AsyncioEnvelope))
    assert not envelope.status.is_error()
    assert envelope.result.channels[chan_1] == 1
    assert envelope.result.channels[chan_2] == 0
    assert isinstance(envelope.result, PNMessageCountResult)
    assert isinstance(envelope.status, PNStatus)
