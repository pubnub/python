
from pubnub.pubnub import PubNub
from pubnub.models.consumer.v3.access_manager import PNGrantTokenResult
from pubnub.models.consumer.v3.channel import Channel
from pubnub.models.consumer.v3.group import Group
from pubnub.models.consumer.v3.uuid import UUID
from pubnub.models.consumer.v3.space import Space
from tests.helper import pnconf_pam_env_copy
from tests.integrational.vcr_helper import pn_vcr

pubnub = PubNub(pnconf_pam_env_copy())
pubnub.config.uuid = "test_grant"


@pn_vcr.use_cassette(
    'tests/integrational/fixtures/native_sync/pam/grant_token_with_uuid_and_channels.json', serializer='pn_json',
    filter_query_parameters=['uuid', 'seqn', 'pnsdk', 'timestamp', 'signature']
)
def test_grant_auth_key_with_uuid_and_channels():
    envelope = pubnub.grant_token() \
        .ttl(60) \
        .authorized_uuid('some_uuid') \
        .channels([
            Channel().id('some_channel_id').read().write().manage().delete().get().update().join(),
            Channel().pattern('some_*').read().write().manage()
        ]) \
        .groups([
            Group().id('some_group_id').read().manage(),
            Group().pattern('some_*').read(),
        ]) \
        .uuids([
            UUID().id('some_uuid').get().update().delete(),
            UUID().pattern('some_*').get()
        ]) \
        .sync()
    assert isinstance(envelope.result, PNGrantTokenResult)
    assert envelope.result.token


@pn_vcr.use_cassette(
    'tests/integrational/fixtures/native_sync/pam/grant_token_user_space.json', serializer='pn_json',
    filter_query_parameters=['uuid', 'seqn', 'pnsdk', 'timestamp', 'signature']
)
def test_grant_auth_key_with_user_id_and_spaces():
    envelope = pubnub.grant_token()\
        .ttl(60)\
        .authorized_user('some_user_id')\
        .spaces([
            Space().id('some_space_id').read().write(),
            Space().pattern('some_*').read().write()
        ])\
        .sync()
    assert isinstance(envelope.result, PNGrantTokenResult)
    assert envelope.result.token
