import unittest

try:
    from mock import MagicMock
except ImportError:
    from unittest.mock import MagicMock

from pubnub.pubnub import PubNub

import pubnub.enums

from pubnub.endpoints.push.remove_device import RemoveDeviceFromPush
from tests.helper import pnconf, sdk_name
from pubnub.managers import TelemetryManager


class TestRemoveDeviceFromPush(unittest.TestCase):
    def setUp(self):
        self.pubnub = MagicMock(
            spec=PubNub,
            config=pnconf,
            sdk_name=sdk_name,
            uuid=None
        )

        self.pubnub.uuid = "UUID_RemoveDeviceTest"
        self.pubnub._telemetry_manager = TelemetryManager()
        self.remove_device = RemoveDeviceFromPush(self.pubnub)

    def test_remove_push_apns(self):
        self.remove_device.push_type(pubnub.enums.PNPushType.APNS).device_id("coolDevice")

        params = (pnconf.subscribe_key, "coolDevice")
        self.assertEqual(self.remove_device.build_path(), RemoveDeviceFromPush.REMOVE_PATH % params)

        self.assertEqual(self.remove_device.build_params_callback()({}), {
            'pnsdk': sdk_name,
            'uuid': self.pubnub.uuid,
            'type': 'apns',
        })

    def test_remove_push_gcm(self):
        self.remove_device.push_type(pubnub.enums.PNPushType.GCM).device_id("coolDevice")

        params = (pnconf.subscribe_key, "coolDevice")
        self.assertEqual(self.remove_device.build_path(), RemoveDeviceFromPush.REMOVE_PATH % params)

        self.assertEqual(self.remove_device.build_params_callback()({}), {
            'pnsdk': sdk_name,
            'uuid': self.pubnub.uuid,
            'type': 'gcm',
        })

    def test_remove_push_mpns(self):
        self.remove_device.push_type(pubnub.enums.PNPushType.MPNS).device_id("coolDevice")

        params = (pnconf.subscribe_key, "coolDevice")
        self.assertEqual(self.remove_device.build_path(), RemoveDeviceFromPush.REMOVE_PATH % params)

        self.assertEqual(self.remove_device.build_params_callback()({}), {
            'pnsdk': sdk_name,
            'uuid': self.pubnub.uuid,
            'type': 'mpns',
        })

    def test_remove_push_apns2(self):
        self.remove_device.push_type(pubnub.enums.PNPushType.APNS2).device_id("coolDevice")\
            .environment(pubnub.enums.PNPushEnvironment.PRODUCTION).topic("testTopic")

        params = (pnconf.subscribe_key, "coolDevice")
        self.assertEqual(self.remove_device.build_path(), RemoveDeviceFromPush.REMOVE_PATH_APNS2 % params)

        self.assertEqual(self.remove_device.build_params_callback()({}), {
            'pnsdk': sdk_name,
            'uuid': self.pubnub.uuid,
            'environment': pubnub.enums.PNPushEnvironment.PRODUCTION,
            'topic': 'testTopic'
        })
