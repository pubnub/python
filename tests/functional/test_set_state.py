import json
import unittest

from pubnub.endpoints.presence.set_state import SetState
from tests import helper
from pubnub.managers import TelemetryManager

try:
    from mock import MagicMock
except ImportError:
    from unittest.mock import MagicMock

from pubnub.pubnub import PubNub
from tests.helper import pnconf, sdk_name


class TestSetState(unittest.TestCase):
    def setUp(self):
        self.pubnub = MagicMock(
            spec=PubNub,
            config=pnconf,
            sdk_name=sdk_name,
            uuid=None
        )
        self.pubnub.uuid = "UUID_SetStateTest"
        self.pubnub._telemetry_manager = TelemetryManager()
        self.set_state = SetState(self.pubnub)
        self.state = {'name': 'Alex', "count": 5}

    def test_set_state_single_channel(self):
        self.set_state.channels('ch').state(self.state)

        self.assertEqual(self.set_state.build_path(), SetState.SET_STATE_PATH % (pnconf.subscribe_key,
                                                                                 "ch",
                                                                                 self.pubnub.uuid))

        params = self.set_state.build_params_callback()({})
        self.assertEqual(params['pnsdk'], sdk_name)
        self.assertEqual(params['uuid'], self.pubnub.uuid)
        self.assertEqual(json.loads(helper.url_decode(params['state'])),
                         json.loads(helper.url_decode('%7B%22count%22%3A%205%2C%20%22name%22%3A%20%22Alex%22%7D')))

        self.assertEqual(self.set_state._channels, ['ch'])

    def test_set_state_single_group(self):
        self.set_state.channel_groups('gr').state(self.state)

        self.assertEqual(self.set_state.build_path(), SetState.SET_STATE_PATH % (pnconf.subscribe_key,
                                                                                 ",",
                                                                                 self.pubnub.uuid))

        params = self.set_state.build_params_callback()({})
        self.assertEqual(params['pnsdk'], sdk_name)
        self.assertEqual(params['uuid'], self.pubnub.uuid)
        self.assertEqual(params['channel-group'], 'gr')
        self.assertEqual(json.loads(helper.url_decode(params['state'])),
                         json.loads(helper.url_decode('%7B%22count%22%3A%205%2C%20%22name%22%3A%20%22Alex%22%7D')))

        assert len(self.set_state._channels) == 0
        self.assertEqual(self.set_state._groups, ['gr'])
