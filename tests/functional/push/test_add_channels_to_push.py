import unittest

try:
    from mock import MagicMock
except ImportError:
    from unittest.mock import MagicMock

from pubnub.pubnub import PubNub

import pubnub.enums

from pubnub.endpoints.push.add_channels_to_push import AddChannelsToPush
from tests.helper import pnconf, sdk_name
from pubnub.managers import TelemetryManager


class TestAddChannelsFromPush(unittest.TestCase):
    def setUp(self):
        self.pubnub = MagicMock(
            spec=PubNub,
            config=pnconf,
            sdk_name=sdk_name,
            uuid=None
        )

        self.pubnub.uuid = "UUID_AddChannelsTest"
        self.pubnub._telemetry_manager = TelemetryManager()
        self.add_channels = AddChannelsToPush(self.pubnub)

    def test_push_add_single_channel(self):
        self.add_channels.channels(['ch']).push_type(pubnub.enums.PNPushType.APNS).device_id("coolDevice")

        params = (pnconf.subscribe_key, "coolDevice")
        self.assertEqual(self.add_channels.build_path(), AddChannelsToPush.ADD_PATH % params)

        self.assertEqual(self.add_channels.build_params_callback()({}), {
            'pnsdk': sdk_name,
            'uuid': self.pubnub.uuid,
            'type': 'apns',
            'add': 'ch'
        })

        self.assertEqual(self.add_channels._channels, ['ch'])

    def test_push_add_multiple_channels(self):
        self.add_channels.channels(['ch1', 'ch2']).push_type(pubnub.enums.PNPushType.MPNS).device_id("coolDevice")

        params = (pnconf.subscribe_key, "coolDevice")
        self.assertEqual(self.add_channels.build_path(), AddChannelsToPush.ADD_PATH % params)

        self.assertEqual(self.add_channels.build_params_callback()({}), {
            'pnsdk': sdk_name,
            'uuid': self.pubnub.uuid,
            'type': 'mpns',
            'add': 'ch1,ch2'
        })

        self.assertEqual(self.add_channels._channels, ['ch1', 'ch2'])

    def test_push_add_google(self):
        self.add_channels.channels(['ch1', 'ch2', 'ch3']).push_type(pubnub.enums.PNPushType.GCM).device_id("coolDevice")

        params = (pnconf.subscribe_key, "coolDevice")
        self.assertEqual(self.add_channels.build_path(), AddChannelsToPush.ADD_PATH % params)

        self.assertEqual(self.add_channels.build_params_callback()({}), {
            'pnsdk': sdk_name,
            'uuid': self.pubnub.uuid,
            'type': 'gcm',
            'add': 'ch1,ch2,ch3'
        })

        self.assertEqual(self.add_channels._channels, ['ch1', 'ch2', 'ch3'])

    def test_push_add_single_channel_apns2(self):
        self.add_channels.channels(['ch']).push_type(pubnub.enums.PNPushType.APNS2).device_id("coolDevice")\
            .environment(pubnub.enums.PNPushEnvironment.PRODUCTION).topic("testTopic")

        params = (pnconf.subscribe_key, "coolDevice")
        self.assertEqual(self.add_channels.build_path(), AddChannelsToPush.ADD_PATH_APNS2 % params)

        self.assertEqual(self.add_channels.build_params_callback()({}), {
            'pnsdk': sdk_name,
            'uuid': self.pubnub.uuid,
            'add': 'ch',
            'environment': pubnub.enums.PNPushEnvironment.PRODUCTION,
            'topic': 'testTopic'
        })

        self.assertEqual(self.add_channels._channels, ['ch'])
