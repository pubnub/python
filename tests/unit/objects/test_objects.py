import asyncio
from pubnub.pubnub import PubNub
from pubnub.pubnub_asyncio import PubNubAsyncio
from pubnub.pnconfiguration import PNConfiguration
from unittest import TestCase


class TestObjectsIsMatchingEtag(TestCase):
    config: PNConfiguration = None
    pubnub: PubNub = None
    pubnub_asyncio: PubNubAsyncio = None

    def setUp(self):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        self.config = PNConfiguration()
        self.config.publish_key = "test"
        self.config.subscribe_key = "test"
        self.config.uuid = "test"
        self.pubnub = PubNub(self.config)
        self.pubnub_asyncio = PubNubAsyncio(self.config)
        return super().setUp()

    def test_get_all_channel_metadata(self):
        builder = self.pubnub.get_all_channel_metadata().if_matches_etag('etag')
        assert builder._custom_headers['If-Match'] == 'etag'

        async_builder = self.pubnub_asyncio.get_all_channel_metadata().if_matches_etag('etag')
        assert async_builder._custom_headers['If-Match'] == 'etag'

    def test_set_channel_metadata(self):
        builder = self.pubnub.set_channel_metadata().if_matches_etag('etag')
        assert builder._custom_headers['If-Match'] == 'etag'

        async_builder = self.pubnub_asyncio.set_channel_metadata().if_matches_etag('etag')
        assert async_builder._custom_headers['If-Match'] == 'etag'

    def test_remove_channel_metadata(self):
        builder = self.pubnub.remove_channel_metadata().if_matches_etag('etag')
        assert builder._custom_headers['If-Match'] == 'etag'

        async_builder = self.pubnub_asyncio.remove_channel_metadata().if_matches_etag('etag')
        assert async_builder._custom_headers['If-Match'] == 'etag'

    def test_get_channel_metadata(self):
        builder = self.pubnub.get_channel_metadata().if_matches_etag('etag')
        assert builder._custom_headers['If-Match'] == 'etag'

        async_builder = self.pubnub_asyncio.get_channel_metadata().if_matches_etag('etag')
        assert async_builder._custom_headers['If-Match'] == 'etag'

    def test_manage_memberships(self):
        builder = self.pubnub.manage_memberships().if_matches_etag('etag')
        assert builder._custom_headers['If-Match'] == 'etag'

        async_builder = self.pubnub_asyncio.manage_memberships().if_matches_etag('etag')
        assert async_builder._custom_headers['If-Match'] == 'etag'

    def test_set_memberships(self):
        builder = self.pubnub.set_memberships().if_matches_etag('etag')
        assert builder._custom_headers['If-Match'] == 'etag'

        async_builder = self.pubnub_asyncio.set_memberships().if_matches_etag('etag')
        assert async_builder._custom_headers['If-Match'] == 'etag'

    def test_get_memberships(self):
        builder = self.pubnub.get_memberships().if_matches_etag('etag')
        assert builder._custom_headers['If-Match'] == 'etag'

        async_builder = self.pubnub_asyncio.get_memberships().if_matches_etag('etag')
        assert async_builder._custom_headers['If-Match'] == 'etag'

    def test_remove_memberships(self):
        builder = self.pubnub.remove_memberships().if_matches_etag('etag')
        assert builder._custom_headers['If-Match'] == 'etag'

        async_builder = self.pubnub_asyncio.remove_memberships().if_matches_etag('etag')
        assert async_builder._custom_headers['If-Match'] == 'etag'

    def test_set_channel_members(self):
        builder = self.pubnub.set_channel_members().if_matches_etag('etag')
        assert builder._custom_headers['If-Match'] == 'etag'

        async_builder = self.pubnub_asyncio.set_channel_members().if_matches_etag('etag')
        assert async_builder._custom_headers['If-Match'] == 'etag'

    def test_remove_channel_members(self):
        builder = self.pubnub.remove_channel_members().if_matches_etag('etag')
        assert builder._custom_headers['If-Match'] == 'etag'

        async_builder = self.pubnub_asyncio.remove_channel_members().if_matches_etag('etag')
        assert async_builder._custom_headers['If-Match'] == 'etag'

    def test_get_channel_members(self):
        builder = self.pubnub.get_channel_members().if_matches_etag('etag')
        assert builder._custom_headers['If-Match'] == 'etag'

        async_builder = self.pubnub_asyncio.get_channel_members().if_matches_etag('etag')
        assert async_builder._custom_headers['If-Match'] == 'etag'

    def test_manage_channel_members(self):
        builder = self.pubnub.manage_channel_members().if_matches_etag('etag')
        assert builder._custom_headers['If-Match'] == 'etag'

        async_builder = self.pubnub_asyncio.manage_channel_members().if_matches_etag('etag')
        assert async_builder._custom_headers['If-Match'] == 'etag'

    def test_set_uuid_metadata(self):
        builder = self.pubnub.set_uuid_metadata().if_matches_etag('etag')
        assert builder._custom_headers['If-Match'] == 'etag'

        async_builder = self.pubnub_asyncio.set_uuid_metadata().if_matches_etag('etag')
        assert async_builder._custom_headers['If-Match'] == 'etag'

    def test_get_uuid_metadata(self):
        builder = self.pubnub.get_uuid_metadata().if_matches_etag('etag')
        assert builder._custom_headers['If-Match'] == 'etag'

        async_builder = self.pubnub_asyncio.get_uuid_metadata().if_matches_etag('etag')
        assert async_builder._custom_headers['If-Match'] == 'etag'

    def test_get_all_uuid_metadata(self):
        builder = self.pubnub.get_all_uuid_metadata().if_matches_etag('etag')
        assert builder._custom_headers['If-Match'] == 'etag'

        async_builder = self.pubnub_asyncio.get_all_uuid_metadata().if_matches_etag('etag')
        assert async_builder._custom_headers['If-Match'] == 'etag'

    def test_remove_uuid_metadata(self):
        builder = self.pubnub.remove_uuid_metadata().if_matches_etag('etag')
        assert builder._custom_headers['If-Match'] == 'etag'

        async_builder = self.pubnub_asyncio.remove_uuid_metadata().if_matches_etag('etag')
        assert async_builder._custom_headers['If-Match'] == 'etag'
