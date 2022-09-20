import logging
import unittest

import pubnub
from pubnub.models.consumer.entities.user import PNCreateUserResult, PNFetchUserResult, PNFetchUsersResult, \
    PNUpdateUserResult, PNUpsertUserResult
from pubnub.pubnub import PubNub
from pubnub.exceptions import PubNubException
from tests.helper import pnconf_pam_copy
from tests.integrational.vcr_helper import pn_vcr


pubnub.set_stream_logger('pubnub', logging.WARNING)


class TestPubNubUsers(unittest.TestCase):
    def get_config(self):
        config = pnconf_pam_copy()
        config.origin = 'test.ps.pn'
        config.subscribe_key = 'sub-c-test'
        return config

    @pn_vcr.use_cassette('tests/integrational/fixtures/native_sync/users/create_user.yaml',
                         filter_query_parameters=['uuid', 'pnsdk', 'signature', 'timestamp'])
    def test_create_user(self):
        test_user_id = 'AdaLovelace'
        pubnub = PubNub(self.get_config())

        create = pubnub.create_user(
            user_id=test_user_id,
            name='Ada Lovelace',
            email='ada.lovelace@user.id',
            user_type='programmer',
            user_status='legend',
            profile_url='https://eee.ee/eeee/e/ee.e',
            external_id='x1x2x3',
            custom={
                'dob': '12/10/1815'
            },
            sync=True
        )

        assert isinstance(create.result, PNCreateUserResult)
        assert 'custom' in create.result.data
        assert {'dob': '12/10/1815'} == create.result.data['custom']

        pubnub.remove_user(test_user_id, sync=True)

    @pn_vcr.use_cassette('tests/integrational/fixtures/native_sync/users/update_user.yaml',
                         filter_query_parameters=['uuid', 'pnsdk', 'signature', 'timestamp'])
    def test_update_user(self):
        test_user_id = 'AdaLovelace'
        pubnub = PubNub(self.get_config())
        pubnub.create_user(test_user_id, sync=True)

        update = pubnub.update_user(
            user_id=test_user_id,
            name='Ada Lovelace',
            email='ada.lovelace@user.id',
            user_type='programmer',
            user_status='legend',
            custom={
                'dob': '1815-12-10'
            },
            sync=True
        )

        assert isinstance(update.result, PNUpdateUserResult)
        assert 'custom' in update.result.data
        assert {'dob': '1815-12-10'} == update.result.data['custom']

        pubnub.remove_user(test_user_id, sync=True)

    @pn_vcr.use_cassette('tests/integrational/fixtures/native_sync/users/upsert_create_user.yaml',
                         filter_query_parameters=['uuid', 'pnsdk', 'signature', 'timestamp'])
    def test_upsert_create_user(self):
        pubnub = PubNub(self.get_config())
        test_user_id = 'CharlesBabbage'

        pubnub.remove_user(test_user_id, sync=True)

        update = pubnub.upsert_user(
            user_id=test_user_id,
            name='Charles Babbage',
            email='charlie.b@user.id',
            user_type='genius',
            user_status='legend',
            custom={
                'dob': '1791-12-26'
            },
            sync=True
        )

        assert isinstance(update.result, PNUpsertUserResult)
        assert 'custom' in update.result.data
        assert {'dob': '1791-12-26'} == update.result.data['custom']

        pubnub.remove_user(test_user_id, sync=True)

    @pn_vcr.use_cassette('tests/integrational/fixtures/native_sync/users/upsert_update_user.yaml',
                         filter_query_parameters=['uuid', 'pnsdk', 'signature', 'timestamp'])
    def test_upsert_update_user(self):
        pubnub = PubNub(self.get_config())
        test_user_id = 'CharlesBabbage'

        pubnub.create_user(test_user_id, sync=True)

        update = pubnub.upsert_user(
            user_id=test_user_id,
            name='Charles Babbage',
            email='charlie.b@user.id',
            user_type='genius',
            user_status='legend',
            custom={
                'dob': '1791-12-26'
            },
            sync=True
        )

        assert isinstance(update.result, PNUpsertUserResult)
        assert 'custom' in update.result.data
        assert {'dob': '1791-12-26'} == update.result.data['custom']

        pubnub.remove_user(test_user_id, sync=True)

    @pn_vcr.use_cassette('tests/integrational/fixtures/native_sync/users/create_user_id_collision.yaml',
                         filter_query_parameters=['uuid', 'pnsdk', 'signature', 'timestamp'])
    def test_create_user_id_collision(self):
        pubnub = PubNub(self.get_config())
        test_user_id = 'JosephMarieJacquard'

        pubnub.create_user(test_user_id, sync=True)

        with self.assertRaises(PubNubException) as context:

            pubnub.create_user(
                user_id=test_user_id,
                name='Joseph Marie Jacquard',
                email='jmjacquard@user.id',
                user_type='inventor',
                user_status='legend',
                custom={
                    'dob': '1752-07-07'
                },
                sync=True
            )

        self.assertEqual(
            '{"error":{"message":"Requested resource already exists.","source":"metadata"},"status":409}',
            context.exception._errormsg
        )
        self.assertEqual(409, context.exception._status_code)

        pubnub.remove_user(test_user_id, sync=True)

    @pn_vcr.use_cassette('tests/integrational/fixtures/native_sync/users/update_user_id_missing.yaml',
                         filter_query_parameters=['uuid', 'pnsdk', 'signature', 'timestamp'])
    def test_update_user_id_missing(self):
        pubnub = PubNub(self.get_config())
        test_user_id = 'StevenPaulJobs'

        pubnub.remove_user(test_user_id, sync=True)

        with self.assertRaises(PubNubException) as context:
            pubnub.update_user(
                user_id=test_user_id,
                name='Steven Paul Jobs',
                email='steve-j@user.id',
                user_type='entrepreneur',
                user_status='guru',
                custom={
                    'dob': '1955-02-24'
                },
                sync=True
            )

        self.assertEqual(
            '{"error":{"message":"Requested resource does not exists.","source":"metadata"},"status":404}',
            context.exception._errormsg
        )
        self.assertEqual(404, context.exception._status_code)

        pubnub.remove_user(test_user_id, sync=True)

    @pn_vcr.use_cassette('tests/integrational/fixtures/native_sync/users/fetch_user_existing.yaml',
                         filter_query_parameters=['uuid', 'pnsdk', 'signature', 'timestamp'])
    def test_fetch_user_existing(self):
        pubnub = PubNub(self.get_config())
        test_user_id = 'GraceBrewsterMurrayHopper'
        pubnub.remove_user(test_user_id, sync=True)
        pubnub.create_user(user_id=test_user_id, name='Grace Brewster Murray Hopper', email='admiral.grace@user.id',
                           user_type='debugger', user_status='legend', custom={'dob': '1906-12-09'}, sync=True)

        user = pubnub.fetch_user(test_user_id, sync=True)
        self.assertIs(type(user.result), PNFetchUserResult)
        self.assertTrue("custom" in user.result.data.keys())
        self.assertEqual({'dob': '1906-12-09'}, user.result.data["custom"])

        pubnub.remove_user(test_user_id, sync=True)

    @pn_vcr.use_cassette('tests/integrational/fixtures/native_sync/users/fetch_user_not_existing.yaml',
                         filter_query_parameters=['uuid', 'pnsdk', 'signature', 'timestamp'])
    def test_fetch_user_not_existing(self):
        pubnub = PubNub(self.get_config())
        test_user_id = 'JamesTiberiusKirk '

        with self.assertRaises(PubNubException) as context:
            pubnub.fetch_user(test_user_id, sync=True)

        self.assertEqual(
            '{"error":{"message":"Requested resource not found.","source":"metadata"},"status":404}',
            context.exception._errormsg
        )
        self.assertEqual(404, context.exception._status_code)

    @pn_vcr.use_cassette('tests/integrational/fixtures/native_sync/users/fetch_users_existing.yaml',
                         filter_query_parameters=['uuid', 'pnsdk', 'signature', 'timestamp'])
    def test_fetch_users_existing(self):
        pubnub = PubNub(self.get_config())
        test_user_id = 'GraceBrewsterMurrayHopper'

        pubnub.remove_user(test_user_id, sync=True)
        pubnub.create_user(user_id=test_user_id, name='Grace Brewster Murray Hopper', email='admiral.grace@user.id',
                           user_type='debugger', user_status='legend', custom={'dob': '1906-12-09'}, sync=True)

        users = pubnub.fetch_users(sync=True)
        self.assertTrue(isinstance(users.result, PNFetchUsersResult))
        self.assertEqual(1, len(users.result.data))
        self.assertEqual(users.result.data[0]['id'], test_user_id)

        pubnub.remove_user(test_user_id, sync=True)

    @pn_vcr.use_cassette('tests/integrational/fixtures/native_sync/users/fetch_users_not_existing.yaml',
                         filter_query_parameters=['uuid', 'pnsdk', 'signature', 'timestamp'])
    def test_fetch_users_not_existing(self):
        pubnub = PubNub(self.get_config())

        with self.assertRaises(PubNubException) as context:
            pubnub.fetch_users(sync=True)

        self.assertEqual(
            '{"error":{"message":"Requested resource not found.","source":"metadata"},"status":404}',
            context.exception._errormsg
        )
        self.assertEqual(404, context.exception._status_code)

    @pn_vcr.use_cassette('tests/integrational/fixtures/native_sync/users/fetch_users_multiple.yaml',
                         filter_query_parameters=['uuid', 'pnsdk', 'signature', 'timestamp'])
    def test_fetch_users_multiple(self):
        pubnub = PubNub(self.get_config())
        test_users = ['GraceBrewsterMurrayHopper', 'MargaretHeafieldHamilton', 'FranBlanche']
        for test_user_id in test_users:
            pubnub.upsert_user(user_id=test_user_id, sync=True)

        users = pubnub.fetch_users(sync=True)
        self.assertTrue(isinstance(users.result, PNFetchUsersResult))
        self.assertEqual(3, len(users.result.data))

        for test_user_id in test_users:
            pubnub.remove_user(test_user_id, sync=True)

    @unittest.skip('Not implemented on a server side')
    def test_fetch_users_multiple_limit(self):
        pubnub = PubNub(self.get_config())
        users = ['GraceBrewsterMurrayHopper', 'MargaretHeafieldHamilton', 'FranBlanche']
        for test_user_id in users:
            pubnub.upsert_user(user_id=test_user_id, sync=True)

        users = pubnub.fetch_users(limit=2, sync=True)
        self.assertTrue(isinstance(users.result, PNFetchUsersResult))
        self.assertEqual(2, len(users.result.data))
        self.assertIsNotNone(users.result.data.page)

        for test_user_id in users:
            pubnub.remove_user(test_user_id, sync=True)
