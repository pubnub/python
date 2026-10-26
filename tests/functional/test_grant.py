import unittest

from pubnub import utils
from pubnub.endpoints.access.grant import Grant
from pubnub.enums import HttpMethod
from pubnub.exceptions import PubNubException

try:
    from mock import MagicMock
except ImportError:
    from unittest.mock import MagicMock

from pubnub.pubnub import PubNub
from tests.helper import pnconf_pam, sdk_name


class TestGrant(unittest.TestCase):
    def setUp(self):
        self.pubnub = MagicMock(
            spec=PubNub,
            config=pnconf_pam,
            sdk_name=sdk_name,
            timestamp=MagicMock(return_value=123),
            uuid=None
        )
        self.pubnub.uuid = "UUID_GrantUnitTest"
        self.grant = Grant(self.pubnub)

    def test_grant_read_and_write_to_channel(self):
        self.grant.channels('ch').read(True).write(True).ttl(7)
        self.assertEqual(self.grant.build_path(), Grant.GRANT_PATH % pnconf_pam.subscribe_key)

        pam_args = utils.prepare_pam_arguments({
            'r': '1',
            'w': '1',
            'ttl': '7',
            'timestamp': 123,
            'channel': 'ch',
            'pnsdk': sdk_name,
            'uuid': self.pubnub.uuid
        })
        sign_input = HttpMethod.string(self.grant.http_method()).upper() + "\n" + \
            pnconf_pam.publish_key + "\n" + \
            self.grant.build_path() + "\n" + \
            pam_args + "\n"
        self.assertEqual(self.grant.build_params_callback()({}), {
            'pnsdk': sdk_name,
            'uuid': self.pubnub.uuid,
            'r': '1',
            'w': '1',
            'ttl': '7',
            'timestamp': '123',
            'channel': 'ch',
            'signature': "v2." + utils.sign_sha256(pnconf_pam.secret_key, sign_input).rstrip("=")
        })

    def test_grant_categories_to_auth_key(self):
        self.grant.auth_keys('my-auth-key').categories(['channels', 'uuids']).get(True).ttl(1440)

        pam_args = utils.prepare_pam_arguments({
            'g': '1',
            'auth': 'my-auth-key',
            'category': 'channels,uuids',
            'ttl': '1440',
            'timestamp': 123,
            'pnsdk': sdk_name,
            'uuid': self.pubnub.uuid,
        })
        sign_input = HttpMethod.string(self.grant.http_method()).upper() + "\n" + \
            pnconf_pam.publish_key + "\n" + \
            self.grant.build_path() + "\n" + \
            pam_args + "\n"

        self.assertEqual(self.grant.build_params_callback()({}), {
            'g': '1',
            'auth': 'my-auth-key',
            'category': 'channels,uuids',
            'ttl': '1440',
            'timestamp': '123',
            'pnsdk': sdk_name,
            'uuid': self.pubnub.uuid,
            'signature': "v2." + utils.sign_sha256(pnconf_pam.secret_key, sign_input).rstrip("=")
        })

    def test_grant_categories_accepts_string(self):
        self.grant.auth_keys('my-auth-key').categories('channels,uuids').get(True)
        self.assertEqual(self.grant.build_params_callback()({})['category'], 'channels,uuids')

    def test_grant_categories_alongside_channel(self):
        self.grant.auth_keys('my-auth-key').channels('ch1').categories(['channels']).get(True).ttl(1440)

        params = self.grant.build_params_callback()({})
        self.assertEqual(params['channel'], 'ch1')
        self.assertEqual(params['category'], 'channels')
        self.assertEqual(params['g'], '1')

    def test_grant_categories_revoke_with_get_false(self):
        self.grant.auth_keys('my-auth-key').categories(['channels']).get(False)

        params = self.grant.build_params_callback()({})
        self.assertEqual(params['g'], '0')
        self.assertEqual(params['category'], 'channels')
        self.assertNotIn('ttl', params)

    def test_grant_without_categories_omits_param(self):
        self.grant.channels('ch').read(True).write(True)
        self.assertNotIn('category', self.grant.build_params_callback()({}))

    def test_grant_read_and_write_to_channel_group(self):
        self.grant.channel_groups(['gr1', 'gr2']).read(True).write(True)

        self.assertEqual(self.grant.build_path(), Grant.GRANT_PATH % pnconf_pam.subscribe_key)

        pam_args = utils.prepare_pam_arguments({
            'r': '1',
            'w': '1',
            'timestamp': 123,
            'channel-group': 'gr1,gr2',
            'pnsdk': sdk_name,
            'uuid': self.pubnub.uuid
        })
        sign_input = HttpMethod.string(self.grant.http_method()).upper() + "\n" + \
            pnconf_pam.publish_key + "\n" + \
            self.grant.build_path() + "\n" + \
            pam_args + "\n"
        self.assertEqual(self.grant.build_params_callback()({}), {
            'pnsdk': sdk_name,
            'uuid': self.pubnub.uuid,
            'r': '1',
            'w': '1',
            'timestamp': '123',
            'channel-group': 'gr1,gr2',
            'signature': "v2." + utils.sign_sha256(pnconf_pam.secret_key, sign_input).rstrip("=")
        })


class TestGrantCategoryValidation(unittest.TestCase):
    def setUp(self):
        self.pubnub = MagicMock(spec=PubNub, config=pnconf_pam, sdk_name=sdk_name,
                                timestamp=MagicMock(return_value=123), uuid=None)
        self.pubnub.uuid = "UUID_GrantUnitTest"
        self.grant = Grant(self.pubnub)

    def test_valid_category_grant(self):
        self.grant.auth_keys('a').categories(['channels', 'uuids']).get(True).validate_params()

    def test_unknown_category_rejected(self):
        with self.assertRaises(PubNubException):
            self.grant.auth_keys('a').categories(['users']).get(True).validate_params()

    def test_category_requires_auth(self):
        with self.assertRaises(PubNubException):
            self.grant.categories(['channels']).get(True).validate_params()

    def test_category_rejects_other_permissions(self):
        with self.assertRaises(PubNubException):
            self.grant.auth_keys('a').categories(['channels']).get(True).read(True).validate_params()

    def test_category_one_minute_grant_rejected(self):
        with self.assertRaises(PubNubException):
            self.grant.auth_keys('a').categories(['channels']).get(True).ttl(1).validate_params()

    def test_category_one_minute_revoke_allowed(self):
        self.grant.auth_keys('a').categories(['channels']).get(False).ttl(1).validate_params()
