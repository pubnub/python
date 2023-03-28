import pytest
import unittest

from pubnub.pubnub import PubNub
from pubnub.exceptions import PubNubException
from pubnub.endpoints.signal import Signal
from pubnub.managers import TelemetryManager
from tests.helper import url_encode, pnconf_copy, sdk_name
from unittest.mock import MagicMock


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


class TestPublish(unittest.TestCase):
    def setUp(self):
        self.sm = MagicMock(
            get_next_sequence=MagicMock(return_value=2)
        )

        self.pubnub = MagicMock(
            spec=PubNub,
            config=pnconf,
            sdk_name=sdk_name,
            _publish_sequence_manager=self.sm,
            _get_token=lambda: None
        )

        self.pubnub.uuid = "UUID_PublishUnitTest"
        self.pubnub._telemetry_manager = TelemetryManager()
        self.signal = Signal(self.pubnub)

    def test_signal_with_space_id(self):
        message = "hi"
        space_id = "test_space"
        encoded_message = url_encode(message)

        self.signal.channel("ch1").message(message).space_id(space_id)

        self.assertEqual(self.signal.build_path(), "/signal/%s/%s/0/ch1/0/%s"
                         % (pnconf.publish_key, pnconf.subscribe_key, encoded_message))

        self.assertEqual(self.signal.build_params_callback()({}), {
            'auth': 'auth',
            'pnsdk': sdk_name,
            'space-id': space_id,
            'uuid': self.pubnub.uuid,
        })

    def test_signal_with_message_type(self):
        message = "hi"
        message_type = 'test_type'
        encoded_message = url_encode(message)

        self.signal.channel("ch1").message(message).message_type(message_type)

        self.assertEqual(self.signal.build_path(), "/signal/%s/%s/0/ch1/0/%s"
                         % (pnconf.publish_key, pnconf.subscribe_key, encoded_message))

        self.assertEqual(self.signal.build_params_callback()({}), {
            'auth': 'auth',
            'pnsdk': sdk_name,
            'type': message_type,
            'uuid': self.pubnub.uuid,
        })
