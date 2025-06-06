import unittest

from pubnub.endpoints.channel_groups.list_channels_in_channel_group import ListChannelsInChannelGroup

try:
    from mock import MagicMock
except ImportError:
    from unittest.mock import MagicMock

from pubnub.pubnub import PubNub
from tests.helper import pnconf, sdk_name


class TestListChannelsInChannelGroup(unittest.TestCase):
    def setUp(self):
        self.pubnub = MagicMock(
            spec=PubNub,
            config=pnconf,
            sdk_name=sdk_name,
            uuid=None,
            _get_token=lambda: None
        )
        self.pubnub.uuid = "UUID_ListChannelsInCGTest"
        self.list = ListChannelsInChannelGroup(self.pubnub)

    def test_list_channel_group(self):
        self.list.channel_group('gr')

        self.assertEqual(self.list.build_path(),
                         ListChannelsInChannelGroup.LIST_PATH % (
                             pnconf.subscribe_key, "gr"))

        self.assertEqual(self.list.build_params_callback()({}), {
            'pnsdk': sdk_name,
            'uuid': self.pubnub.uuid,
        })
