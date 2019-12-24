import unittest

try:
    from mock import MagicMock
except ImportError:
    from unittest.mock import MagicMock

from pubnub.endpoints.presence.where_now import WhereNow
from pubnub.pubnub import PubNub
from tests.helper import pnconf, sdk_name, pnconf_copy
from pubnub.managers import TelemetryManager


class TestWhereNow(unittest.TestCase):
    def setUp(self):
        self.pubnub = MagicMock(
            spec=PubNub,
            config=pnconf_copy(),
            sdk_name=sdk_name
        )
        self.pubnub.config.uuid = "UUID_WhereNowTest"
        self.pubnub._telemetry_manager = TelemetryManager()
        self.where_now = WhereNow(self.pubnub)

    def test_where_now(self):
        self.where_now.uuid("person_uuid")

        self.assertEqual(self.where_now.build_path(), WhereNow.WHERE_NOW_PATH
                         % (pnconf.subscribe_key, "person_uuid"))

        self.assertEqual(self.where_now.build_params_callback()({}), {
            'pnsdk': sdk_name,
            'uuid': self.pubnub.uuid
        })

    def test_where_now_no_uuid(self):
        self.assertEqual(self.where_now.build_path(), WhereNow.WHERE_NOW_PATH
                         % (pnconf.subscribe_key, self.pubnub.config.uuid))

        self.assertEqual(self.where_now.build_params_callback()({}), {
            'pnsdk': sdk_name,
            'uuid': self.pubnub.uuid
        })
