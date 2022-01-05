import pytest

from pubnub.pubnub import PubNub
from pubnub.endpoints.message_count import MessageCount
from pubnub.exceptions import PubNubException
from tests.helper import pnconf

SUB_KEY = pnconf.subscribe_key


@pytest.fixture
def mc():
    return PubNub(pnconf).message_counts()


def test_single_channel(mc):
    mc.channel('chan')
    assert mc.build_path() == MessageCount.MESSAGE_COUNT_PATH % (SUB_KEY, 'chan')

    with pytest.raises(PubNubException):
        mc.validate_params()
    mc.channel_timetokens([11])
    mc.validate_params()

    params = mc.custom_params()
    assert 'timetoken' in params
    assert params['timetoken'] == '11'
    assert 'channelsTimetoken' not in params


def test_multi_channels(mc):
    chans = 'chan,chan_2'
    mc.channel(chans)
    assert mc.build_path() == MessageCount.MESSAGE_COUNT_PATH % (SUB_KEY, chans)

    mc.channel_timetokens([11])
    with pytest.raises(PubNubException):
        mc.validate_params()
    mc.channel_timetokens([12])
    mc.validate_params()

    params = mc.custom_params()
    assert 'channelsTimetoken' in params
    assert params['channelsTimetoken'] == '11,12'
    assert 'timetoken' not in params
