import json
import unittest

from pubnub.endpoints.access.grant_token import GrantToken
from pubnub.models.consumer.v3.category import Category
from pubnub.models.consumer.v3.channel import Channel
from pubnub.models.consumer.v3.uuid import UUID

from pubnub.pubnub import PubNub
from tests.helper import pnconf_pam_copy


GET_PERMISSION = 32


class TestGrantTokenCategories(unittest.TestCase):
    def setUp(self):
        self.pubnub = PubNub(pnconf_pam_copy())

    def permissions(self, grant_token):
        return json.loads(grant_token.build_data())['permissions']

    def test_categories_only_grant(self):
        grant_token = GrantToken(
            self.pubnub,
            ttl=1440,
            categories=[Category.channels().get(), Category.uuids().get()]
        )

        grant_token.validate_resources()
        categories_permission = self.permissions(grant_token)['categories']
        self.assertEqual(categories_permission, {'channels': GET_PERMISSION, 'uuids': GET_PERMISSION})

    def test_categories_alongside_resources(self):
        grant_token = GrantToken(self.pubnub, ttl=1440) \
            .channels([Channel.id('ch1').read(), Channel.pattern('.*').get()]) \
            .uuids([UUID.id('uuid1').get()]) \
            .categories([Category.uuids().get()])

        permissions = self.permissions(grant_token)
        self.assertEqual(permissions['categories'], {'uuids': GET_PERMISSION})
        self.assertEqual(permissions['resources']['channels'], {'ch1': 1})
        self.assertEqual(permissions['patterns']['channels'], {'.*': GET_PERMISSION})
        self.assertEqual(permissions['resources']['uuids'], {'uuid1': GET_PERMISSION})

    def test_resource_get_permissions_do_not_create_category_permissions(self):
        grant_token = GrantToken(self.pubnub, ttl=1440) \
            .channels([Channel.id('ch1').get(), Channel.pattern('.*').get()]) \
            .uuids([UUID.id('uuid1').get(), UUID.pattern('.*').get()])

        permissions = self.permissions(grant_token)
        self.assertNotIn('categories', permissions)
        self.assertEqual(permissions['patterns']['channels'], {'.*': GET_PERMISSION})
        self.assertEqual(permissions['patterns']['uuids'], {'.*': GET_PERMISSION})

    def test_request_without_categories_is_unchanged(self):
        grant_token = GrantToken(self.pubnub, ttl=1440).channels([Channel.id('ch1').read()])

        self.assertEqual(sorted(self.permissions(grant_token).keys()), ['meta', 'patterns', 'resources'])
