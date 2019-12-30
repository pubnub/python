import unittest

from pubnub.endpoints.channel_groups.remove_channel_from_channel_group import RemoveChannelFromChannelGroup

try:
    from mock import MagicMock
except ImportError:
    from unittest.mock import MagicMock

from pubnub.pubnub import PubNub
from tests.helper import pnconf, sdk_name
from pubnub.managers import TelemetryManager


class TestRemoveChannelToChannelGroup(unittest.TestCase):
    def setUp(self):
        self.pubnub = MagicMock(
            spec=PubNub,
            config=pnconf,
            sdk_name=sdk_name,
            uuid=None
        )
        self.pubnub.uuid = "UUID_RemoveChannelToCGTest"
        self.pubnub._telemetry_manager = TelemetryManager()
        self.remove = RemoveChannelFromChannelGroup(self.pubnub)

    def test_remove_single_channel(self):
        self.remove.channels('ch').channel_group('gr')

        self.assertEqual(self.remove.build_path(),
                         RemoveChannelFromChannelGroup.REMOVE_PATH % (
                             pnconf.subscribe_key, "gr"))

        self.assertEqual(self.remove.build_params_callback()({}), {
            'pnsdk': sdk_name,
            'uuid': self.pubnub.uuid,
            'remove': "ch"
        })

        self.assertEqual(self.remove._channels, ['ch'])

    def test_remove_multiple_channels(self):
        self.remove.channels(['ch1', 'ch2']).channel_group('gr')

        self.assertEqual(self.remove.build_path(),
                         RemoveChannelFromChannelGroup.REMOVE_PATH % (
                             pnconf.subscribe_key, "gr"))

        self.assertEqual(self.remove.build_params_callback()({}), {
            'pnsdk': sdk_name,
            'uuid': self.pubnub.uuid,
            'remove': "ch1,ch2"
        })

        self.assertEqual(self.remove._channels, ['ch1', 'ch2'])
