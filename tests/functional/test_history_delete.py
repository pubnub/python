import unittest

try:
    from mock import MagicMock
except ImportError:
    from unittest.mock import MagicMock

from pubnub.endpoints.history_delete import HistoryDelete
from pubnub.pubnub import PubNub
from tests.helper import pnconf_pam_copy, sdk_name

pnconf = pnconf_pam_copy()
pnconf.secret_key = None


class TestHistoryDelete(unittest.TestCase):
    def setUp(self):
        self.pubnub = MagicMock(
            spec=PubNub,
            config=pnconf,
            sdk_name=sdk_name,
            timestamp=MagicMock(return_value=""),
            uuid=None
        )
        self.pubnub.uuid = "UUID_UnitTest"
        self.history_delete = HistoryDelete(self.pubnub)

    def test_history_delete_basic(self):
        self.history_delete.channel('ch')

        self.assertEquals(self.history_delete.build_path(), HistoryDelete.HISTORY_DELETE_PATH % (pnconf.subscribe_key, 'ch'))

        self.assertEqual(self.history_delete.build_params_callback()({}), {
            'pnsdk': sdk_name,
            'uuid': self.pubnub.uuid,
        })

    def test_history_delete_full(self):
        self.history_delete.channel('ch').start(100000).end(200000)

        self.assertEquals(self.history_delete.build_path(), HistoryDelete.HISTORY_DELETE_PATH % (pnconf.subscribe_key, 'ch'))

        self.assertEqual(self.history_delete.build_params_callback()({}), {
            'pnsdk': sdk_name,
            'uuid': self.pubnub.uuid,
            'start': '100000',
            'end': '200000',
        })