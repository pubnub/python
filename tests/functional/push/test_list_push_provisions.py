import unittest

from pubnub.endpoints.push.list_push_provisions import ListPushProvisions
from pubnub.enums import PNPushType

try:
    from mock import MagicMock
except ImportError:
    from unittest.mock import MagicMock

from pubnub.pubnub import PubNub
from tests.helper import pnconf, sdk_name
from pubnub.managers import TelemetryManager


class TestListPushProvisions(unittest.TestCase):
    def setUp(self):
        self.pubnub = MagicMock(
            spec=PubNub,
            config=pnconf,
            sdk_name=sdk_name,
            uuid=None
        )
        self.pubnub.uuid = "UUID_ListChannelsInCGTest"
        self.pubnub._telemetry_manager = TelemetryManager()
        self.list_push = ListPushProvisions(self.pubnub)

    def test_list_channel_group_apns(self):
        self.list_push.push_type(PNPushType.APNS).device_id('coolDevice')

        self.assertEquals(self.list_push.build_path(),
                          ListPushProvisions.LIST_PATH % (
                              pnconf.subscribe_key, "coolDevice"))

        self.assertEqual(self.list_push.build_params_callback()({}), {
            'pnsdk': sdk_name,
            'uuid': self.pubnub.uuid,
            'type': 'apns'
        })

    def test_list_channel_group_gcm(self):
        self.list_push.push_type(PNPushType.GCM).device_id('coolDevice')

        self.assertEquals(self.list_push.build_path(),
                          ListPushProvisions.LIST_PATH % (
                              pnconf.subscribe_key, "coolDevice"))

        self.assertEqual(self.list_push.build_params_callback()({}), {
            'pnsdk': sdk_name,
            'uuid': self.pubnub.uuid,
            'type': 'gcm'
        })

    def test_list_channel_group_mpns(self):
        self.list_push.push_type(PNPushType.MPNS).device_id('coolDevice')

        self.assertEquals(self.list_push.build_path(),
                          ListPushProvisions.LIST_PATH % (
                              pnconf.subscribe_key, "coolDevice"))

        self.assertEqual(self.list_push.build_params_callback()({}), {
            'pnsdk': sdk_name,
            'uuid': self.pubnub.uuid,
            'type': 'mpns'
        })
