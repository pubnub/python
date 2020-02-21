import unittest

try:
    from mock import MagicMock
except ImportError:
    from unittest.mock import MagicMock

from pubnub.pubnub import PubNub

import pubnub.enums

from pubnub.endpoints.push.remove_channels_from_push import RemoveChannelsFromPush
from tests.helper import pnconf, sdk_name
from pubnub.managers import TelemetryManager


class TestRemoveChannelsFromPush(unittest.TestCase):
    def setUp(self):
        self.pubnub = MagicMock(
            spec=PubNub,
            config=pnconf,
            sdk_name=sdk_name,
            uuid=None
        )

        self.pubnub.uuid = "UUID_RemoveChannelsTest"
        self.pubnub._telemetry_manager = TelemetryManager()
        self.remove_channels = RemoveChannelsFromPush(self.pubnub)

    def test_push_remove_single_channel(self):
        self.remove_channels.channels(['ch']).push_type(pubnub.enums.PNPushType.APNS).device_id("coolDevice")

        params = (pnconf.subscribe_key, "coolDevice")
        self.assertEqual(self.remove_channels.build_path(), RemoveChannelsFromPush.REMOVE_PATH % params)

        self.assertEqual(self.remove_channels.build_params_callback()({}), {
            'pnsdk': sdk_name,
            'uuid': self.pubnub.uuid,
            'type': 'apns',
            'remove': 'ch'
        })

        self.assertEqual(self.remove_channels._channels, ['ch'])

    def test_push_remove_multiple_channels(self):
        self.remove_channels.channels(['ch1', 'ch2']).push_type(pubnub.enums.PNPushType.MPNS).device_id("coolDevice")

        params = (pnconf.subscribe_key, "coolDevice")
        self.assertEqual(self.remove_channels.build_path(), RemoveChannelsFromPush.REMOVE_PATH % params)

        self.assertEqual(self.remove_channels.build_params_callback()({}), {
            'pnsdk': sdk_name,
            'uuid': self.pubnub.uuid,
            'type': 'mpns',
            'remove': 'ch1,ch2'
        })

        self.assertEqual(self.remove_channels._channels, ['ch1', 'ch2'])

    def test_push_remove_google(self):
        self.remove_channels.channels(['ch1', 'ch2', 'ch3']).push_type(pubnub.enums.PNPushType.GCM)\
            .device_id("coolDevice")

        params = (pnconf.subscribe_key, "coolDevice")
        self.assertEqual(self.remove_channels.build_path(), RemoveChannelsFromPush.REMOVE_PATH % params)

        self.assertEqual(self.remove_channels.build_params_callback()({}), {
            'pnsdk': sdk_name,
            'uuid': self.pubnub.uuid,
            'type': 'gcm',
            'remove': 'ch1,ch2,ch3'
        })

        self.assertEqual(self.remove_channels._channels, ['ch1', 'ch2', 'ch3'])

    def test_push_remove_single_channel_apns2(self):
        self.remove_channels.channels(['ch']).push_type(pubnub.enums.PNPushType.APNS2).device_id("coolDevice")\
            .environment(pubnub.enums.PNPushEnvironment.PRODUCTION).topic("testTopic")

        params = (pnconf.subscribe_key, "coolDevice")
        self.assertEqual(self.remove_channels.build_path(), RemoveChannelsFromPush.REMOVE_PATH_APNS2 % params)

        self.assertEqual(self.remove_channels.build_params_callback()({}), {
            'pnsdk': sdk_name,
            'uuid': self.pubnub.uuid,
            'remove': 'ch',
            'environment': pubnub.enums.PNPushEnvironment.PRODUCTION,
            'topic': 'testTopic'
        })

        self.assertEqual(self.remove_channels._channels, ['ch'])
