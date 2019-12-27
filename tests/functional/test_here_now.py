import unittest

from pubnub.endpoints.presence.here_now import HereNow
from pubnub.managers import TelemetryManager

try:
    from mock import MagicMock
except ImportError:
    from unittest.mock import MagicMock

from pubnub.pubnub import PubNub
from tests.helper import pnconf, sdk_name


class TestHereNow(unittest.TestCase):
    def setUp(self):
        self.pubnub = MagicMock(
            spec=PubNub,
            config=pnconf,
            sdk_name=sdk_name
        )
        self.pubnub.uuid = "UUID_HereNowTest"
        self.pubnub._telemetry_manager = TelemetryManager()
        self.here_now = HereNow(self.pubnub)

    def test_here_now(self):
        self.here_now.channels("ch1")

        self.assertEqual(self.here_now.build_path(), HereNow.HERE_NOW_PATH
                         % (pnconf.subscribe_key, "ch1"))

        self.assertEqual(self.here_now.build_params_callback()({}), {
            'pnsdk': sdk_name,
            'uuid': self.pubnub.uuid
        })

    def test_here_now_groups(self):
        self.here_now.channel_groups("gr1")

        self.assertEqual(self.here_now.build_path(), HereNow.HERE_NOW_PATH
                         % (pnconf.subscribe_key, ","))

        self.assertEqual(self.here_now.build_params_callback()({}), {
            'channel-group': 'gr1',
            'pnsdk': sdk_name,
            'uuid': self.pubnub.uuid
        })

    def test_here_now_with_options(self):
        self.here_now.channels(["ch1"]).channel_groups("gr1").include_state(True).include_uuids(False)

        self.assertEqual(self.here_now.build_path(), HereNow.HERE_NOW_PATH
                         % (pnconf.subscribe_key, "ch1"))

        self.assertEqual(self.here_now.build_params_callback()({}), {
            'channel-group': 'gr1',
            'state': '1',
            'disable_uuids': '1',
            'pnsdk': sdk_name,
            'uuid': self.pubnub.uuid
        })
