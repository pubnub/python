import unittest

from pubnub.endpoints.presence.leave import Leave
from pubnub.managers import TelemetryManager

try:
    from mock import MagicMock
except ImportError:
    from unittest.mock import MagicMock

from pubnub.pubnub import PubNub
from tests.helper import pnconf, sdk_name


class TestLeave(unittest.TestCase):
    def setUp(self):
        self.pubnub = MagicMock(
            spec=PubNub,
            config=pnconf,
            sdk_name=sdk_name,
            uuid=None
        )
        self.pubnub.uuid = "UUID_SubscribeUnitTest"
        self.pubnub._telemetry_manager = TelemetryManager()
        self.leave = Leave(self.pubnub)

    def test_leave_single_channel(self):
        self.leave.channels('ch')

        self.assertEqual(self.leave.build_path(), Leave.LEAVE_PATH % (pnconf.subscribe_key, "ch"))

        self.assertEqual(self.leave.build_params_callback()({}), {
            'pnsdk': sdk_name,
            'uuid': self.pubnub.uuid
        })

        self.assertEqual(self.leave._channels, ['ch'])

    def test_leave_multiple_channels(self):
        self.leave.channels("ch1,ch2,ch3")

        self.assertEqual(self.leave.build_path(), Leave.LEAVE_PATH % (pnconf.subscribe_key, "ch1,ch2,ch3"))

        self.assertEqual(self.leave.build_params_callback()({}), {
            'pnsdk': sdk_name,
            'uuid': self.pubnub.uuid
        })

        self.assertEqual(self.leave._channels, ['ch1', 'ch2', 'ch3'])

    def test_leave_multiple_channels_using_list(self):
        self.leave.channels(['ch1', 'ch2', 'ch3'])

        self.assertEqual(self.leave.build_path(), Leave.LEAVE_PATH % (pnconf.subscribe_key, "ch1,ch2,ch3"))

        self.assertEqual(self.leave.build_params_callback()({}), {
            'pnsdk': sdk_name,
            'uuid': self.pubnub.uuid
        })

        self.assertEqual(self.leave._channels, ['ch1', 'ch2', 'ch3'])

    def test_leave_multiple_channels_using_tuple(self):
        self.leave.channels(('ch1', 'ch2', 'ch3'))

        self.assertEqual(self.leave.build_path(), Leave.LEAVE_PATH % (pnconf.subscribe_key, "ch1,ch2,ch3"))

        self.assertEqual(self.leave.build_params_callback()({}), {
            'pnsdk': sdk_name,
            'uuid': self.pubnub.uuid
        })

        self.assertEqual(self.leave._channels, ['ch1', 'ch2', 'ch3'])

    def test_leave_single_group(self):
        self.leave.channel_groups("gr")

        self.assertEqual(self.leave.build_path(), Leave.LEAVE_PATH
                         % (pnconf.subscribe_key, ","))

        self.assertEqual(self.leave.build_params_callback()({}), {
            'channel-group': 'gr',
            'pnsdk': sdk_name,
            'uuid': self.pubnub.uuid
        })

        self.assertEqual(self.leave._groups, ['gr'])

    def test_leave_multiple_groups_using_string(self):
        self.leave.channel_groups("gr1,gr2,gr3")

        self.assertEqual(self.leave.build_path(), Leave.LEAVE_PATH
                         % (pnconf.subscribe_key, ","))

        self.assertEqual(self.leave.build_params_callback()({}), {
            'channel-group': 'gr1,gr2,gr3',
            'pnsdk': sdk_name,
            'uuid': self.pubnub.uuid
        })

        self.assertEqual(self.leave._groups, ['gr1', 'gr2', 'gr3'])

    def test_leave_multiple_groups_using_list(self):
        self.leave.channel_groups(['gr1', 'gr2', 'gr3'])

        self.assertEqual(self.leave.build_path(), Leave.LEAVE_PATH
                         % (pnconf.subscribe_key, ","))

        self.assertEqual(self.leave.build_params_callback()({}), {
            'channel-group': 'gr1,gr2,gr3',
            'pnsdk': sdk_name,
            'uuid': self.pubnub.uuid
        })

        self.assertEqual(self.leave._groups, ['gr1', 'gr2', 'gr3'])

    def test_leave_channels_and_groups(self):
        self.leave.channels('ch1,ch2').channel_groups(["gr1", "gr2"])

        self.assertEqual(self.leave.build_path(), Leave.LEAVE_PATH
                         % (pnconf.subscribe_key, "ch1,ch2"))

        self.assertEqual(self.leave.build_params_callback()({}), {
            'pnsdk': sdk_name,
            'uuid': self.pubnub.uuid,
            'channel-group': 'gr1,gr2',
        })

        self.assertEqual(self.leave._groups, ['gr1', 'gr2'])
        self.assertEqual(self.leave._channels, ['ch1', 'ch2'])
