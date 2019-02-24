import pytest

from pubnub.pubnub import PubNub
from pubnub.models.consumer.message_count import PNMessageCountResult
from pubnub.models.consumer.common import PNStatus
from tests.helper import pnconf_mc_copy


@pytest.fixture
def pn():
    config = pnconf_mc_copy()
    config.enable_subscribe = False
    return PubNub(config)


def test_single_channel(pn):
    chan = 'unique_threads'

    def callback(result, status):
        time = result.timetoken - 10
        pn.message_counts().channel(chan).channel_timetokens([time]).pn_async(check_result)

    def check_result(result, status):
        assert not status.is_error()
        assert result.channels[chan] == 1
        assert isinstance(result, PNMessageCountResult)
        assert isinstance(status, PNStatus)

    pn.publish().channel(chan).message('bla').pn_async(callback)


def test_multiple_channels(pn):
    chan_1 = 'unique_threads_1'
    chan_2 = 'unique_threads_2'
    chans = ','.join([chan_1, chan_2])

    def callback(result, status):
        time = result.timetoken - 10
        pn.message_counts().channel(chans).channel_timetokens([time, time]).pn_async(check_result)

    def check_result(result, status):
        assert not status.is_error()
        assert result.channels[chan_1] == 1
        assert result.channels[chan_2] == 0
        assert isinstance(result, PNMessageCountResult)
        assert isinstance(status, PNStatus)

    pn.publish().channel(chan_1).message('something').pn_async(callback)
