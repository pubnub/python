import unittest

from pubnub.endpoints.channel_groups.add_channel_to_channel_group import AddChannelToChannelGroup
from pubnub.managers import TelemetryManager

try:
    from mock import MagicMock
except ImportError:
    from unittest.mock import MagicMock

from pubnub.pubnub import PubNub
from tests.helper import pnconf, sdk_name


class TestAddChannelToChannelGroup(unittest.TestCase):
    def setUp(self):
        self.pubnub = MagicMock(
            spec=PubNub,
            config=pnconf,
            sdk_name=sdk_name,
            uuid=None
        )
        self.pubnub.uuid = "UUID_AddChannelToCGTest"
        self.pubnub._telemetry_manager = TelemetryManager()
        self.add = AddChannelToChannelGroup(self.pubnub)

    def test_add_single_channel(self):
        self.add.channels('ch').channel_group('gr')

        self.assertEqual(self.add.build_path(),
                         AddChannelToChannelGroup.ADD_PATH % (
                             pnconf.subscribe_key, "gr"))

        self.assertEqual(self.add.build_params_callback()({}), {
            'pnsdk': sdk_name,
            'uuid': self.pubnub.uuid,
            'add': "ch"
        })

        self.assertEqual(self.add._channels, ['ch'])

    def test_add_multiple_channels(self):
        self.add.channels(['ch1', 'ch2']).channel_group('gr')

        self.assertEqual(self.add.build_path(),
                         AddChannelToChannelGroup.ADD_PATH % (
                             pnconf.subscribe_key, "gr"))

        self.assertEqual(self.add.build_params_callback()({}), {
            'pnsdk': sdk_name,
            'uuid': self.pubnub.uuid,
            'add': "ch1,ch2"
        })

        self.assertEqual(self.add._channels, ['ch1', 'ch2'])
