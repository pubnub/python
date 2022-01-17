import pytest

from pubnub.pubnub import PubNub
from pubnub.exceptions import PubNubException
from pubnub.endpoints.signal import Signal
from tests.helper import url_encode, pnconf_copy

pnconf = pnconf_copy()
SUB_KEY = pnconf.subscribe_key
PUB_KEY = pnconf.publish_key
CHAN = 'chan'
MSG = 'x'
MSG_ENCODED = url_encode(MSG)
AUTH = 'auth'
UUID = 'uuid'


def test_signal():
    pnconf.auth_key = AUTH
    signal = PubNub(pnconf).signal()

    with pytest.raises(PubNubException):
        signal.validate_params()
    signal.message(MSG)
    with pytest.raises(PubNubException):
        signal.validate_params()
    signal.channel(CHAN)
    assert signal.build_path() == Signal.SIGNAL_PATH % (PUB_KEY, SUB_KEY, CHAN, MSG_ENCODED)
    assert 'auth' in signal.build_params_callback()({})
    assert AUTH == signal.build_params_callback()({})['auth']
