import unittest

from pubnub import utils
from pubnub.endpoints.access.revoke import Revoke
from pubnub.enums import HttpMethod

try:
    from mock import MagicMock
except ImportError:
    from unittest.mock import MagicMock

from pubnub.pubnub import PubNub
from tests.helper import pnconf_pam_copy, sdk_name
from pubnub.managers import TelemetryManager

pnconf = pnconf_pam_copy()
# pnconf.secret_key = None


class TestRevoke(unittest.TestCase):
    def setUp(self):

        self.pubnub = MagicMock(
            spec=PubNub,
            config=pnconf,
            sdk_name=sdk_name,
            timestamp=MagicMock(return_value=123),
            uuid=None
        )
        self.pubnub.uuid = "UUID_RevokeUnitTest"
        self.pubnub._telemetry_manager = TelemetryManager()
        self.revoke = Revoke(self.pubnub)

    def test_revoke_to_channel(self):
        self.revoke.channels('ch')

        self.assertEqual(self.revoke.build_path(), Revoke.GRANT_PATH % pnconf.subscribe_key)

        pam_args = utils.prepare_pam_arguments({
            'timestamp': 123,
            'channel': 'ch',
            'r': '0',
            'w': '0',
            'm': '0',
            'pnsdk': sdk_name,
            'uuid': self.pubnub.uuid
        })
        sign_input = HttpMethod.string(self.revoke.http_method()).upper() + "\n" + \
            pnconf.publish_key + "\n" + \
            self.revoke.build_path() + "\n" + \
            pam_args + "\n"
        self.assertEqual(self.revoke.build_params_callback()({}), {
            'pnsdk': sdk_name,
            'uuid': self.pubnub.uuid,
            'timestamp': '123',
            'channel': 'ch',
            'r': '0',
            'w': '0',
            'm': '0',
            'signature': "v2." + utils.sign_sha256(pnconf.secret_key, sign_input).rstrip("=")
        })

    def test_revoke_read_to_channel(self):
        def revoke():
            self.revoke.channels('ch').read(True).write(True)

        self.assertRaises(NotImplementedError, revoke)

    def test_grant_read_and_write_to_channel_group(self):
        self.revoke.channel_groups(['gr1', 'gr2'])

        self.assertEqual(self.revoke.build_path(), Revoke.GRANT_PATH % pnconf.subscribe_key)

        pam_args = utils.prepare_pam_arguments({
            'r': '0',
            'w': '0',
            'm': '0',
            'timestamp': 123,
            'channel-group': 'gr1,gr2',
            'pnsdk': sdk_name,
            'uuid': self.pubnub.uuid
        })
        sign_input = HttpMethod.string(self.revoke.http_method()).upper() + "\n" + \
            pnconf.publish_key + "\n" + \
            self.revoke.build_path() + "\n" + \
            pam_args + "\n"
        self.assertEqual(self.revoke.build_params_callback()({}), {
            'pnsdk': sdk_name,
            'uuid': self.pubnub.uuid,
            'r': '0',
            'w': '0',
            'm': '0',
            'timestamp': '123',
            'channel-group': 'gr1,gr2',
            'signature': "v2." + utils.sign_sha256(pnconf.secret_key, sign_input).rstrip("=")
        })
