import json
import unittest
import urllib
from unittest.mock import MagicMock

from pubnub.endpoints.presence.heartbeat import Heartbeat
from pubnub.managers import TelemetryManager
from pubnub.pubnub import PubNub
from tests.helper import pnconf, sdk_name, pnconf_copy


class TestHeartbeat(unittest.TestCase):
    def setUp(self):
        self.pubnub = MagicMock(
            spec=PubNub,
            config=pnconf_copy(),
            sdk_name=sdk_name,
            _get_token=lambda: None
        )
        self.pubnub.uuid = "UUID_HeartbeatUnitTest"
        self.hb = Heartbeat(self.pubnub)
        self.pubnub._telemetry_manager = TelemetryManager()
        self.pubnub.config.set_presence_timeout(20)

    def test_sub_single_channel(self):
        self.hb.channels('ch')

        self.assertEqual(self.hb.build_path(), Heartbeat.HEARTBEAT_PATH
                         % (pnconf.subscribe_key, 'ch'))

        self.assertEqual(self.hb.build_params_callback()({}), {
            'pnsdk': sdk_name,
            'uuid': self.pubnub.uuid,
            'heartbeat': '20'
        })

        self.assertEqual(self.hb._channels, ['ch'])

    def test_hb_multiple_channels_using_list(self):
        self.hb.channels(['ch1', 'ch2', 'ch3'])

        self.assertEqual(self.hb.build_path(), Heartbeat.HEARTBEAT_PATH
                         % (pnconf.subscribe_key, "ch1,ch2,ch3"))

        self.assertEqual(self.hb.build_params_callback()({}), {
            'pnsdk': sdk_name,
            'uuid': self.pubnub.uuid,
            'heartbeat': '20'
        })

        self.assertEqual(self.hb._channels, ['ch1', 'ch2', 'ch3'])

    def test_hb_single_group(self):
        self.hb.channel_groups("gr")

        self.assertEqual(self.hb.build_path(), Heartbeat.HEARTBEAT_PATH
                         % (pnconf.subscribe_key, ","))

        self.assertEqual(self.hb.build_params_callback()({}), {
            'channel-group': 'gr',
            'pnsdk': sdk_name,
            'uuid': self.pubnub.uuid,
            'heartbeat': '20'
        })

        self.assertEqual(self.hb._groups, ['gr'])

    def test_hb_multiple_groups_using_list(self):
        self.hb.channel_groups(['gr1', 'gr2', 'gr3'])

        self.assertEqual(self.hb.build_path(), Heartbeat.HEARTBEAT_PATH
                         % (pnconf.subscribe_key, ","))

        self.assertEqual(self.hb.build_params_callback()({}), {
            'channel-group': 'gr1,gr2,gr3',
            'pnsdk': sdk_name,
            'uuid': self.pubnub.uuid,
            'heartbeat': '20'
        })

        self.assertEqual(self.hb._groups, ['gr1', 'gr2', 'gr3'])

    def test_hb_with_state(self):
        state = {"name": "Alex", "count": 7}
        self.hb.channels('ch1,ch2').state(state)

        self.assertEqual(self.hb.build_path(), Heartbeat.HEARTBEAT_PATH
                         % (pnconf.subscribe_key, "ch1,ch2"))

        params = self.hb.build_params_callback()({})
        params['state'] = json.loads(urllib.parse.unquote(params['state']))

        self.assertEqual(params, {
            'pnsdk': sdk_name,
            'uuid': self.pubnub.uuid,
            'heartbeat': '20',
            'state': state
        })

        self.assertEqual(self.hb._groups, [])
        self.assertEqual(self.hb._channels, ['ch1', 'ch2'])
