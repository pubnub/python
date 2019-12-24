import unittest

from pubnub.endpoints.presence.get_state import GetState

try:
    from mock import MagicMock
except ImportError:
    from unittest.mock import MagicMock

from pubnub.pubnub import PubNub
from tests.helper import pnconf, sdk_name
from pubnub.managers import TelemetryManager


class TestGetState(unittest.TestCase):
    def setUp(self):
        self.pubnub = MagicMock(
            spec=PubNub,
            config=pnconf,
            sdk_name=sdk_name,
            uuid=None
        )
        self.pubnub.uuid = "UUID_GetStateTest"
        self.pubnub._telemetry_manager = TelemetryManager()
        self.get_state = GetState(self.pubnub)

    def test_get_state_single_channel(self):
        self.get_state.channels('ch')

        self.assertEqual(self.get_state.build_path(), GetState.GET_STATE_PATH % (pnconf.subscribe_key,
                                                                                 "ch",
                                                                                 self.pubnub.uuid))

        self.assertEqual(self.get_state.build_params_callback()({}), {
            'pnsdk': sdk_name,
            'uuid': self.pubnub.uuid,
        })

        self.assertEqual(self.get_state._channels, ['ch'])

    def test_get_state_single_group(self):
        self.get_state.channel_groups('gr')

        self.assertEqual(self.get_state.build_path(), GetState.GET_STATE_PATH % (pnconf.subscribe_key,
                                                                                 ",",
                                                                                 self.pubnub.uuid))

        self.assertEqual(self.get_state.build_params_callback()({}), {
            'pnsdk': sdk_name,
            'uuid': self.pubnub.uuid,
            'channel-group': 'gr'
        })

        assert len(self.get_state._channels) == 0
        self.assertEqual(self.get_state._groups, ['gr'])
