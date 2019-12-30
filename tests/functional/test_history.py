import unittest

try:
    from mock import MagicMock
except ImportError:
    from unittest.mock import MagicMock

from pubnub.endpoints.history import History
from pubnub.pubnub import PubNub
from tests.helper import pnconf_pam_copy, sdk_name
from pubnub.managers import TelemetryManager

pnconf = pnconf_pam_copy()
pnconf.secret_key = None


class TestHistory(unittest.TestCase):
    def setUp(self):
        self.pubnub = MagicMock(
            spec=PubNub,
            config=pnconf,
            sdk_name=sdk_name,
            timestamp=MagicMock(return_value=123),
            uuid=None
        )
        self.pubnub.uuid = "UUID_UnitTest"
        self.pubnub._telemetry_manager = TelemetryManager()
        self.history = History(self.pubnub)

    def test_history_basic(self):
        self.history.channel('ch')

        self.assertEqual(self.history.build_path(), History.HISTORY_PATH % (pnconf.subscribe_key, 'ch'))

        self.assertEqual(self.history.build_params_callback()({}), {
            'pnsdk': sdk_name,
            'uuid': self.pubnub.uuid,
            'count': '100'
        })

    def test_history_full(self):
        self.history.channel('ch').start(100000).end(200000).reverse(False).count(3).include_timetoken(True)

        self.assertEqual(self.history.build_path(), History.HISTORY_PATH % (pnconf.subscribe_key, 'ch'))

        self.assertEqual(self.history.build_params_callback()({}), {
            'pnsdk': sdk_name,
            'uuid': self.pubnub.uuid,
            'count': '3',
            'start': '100000',
            'end': '200000',
            'reverse': 'false',
            'include_token': 'true'
        })
