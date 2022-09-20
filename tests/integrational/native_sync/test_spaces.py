import logging
import unittest

import pubnub
from pubnub.models.consumer.entities.space import PNCreateSpaceResult, PNFetchSpaceResult, PNFetchSpacesResult, \
    PNUpdateSpaceResult, PNUpsertSpaceResult

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

    @pn_vcr.use_cassette('tests/integrational/fixtures/native_sync/spaces/create_space.yaml',
                         filter_query_parameters=['pnsdk', 'signature', 'timestamp'])
    def test_create_space(self):
        test_space_id = 'Trekkie'
        pubnub = PubNub(self.get_config())

        create = pubnub.create_space(test_space_id,
                                     name='Trekkies Fan Space',
                                     description='Live Long and Prosper',
                                     space_type='nerdy',
                                     space_status='fanclub',
                                     custom={'Leader': 'Cpt. James \'Jim\' Tiberius Kirk'},
                                     sync=True)

        assert isinstance(create.result, PNCreateSpaceResult)
        assert 'custom' in create.result.data
        assert {'Leader': 'Cpt. James \'Jim\' Tiberius Kirk'} == create.result.data['custom']

        pubnub.remove_space(test_space_id, sync=True)

    @pn_vcr.use_cassette('tests/integrational/fixtures/native_sync/spaces/update_space.yaml',
                         filter_query_parameters=['pnsdk', 'signature', 'timestamp'])
    def test_update_space(self):
        test_space_id = 'Trekkie'
        pubnub = PubNub(self.get_config())

        pubnub.create_space(test_space_id, sync=True)

        update = pubnub.update_space(test_space_id,
                                     name='Trekkies Fan Space',
                                     description='Live Long and Prosper',
                                     space_type='nerdy',
                                     space_status='fanclub',
                                     custom={'Leader': 'Cpt. James \'Jim\' Tiberius Kirk'},
                                     sync=True)

        assert isinstance(update.result, PNUpdateSpaceResult)
        assert 'custom' in update.result.data
        assert {'Leader': 'Cpt. James \'Jim\' Tiberius Kirk'} == update.result.data['custom']

        pubnub.remove_space(test_space_id, sync=True)

    @pn_vcr.use_cassette('tests/integrational/fixtures/native_sync/spaces/upsert_space.yaml',
                         filter_query_parameters=['pnsdk', 'signature', 'timestamp'])
    def test_upsert_create_space(self):
        test_space_id = 'Trekkie'
        pubnub = PubNub(self.get_config())

        upsert = pubnub.upsert_space(test_space_id,
                                     name='Trekkies Fan Space',
                                     description='Live Long and Prosper',
                                     space_type='nerdy',
                                     space_status='fanclub',
                                     custom={'Leader': 'Cpt. James \'Jim\' Tiberius Kirk'},
                                     sync=True)

        assert isinstance(upsert.result, PNUpsertSpaceResult)
        assert 'custom' in upsert.result.data
        assert {'Leader': 'Cpt. James \'Jim\' Tiberius Kirk'} == upsert.result.data['custom']

        pubnub.remove_space(test_space_id, sync=True)

    @pn_vcr.use_cassette('tests/integrational/fixtures/native_sync/spaces/upsert_update_space.yaml',
                         filter_query_parameters=['pnsdk', 'signature', 'timestamp'])
    def test_upsert_update_space(self):
        test_space_id = 'Trekkie'
        pubnub = PubNub(self.get_config())

        pubnub.create_space(test_space_id, sync=True)

        upsert = pubnub.upsert_space(test_space_id,
                                     name='Trekkies Fan Space',
                                     description='Live Long and Prosper',
                                     space_type='nerdy',
                                     space_status='fanclub',
                                     custom={'Leader': 'Cpt. James \'Jim\' Tiberius Kirk'},
                                     sync=True)

        assert isinstance(upsert.result, PNUpsertSpaceResult)
        assert 'custom' in upsert.result.data
        assert {'Leader': 'Cpt. James \'Jim\' Tiberius Kirk'} == upsert.result.data['custom']

        pubnub.remove_space(test_space_id, sync=True)

    @pn_vcr.use_cassette('tests/integrational/fixtures/native_sync/spaces/create_space_id_collision.yaml',
                         filter_query_parameters=['pnsdk', 'signature', 'timestamp'])
    def test_create_space_id_collision(self):
        test_space_id = 'Trekkie'
        pubnub = PubNub(self.get_config())

        pubnub.create_space(test_space_id, sync=True)
        with self.assertRaises(PubNubException) as context:
            pubnub.create_space(test_space_id,
                                name='Trekkies Fan Space',
                                description='Live Long and Prosper',
                                space_type='nerdy',
                                space_status='fanclub',
                                custom={'Leader': 'Cpt. James \'Jim\' Tiberius Kirk'},
                                sync=True)

        self.assertEqual(
            '{"error":{"message":"Requested resource already exists.","source":"metadata"},"status":409}',
            context.exception._errormsg
        )
        self.assertEqual(409, context.exception._status_code)

        pubnub.remove_space(test_space_id, sync=True)

    @pn_vcr.use_cassette('tests/integrational/fixtures/native_sync/spaces/update_space_id_missing.yaml',
                         filter_query_parameters=['pnsdk', 'signature', 'timestamp'])
    def test_update_space_id_missing(self):
        test_space_id = 'Trekkie'
        pubnub = PubNub(self.get_config())

        with self.assertRaises(PubNubException) as context:
            pubnub.update_space(test_space_id,
                                name='Trekkies Fan Space',
                                description='Live Long and Prosper',
                                space_type='nerdy',
                                space_status='fanclub',
                                custom={'Leader': 'Cpt. James \'Jim\' Tiberius Kirk'},
                                sync=True)

        self.assertEqual(
            '{"error":{"message":"Requested resource does not exists.","source":"metadata"},"status":404}',
            context.exception._errormsg
        )
        self.assertEqual(404, context.exception._status_code)

        pubnub.remove_space(test_space_id, sync=True)

    @pn_vcr.use_cassette('tests/integrational/fixtures/native_sync/spaces/fetch_space_existing.yaml',
                         filter_query_parameters=['pnsdk', 'signature', 'timestamp'])
    def test_fetch_space_existing(self):
        test_space_id = 'Trekkie'
        pubnub = PubNub(self.get_config())
        pubnub.create_space(test_space_id,
                            name='Trekkies Fan Space',
                            description='Live Long and Prosper',
                            space_type='nerdy',
                            space_status='fanclub',
                            custom={'Leader': 'Cpt. James \'Jim\' Tiberius Kirk'},
                            sync=True)
        space = pubnub.fetch_space(test_space_id, sync=True)

        self.assertIs(type(space.result), PNFetchSpaceResult)
        self.assertTrue("custom" in space.result.data.keys())
        self.assertEqual({'Leader': 'Cpt. James \'Jim\' Tiberius Kirk'}, space.result.data["custom"])
        pubnub.remove_space(test_space_id, sync=True)

    @pn_vcr.use_cassette('tests/integrational/fixtures/native_sync/spaces/fetch_space_not_existing.yaml',
                         filter_query_parameters=['pnsdk', 'signature', 'timestamp'])
    def test_fetch_space_not_existing(self):
        test_space_id = 'Trekkie'
        pubnub = PubNub(self.get_config())

        with self.assertRaises(PubNubException) as context:
            pubnub.fetch_space(test_space_id, sync=True)

        self.assertEqual(
            '{"error":{"message":"Requested resource not found.","source":"metadata"},"status":404}',
            context.exception._errormsg
        )
        self.assertEqual(404, context.exception._status_code)

    @pn_vcr.use_cassette('tests/integrational/fixtures/native_sync/spaces/fetch_spaces_existing.yaml',
                         filter_query_parameters=['pnsdk', 'signature', 'timestamp'])
    def test_fetch_spaces_existing(self):
        test_space_id = 'Trekkie'
        pubnub = PubNub(self.get_config())

        pubnub.create_space(test_space_id,
                            name='Trekkies Fan Space',
                            description='Live Long and Prosper',
                            space_type='nerdy',
                            space_status='fanclub',
                            custom={'Leader': 'Cpt. James \'Jim\' Tiberius Kirk'},
                            sync=True)
        spaces = pubnub.fetch_spaces(sync=True)

        self.assertIs(type(spaces.result), PNFetchSpacesResult)
        self.assertEqual(1, len(spaces.result.data))
        self.assertEqual(spaces.result.data[0]['id'], test_space_id)
        self.assertTrue("custom" in spaces.result.data[0].keys())
        self.assertEqual({'Leader': 'Cpt. James \'Jim\' Tiberius Kirk'}, spaces.result.data[0]["custom"])
        pubnub.remove_space(test_space_id, sync=True)

    @pn_vcr.use_cassette('tests/integrational/fixtures/native_sync/spaces/fetch_spaces_not_existing.yaml',
                         filter_query_parameters=['pnsdk', 'signature', 'timestamp'])
    def test_fetch_spaces_not_existing(self):

        pubnub = PubNub(self.get_config())

        with self.assertRaises(PubNubException) as context:
            pubnub.fetch_spaces(sync=True)

        self.assertEqual(
            '{"error":{"message":"Requested resource not found.","source":"metadata"},"status":404}',
            context.exception._errormsg
        )
        self.assertEqual(404, context.exception._status_code)

    @pn_vcr.use_cassette('tests/integrational/fixtures/native_sync/spaces/fetch_spaces_multiple.yaml',
                         filter_query_parameters=['pnsdk', 'signature', 'timestamp'])
    def test_fetch_spaces_multiple(self):
        pubnub = PubNub(self.get_config())
        test_spaces = ['EuclideanSpace', 'BanachSpace', 'HausdorffSpace']
        for space in test_spaces:
            pubnub.upsert_space(space, sync=True)

        spaces = pubnub.fetch_spaces(sync=True)

        self.assertIs(type(spaces.result), PNFetchSpacesResult)
        self.assertEqual(3, len(spaces.result.data))

        for space in test_spaces:
            pubnub.remove_space(space, sync=True)
