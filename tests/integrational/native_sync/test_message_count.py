import pytest

from pubnub.pubnub import PubNub
from pubnub.models.consumer.message_count import PNMessageCountResult
from pubnub.models.consumer.common import PNStatus
from pubnub.structures import Envelope
from tests.helper import pnconf_mc_copy


@pytest.fixture
def pn(event_loop):
    config = pnconf_mc_copy()
    config.enable_subscribe = False
    return PubNub(config)


def test_single_channel(pn):
    chan = 'unique_sync'
    envelope = pn.publish().channel(chan).message('bla').sync()
    time = envelope.result.timetoken - 1
    envelope = pn.message_count().channel(chan).channel_timetokens([time]).sync()

    assert(isinstance(envelope, Envelope))
    assert not envelope.status.is_error()
    assert envelope.result.channels[chan] == 1
    assert isinstance(envelope.result, PNMessageCountResult)
    assert isinstance(envelope.status, PNStatus)


def test_multiple_channels(pn):
    chan_1 = 'unique_sync_1'
    chan_2 = 'unique_sync_2'
    chans = ','.join([chan_1, chan_2])
    envelope = pn.publish().channel(chan_1).message('something').sync()
    time = envelope.result.timetoken - 1
    envelope = pn.message_count().channel(chans).channel_timetokens([time, time]).sync()

    assert(isinstance(envelope, Envelope))
    assert not envelope.status.is_error()
    assert envelope.result.channels[chan_1] == 1
    assert envelope.result.channels[chan_2] == 0
    assert isinstance(envelope.result, PNMessageCountResult)
    assert isinstance(envelope.status, PNStatus)
