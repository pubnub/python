import json
import unittest

from pubnub.endpoints.presence.set_state import SetState

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
        self.set_state = SetState(self.pubnub)
        self.state = {'name': 'Alex', "count": 5}

    def test_set_state_single_channel(self):
        self.set_state.channels('ch').state(self.state)

        self.assertEquals(self.set_state.build_path(), SetState.SET_STATE_PATH % (pnconf.subscribe_key,
                                                                                  "ch",
                                                                                  self.pubnub.uuid))

        self.assertEqual(self.set_state.build_params(), {
            'pnsdk': sdk_name,
            'uuid': self.pubnub.uuid,
            'state': '%7B%22count%22%3A%205%2C%20%22name%22%3A%20%22Alex%22%7D'
        })

        self.assertEqual(self.set_state._channels, ['ch'])

    def test_set_state_single_group(self):
        self.set_state.channel_groups('gr').state(self.state)

        self.assertEquals(self.set_state.build_path(), SetState.SET_STATE_PATH % (pnconf.subscribe_key,
                                                                                  ",",
                                                                                  self.pubnub.uuid))

        self.assertEqual(self.set_state.build_params(), {
            'pnsdk': sdk_name,
            'uuid': self.pubnub.uuid,
            'state': '%7B%22count%22%3A%205%2C%20%22name%22%3A%20%22Alex%22%7D',
            'channel-group': 'gr'
        })

        assert len(self.set_state._channels) == 0
        self.assertEqual(self.set_state._groups, ['gr'])
