import pytest

from pubnub.pubnub import PubNub
from pubnub.pubnub_asyncio import PubNubAsyncio
from pubnub.pnconfiguration import PNConfiguration


class TestPubNubConfig:
    def test_config_copy_with_mutability_lock(self):
        config = PNConfiguration()
        config.publish_key = 'demo'
        config.subscribe_key = 'demo'
        config.user_id = 'demo'

        pubnub = PubNub(config)
        assert config is not pubnub.config
        assert config.user_id == 'demo'

    def test_config_copy_with_mutability_lock_disabled(self):
        config = PNConfiguration()
        config.disable_config_locking = True
        config.publish_key = 'demo'
        config.subscribe_key = 'demo'
        config.user_id = 'demo'

        pubnub = PubNub(config)
        assert config is pubnub.config
        assert config.user_id == 'demo'

    def test_config_mutability_lock(self):
        with pytest.warns(UserWarning):
            config = PNConfiguration()
            config.publish_key = 'demo'
            config.subscribe_key = 'demo'
            config.user_id = 'demo'

            pubnub = PubNub(config)
            assert config is not pubnub.config

            config.user_id = 'test'
            assert pubnub.config.user_id == 'demo'

    def test_config_mutability_lock_disabled(self):
        config = PNConfiguration()
        config.disable_config_locking = True
        config.publish_key = 'demo'
        config.subscribe_key = 'demo'
        config.user_id = 'demo'

        pubnub = PubNub(config)
        assert config is pubnub.config

        config.user_id = 'test'
        assert pubnub.config.user_id == 'test'

    @pytest.mark.asyncio
    async def test_asyncio_config_copy_with_mutability_lock(self):
        config = PNConfiguration()
        config.publish_key = 'demo'
        config.subscribe_key = 'demo'
        config.user_id = 'demo'

        pubnub = PubNubAsyncio(config)
        assert config is not pubnub.config
        assert config.user_id == 'demo'

    @pytest.mark.asyncio
    async def test_asyncio_config_copy_with_mutability_lock_disabled(self):
        config = PNConfiguration()
        config.disable_config_locking = True
        config.publish_key = 'demo'
        config.subscribe_key = 'demo'
        config.user_id = 'demo'

        pubnub = PubNubAsyncio(config)
        assert config is pubnub.config
        assert config.user_id == 'demo'

    @pytest.mark.asyncio
    async def test_asyncio_config_mutability_lock(self):
        with pytest.warns(UserWarning):
            config = PNConfiguration()
            config.publish_key = 'demo'
            config.subscribe_key = 'demo'
            config.user_id = 'demo'

            pubnub = PubNubAsyncio(config)
            assert config is not pubnub.config

            config.user_id = 'test'
            assert pubnub.config.user_id == 'demo'

    @pytest.mark.asyncio
    async def test_asyncio_config_mutability_lock_disabled(self):
        config = PNConfiguration()
        config.disable_config_locking = True
        config.publish_key = 'demo'
        config.subscribe_key = 'demo'
        config.user_id = 'demo'

        pubnub = PubNubAsyncio(config)
        assert config is pubnub.config

        config.user_id = 'test'
        assert pubnub.config.user_id == 'test'
