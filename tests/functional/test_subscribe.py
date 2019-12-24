import unittest

try:
    from mock import MagicMock
except ImportError:
    from unittest.mock import MagicMock

from pubnub.endpoints.pubsub.subscribe import Subscribe
from pubnub.pubnub import PubNub
from tests.helper import pnconf, sdk_name
from pubnub.managers import TelemetryManager


class TestSubscribe(unittest.TestCase):
    def setUp(self):
        self.pubnub = MagicMock(
            spec=PubNub,
            config=pnconf,
            sdk_name=sdk_name
        )
        self.pubnub.uuid = "UUID_SubscribeUnitTest"
        self.pubnub._telemetry_manager = TelemetryManager()
        self.sub = Subscribe(self.pubnub)

    def test_pub_single_channel(self):
        self.sub.channels('ch')

        self.assertEqual(self.sub.build_path(), Subscribe.SUBSCRIBE_PATH
                         % (pnconf.subscribe_key, 'ch'))

        self.assertEqual(self.sub.build_params_callback()({}), {
            'pnsdk': sdk_name,
            'uuid': self.pubnub.uuid
        })

        self.assertEqual(self.sub._channels, ['ch'])

    def test_sub_multiple_channels_using_string(self):
        self.sub.channels("ch1,ch2,ch3")

        self.assertEqual(self.sub.build_path(), Subscribe.SUBSCRIBE_PATH
                         % (pnconf.subscribe_key, "ch1,ch2,ch3"))

        self.assertEqual(self.sub.build_params_callback()({}), {
            'pnsdk': sdk_name,
            'uuid': self.pubnub.uuid
        })

        self.assertEqual(self.sub._channels, ['ch1', 'ch2', 'ch3'])

    def test_sub_multiple_channels_using_list(self):
        self.sub.channels(['ch1', 'ch2', 'ch3'])

        self.assertEqual(self.sub.build_path(), Subscribe.SUBSCRIBE_PATH
                         % (pnconf.subscribe_key, "ch1,ch2,ch3"))

        self.assertEqual(self.sub.build_params_callback()({}), {
            'pnsdk': sdk_name,
            'uuid': self.pubnub.uuid
        })

        self.assertEqual(self.sub._channels, ['ch1', 'ch2', 'ch3'])

    def test_sub_multiple_channels_using_tuple(self):
        self.sub.channels(('ch1', 'ch2', 'ch3'))

        self.assertEqual(self.sub.build_path(), Subscribe.SUBSCRIBE_PATH
                         % (pnconf.subscribe_key, "ch1,ch2,ch3"))

        self.assertEqual(self.sub.build_params_callback()({}), {
            'pnsdk': sdk_name,
            'uuid': self.pubnub.uuid
        })

        self.assertEqual(self.sub._channels, ['ch1', 'ch2', 'ch3'])

    def test_sub_single_group(self):
        self.sub.channel_groups("gr")

        self.assertEqual(self.sub.build_path(), Subscribe.SUBSCRIBE_PATH
                         % (pnconf.subscribe_key, ","))

        self.assertEqual(self.sub.build_params_callback()({}), {
            'channel-group': 'gr',
            'pnsdk': sdk_name,
            'uuid': self.pubnub.uuid
        })

        self.assertEqual(self.sub._groups, ['gr'])

    def test_sub_multiple_groups_using_string(self):
        self.sub.channel_groups("gr1,gr2,gr3")

        self.assertEqual(self.sub.build_path(), Subscribe.SUBSCRIBE_PATH
                         % (pnconf.subscribe_key, ","))

        self.assertEqual(self.sub.build_params_callback()({}), {
            'channel-group': 'gr1,gr2,gr3',
            'pnsdk': sdk_name,
            'uuid': self.pubnub.uuid
        })

        self.assertEqual(self.sub._groups, ['gr1', 'gr2', 'gr3'])

    def test_sub_multiple_groups_using_list(self):
        self.sub.channel_groups(['gr1', 'gr2', 'gr3'])

        self.assertEqual(self.sub.build_path(), Subscribe.SUBSCRIBE_PATH
                         % (pnconf.subscribe_key, ","))

        self.assertEqual(self.sub.build_params_callback()({}), {
            'channel-group': 'gr1,gr2,gr3',
            'pnsdk': sdk_name,
            'uuid': self.pubnub.uuid
        })

        self.assertEqual(self.sub._groups, ['gr1', 'gr2', 'gr3'])

    def test_sub_multiple(self):
        self.sub.channels('ch1,ch2').filter_expression('blah').region('us-east-1').timetoken('123')

        self.assertEqual(self.sub.build_path(), Subscribe.SUBSCRIBE_PATH
                         % (pnconf.subscribe_key, "ch1,ch2"))

        self.assertEqual(self.sub.build_params_callback()({}), {
            'pnsdk': sdk_name,
            'uuid': self.pubnub.uuid,
            'filter-expr': 'blah',
            'tr': 'us-east-1',
            'tt': '123'
        })

        self.assertEqual(self.sub._groups, [])
        self.assertEqual(self.sub._channels, ['ch1', 'ch2'])
