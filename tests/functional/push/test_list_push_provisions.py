import unittest
import pytest

from pubnub.endpoints.push.list_push_provisions import ListPushProvisions
from pubnub.enums import PNPushType
from pubnub.exceptions import PubNubException

try:
    from mock import MagicMock
except ImportError:
    from unittest.mock import MagicMock

from pubnub.pubnub import PubNub

import pubnub.enums

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

        self.assertEqual(self.list_push.build_path(),
                         ListPushProvisions.LIST_PATH % (
                             pnconf.subscribe_key, "coolDevice"))

        self.assertEqual(self.list_push.build_params_callback()({}), {
            'pnsdk': sdk_name,
            'uuid': self.pubnub.uuid,
            'type': 'apns'
        })

    def test_list_channel_group_gcm(self):
        self.list_push.push_type(PNPushType.GCM).device_id('coolDevice')

        self.assertEqual(self.list_push.build_path(),
                         ListPushProvisions.LIST_PATH % (
                             pnconf.subscribe_key, "coolDevice"))

        self.assertEqual(self.list_push.build_params_callback()({}), {
            'pnsdk': sdk_name,
            'uuid': self.pubnub.uuid,
            'type': 'gcm'
        })

    def test_list_channel_group_mpns(self):
        self.list_push.push_type(PNPushType.MPNS).device_id('coolDevice')

        self.assertEqual(self.list_push.build_path(),
                         ListPushProvisions.LIST_PATH % (
                             pnconf.subscribe_key, "coolDevice"))

        self.assertEqual(self.list_push.build_params_callback()({}), {
            'pnsdk': sdk_name,
            'uuid': self.pubnub.uuid,
            'type': 'mpns'
        })

    def test_list_channel_group_apns2(self):
        self.list_push.push_type(PNPushType.APNS2).device_id('coolDevice')\
            .environment(pubnub.enums.PNPushEnvironment.PRODUCTION).topic("testTopic")

        self.assertEqual(self.list_push.build_path(),
                         ListPushProvisions.LIST_PATH_APNS2 % (
                             pnconf.subscribe_key, "coolDevice"))

        self.assertEqual(self.list_push.build_params_callback()({}), {
            'pnsdk': sdk_name,
            'uuid': self.pubnub.uuid,
            'environment': pubnub.enums.PNPushEnvironment.PRODUCTION,
            'topic': 'testTopic'
        })

    def test_apns2_no_topic(self):
        push = self.list_push.push_type(PNPushType.APNS2).device_id('coolDevice')

        with pytest.raises(PubNubException):
            push.validate_params()

    def test_apns2_default_environment(self):
        self.list_push.push_type(PNPushType.APNS2).device_id('coolDevice').topic("testTopic")

        self.assertEqual(self.list_push.build_path(),
                         ListPushProvisions.LIST_PATH_APNS2 % (
                             pnconf.subscribe_key, "coolDevice"))

        self.assertEqual(self.list_push.build_params_callback()({}), {
            'pnsdk': sdk_name,
            'uuid': self.pubnub.uuid,
            'environment': pubnub.enums.PNPushEnvironment.DEVELOPMENT,
            'topic': 'testTopic'
        })
