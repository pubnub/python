import unittest

from pubnub import utils
from pubnub.endpoints.access.revoke import Revoke

try:
    from mock import MagicMock
except ImportError:
    from unittest.mock import MagicMock

from pubnub.pubnub import PubNub
from tests.helper import pnconf_pam, sdk_name


class TestRevoke(unittest.TestCase):
    def setUp(self):
        self.pubnub = MagicMock(
            spec=PubNub,
            config=pnconf_pam,
            sdk_name=sdk_name,
            timestamp=MagicMock(return_value=123),
            uuid=None
        )
        self.pubnub.uuid = "UUID_RevokeUnitTest"
        self.revoke = Revoke(self.pubnub)

    def test_revoke_to_channel(self):
        self.revoke.channels('ch')

        self.assertEquals(self.revoke.build_path(), Revoke.GRANT_PATH % pnconf_pam.subscribe_key)

        self.assertEqual(self.revoke.build_params(), {
            'pnsdk': sdk_name,
            'uuid': self.pubnub.uuid,
            'timestamp': '123',
            'channel': 'ch',
            'r': '0',
            'w': '0',
            'm': '0',
            'signature': utils.sign_sha256(pnconf_pam.secret_key,
                                           pnconf_pam.subscribe_key + "\n" + pnconf_pam.publish_key + "\n" +
                                           "grant\n" + utils.prepare_pam_arguments({
                                               'timestamp': 123,
                                               'channel': 'ch',
                                               'r': '0',
                                               'w': '0',
                                               'm': '0',
                                               'pnsdk': sdk_name,
                                               'uuid': self.pubnub.uuid
                                           }))
        })

    def test_revoke_read_to_channel(self):
        def revoke():
            self.revoke.channels('ch').read(True).write(True)

        self.assertRaises(NotImplementedError, revoke)

    def test_grant_read_and_write_to_channel_group(self):
        self.revoke.channel_groups(['gr1', 'gr2'])

        self.assertEquals(self.revoke.build_path(), Revoke.GRANT_PATH % pnconf_pam.subscribe_key)

        self.assertEqual(self.revoke.build_params(), {
            'pnsdk': sdk_name,
            'uuid': self.pubnub.uuid,
            'r': '0',
            'w': '0',
            'm': '0',
            'timestamp': '123',
            'channel-group': 'gr1,gr2',
            'signature': utils.sign_sha256(pnconf_pam.secret_key,
                                           pnconf_pam.subscribe_key + "\n" + pnconf_pam.publish_key + "\n" +
                                           "grant\n" + utils.prepare_pam_arguments({
                                               'r': '0',
                                               'w': '0',
                                               'm': '0',
                                               'timestamp': 123,
                                               'channel-group': 'gr1,gr2',
                                               'pnsdk': sdk_name,
                                               'uuid': self.pubnub.uuid
                                           }))
        })
