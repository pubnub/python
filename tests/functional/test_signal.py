import pytest

from pubnub.pubnub import PubNub
from pubnub.pnconfiguration import PNConfiguration
from pubnub.exceptions import PubNubException
from pubnub.endpoints.signal import Signal
from tests.helper import url_encode


SUB_KEY = 'sub'
PUB_KEY = 'pub'
CHAN = 'chan'
MSG = 'x'
MSG_ENCODED = url_encode(MSG)
AUTH = 'auth'


def test_signal():
    config = PNConfiguration()
    config.subscribe_key = SUB_KEY
    config.publish_key = PUB_KEY
    config.auth_key = AUTH
    signal = PubNub(config).signal()

    with pytest.raises(PubNubException):
        signal.validate_params()
    signal.message(MSG)
    with pytest.raises(PubNubException):
        signal.validate_params()
    signal.channel(CHAN)
    assert signal.build_path() == Signal.SIGNAL_PATH % (PUB_KEY, SUB_KEY, CHAN, MSG_ENCODED)
    assert 'auth' in signal.build_params_callback()({})
    assert AUTH == signal.build_params_callback()({})['auth']
