import pytest

from pubnub.exceptions import PubNubException
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


@pn_vcr.use_cassette(
    'tests/integrational/fixtures/native_sync/pam/grant_token_min_ttl.json', serializer='pn_json',
    filter_query_parameters=['uuid', 'seqn', 'pnsdk', 'timestamp', 'signature']
)
def test_grant_token_min_ttl():
    pubnub = PubNub(pnconf_pam_env_copy())
    pubnub.config.uuid = "test_grant_min_ttl"

    envelope = pubnub.grant_token() \
        .ttl(1) \
        .channels([Channel().id('test_channel').read()]) \
        .sync()

    assert isinstance(envelope.result, PNGrantTokenResult)
    assert envelope.result.token


@pn_vcr.use_cassette(
    'tests/integrational/fixtures/native_sync/pam/grant_token_max_ttl.json', serializer='pn_json',
    filter_query_parameters=['uuid', 'seqn', 'pnsdk', 'timestamp', 'signature']
)
def test_grant_token_max_ttl():
    pubnub = PubNub(pnconf_pam_env_copy())
    pubnub.config.uuid = "test_grant_max_ttl"

    envelope = pubnub.grant_token() \
        .ttl(43200) \
        .channels([Channel().id('test_channel').read()]) \
        .sync()

    assert isinstance(envelope.result, PNGrantTokenResult)
    assert envelope.result.token


@pn_vcr.use_cassette(
    'tests/integrational/fixtures/native_sync/pam/grant_token_invalid_ttl.json', serializer='pn_json',
    filter_query_parameters=['uuid', 'seqn', 'pnsdk', 'timestamp', 'signature']
)
def test_grant_token_invalid_ttl():
    pubnub = PubNub(pnconf_pam_env_copy())
    pubnub.config.uuid = "test_grant_invalid_ttl"

    # Test with TTL below minimum (should raise exception)
    with pytest.raises(PubNubException):
        pubnub.grant_token() \
            .ttl(0) \
            .channels([Channel().id('test_channel').read()]) \
            .sync()

    # Test with TTL above maximum (should raise exception)
    with pytest.raises(PubNubException):
        pubnub.grant_token() \
            .ttl(43201) \
            .channels([Channel().id('test_channel').read()]) \
            .sync()


@pn_vcr.use_cassette(
    'tests/integrational/fixtures/native_sync/pam/grant_token_format_validation.json', serializer='pn_json',
    filter_query_parameters=['uuid', 'seqn', 'pnsdk', 'timestamp', 'signature']
)
def test_grant_token_format_validation():
    pubnub = PubNub(pnconf_pam_env_copy())
    pubnub.config.uuid = "test_grant_format"

    envelope = pubnub.grant_token() \
        .ttl(60) \
        .channels([Channel().id('test_channel').read()]) \
        .sync()

    assert isinstance(envelope.result, PNGrantTokenResult)
    assert envelope.result.token

    # Basic format validation - token should be a non-empty string
    assert isinstance(envelope.result.token, str)
    assert len(envelope.result.token) > 0


@pn_vcr.use_cassette(
    'tests/integrational/fixtures/native_sync/pam/grant_token_channel_individual_permissions.json',
    serializer='pn_json', filter_query_parameters=['uuid', 'seqn', 'pnsdk', 'timestamp', 'signature']
)
def test_grant_token_channel_individual_permissions():
    pubnub = PubNub(pnconf_pam_env_copy())
    pubnub.config.uuid = "test_channel_permissions"

    # Test each permission individually
    permissions = {
        "read_only": Channel().id('channel_read').read(),
        "write_only": Channel().id('channel_write').write(),
        "manage_only": Channel().id('channel_manage').manage(),
        "delete_only": Channel().id('channel_delete').delete(),
        "get_only": Channel().id('channel_get').get(),
        "update_only": Channel().id('channel_update').update(),
        "join_only": Channel().id('channel_join').join()
    }

    for permission_name, channel in permissions.items():
        envelope = pubnub.grant_token() \
            .ttl(60) \
            .channels([channel]) \
            .sync()

        assert isinstance(envelope.result, PNGrantTokenResult)
        assert envelope.result.token


@pn_vcr.use_cassette(
    'tests/integrational/fixtures/native_sync/pam/grant_token_channel_all_permissions.json', serializer='pn_json',
    filter_query_parameters=['uuid', 'seqn', 'pnsdk', 'timestamp', 'signature']
)
def test_grant_token_channel_all_permissions():
    pubnub = PubNub(pnconf_pam_env_copy())
    pubnub.config.uuid = "test_channel_all_perms"

    envelope = pubnub.grant_token() \
        .ttl(60) \
        .channels([Channel().id('all_permissions_channel').read().write().manage().delete().get().update().join()]) \
        .sync()

    assert isinstance(envelope.result, PNGrantTokenResult)
    assert envelope.result.token


@pn_vcr.use_cassette(
    'tests/integrational/fixtures/native_sync/pam/grant_token_groups_permissions.json', serializer='pn_json',
    filter_query_parameters=['uuid', 'seqn', 'pnsdk', 'timestamp', 'signature']
)
def test_grant_token_group_permissions():
    pubnub = PubNub(pnconf_pam_env_copy())
    pubnub.config.uuid = "test_group_permissions"

    envelope = pubnub.grant_token() \
        .ttl(60) \
        .groups([
            Group().id('group1').read(),  # Read-only group
            Group().id('group2').read().manage(),  # Read + manage group
        ]) \
        .sync()

    assert isinstance(envelope.result, PNGrantTokenResult)
    assert envelope.result.token


@pn_vcr.use_cassette(
    'tests/integrational/fixtures/native_sync/pam/grant_token_users_permissions.json', serializer='pn_json',
    filter_query_parameters=['uuid', 'seqn', 'pnsdk', 'timestamp', 'signature']
)
def test_grant_token_users_permissions():
    pubnub = PubNub(pnconf_pam_env_copy())
    pubnub.config.uuid = "test_users_permissions"

    envelope = pubnub.grant_token() \
        .ttl(60) \
        .authorized_user('test_user') \
        .uuids([
            UUID().id('user1').get(),  # Get only
            UUID().id('user2').get().update(),  # Get + update
            UUID().id('user3').get().update().delete()  # All user permissions
        ]) \
        .sync()

    assert isinstance(envelope.result, PNGrantTokenResult)
    assert envelope.result.token


@pn_vcr.use_cassette(
    'tests/integrational/fixtures/native_sync/pam/grant_token_spaces_permissions.json', serializer='pn_json',
    filter_query_parameters=['uuid', 'seqn', 'pnsdk', 'timestamp', 'signature']
)
def test_grant_token_spaces_permissions():
    pubnub = PubNub(pnconf_pam_env_copy())
    pubnub.config.uuid = "test_spaces_permissions"

    envelope = pubnub.grant_token() \
        .ttl(60) \
        .spaces([
            Space().id('space1').read(),  # Read only
            Space().id('space2').read().write(),  # Read + write
            Space().id('space3').read().write().manage().delete()  # All space permissions
        ]) \
        .sync()

    assert isinstance(envelope.result, PNGrantTokenResult)
    assert envelope.result.token


@pn_vcr.use_cassette(
    'tests/integrational/fixtures/native_sync/pam/grant_token_mixed_resources.json', serializer='pn_json',
    filter_query_parameters=['uuid', 'seqn', 'pnsdk', 'timestamp', 'signature']
)
def test_grant_token_mixed_resources():
    pubnub = PubNub(pnconf_pam_env_copy())
    pubnub.config.uuid = "test_mixed_resources"

    envelope = pubnub.grant_token() \
        .ttl(60) \
        .authorized_uuid('test_user') \
        .channels([
            Channel().id('channel1').read().write()
        ]) \
        .groups([
            Group().id('group1').read().manage()
        ]) \
        .uuids([
            UUID().id('user1').get().update()
        ]) \
        .spaces([
            Space().id('space1').read().write()
        ]) \
        .sync()

    assert isinstance(envelope.result, PNGrantTokenResult)
    assert envelope.result.token


@pn_vcr.use_cassette(
    'tests/integrational/fixtures/native_sync/pam/grant_token_exact_pattern.json', serializer='pn_json',
    filter_query_parameters=['uuid', 'seqn', 'pnsdk', 'timestamp', 'signature']
)
def test_grant_token_exact_pattern():
    pubnub = PubNub(pnconf_pam_env_copy())
    pubnub.config.uuid = "test_exact_pattern"

    envelope = pubnub.grant_token() \
        .ttl(60) \
        .channels([
            Channel().pattern('^exact-channel$').read().write(),  # Exact match
            Channel().pattern('^prefix-[0-9]+$').read()  # Exact match with regex
        ]) \
        .sync()

    assert isinstance(envelope.result, PNGrantTokenResult)
    assert envelope.result.token


@pn_vcr.use_cassette(
    'tests/integrational/fixtures/native_sync/pam/grant_token_substring_pattern.json', serializer='pn_json',
    filter_query_parameters=['uuid', 'seqn', 'pnsdk', 'timestamp', 'signature']
)
def test_grant_token_substring_pattern():
    pubnub = PubNub(pnconf_pam_env_copy())
    pubnub.config.uuid = "test_substring_pattern"

    envelope = pubnub.grant_token() \
        .ttl(60) \
        .channels([
            Channel().pattern('chat').read(),  # Matches any channel containing 'chat'
            Channel().pattern('room-').write()  # Matches any channel containing 'room-'
        ]) \
        .sync()

    assert isinstance(envelope.result, PNGrantTokenResult)
    assert envelope.result.token


@pn_vcr.use_cassette(
    'tests/integrational/fixtures/native_sync/pam/grant_token_wildcard_pattern.json', serializer='pn_json',
    filter_query_parameters=['uuid', 'seqn', 'pnsdk', 'timestamp', 'signature']
)
def test_grant_token_wildcard_pattern():
    pubnub = PubNub(pnconf_pam_env_copy())
    pubnub.config.uuid = "test_wildcard_pattern"

    envelope = pubnub.grant_token() \
        .ttl(60) \
        .groups([
            Group().pattern('group_*').read(),  # Matches groups starting with 'group_'
            Group().pattern('channel_*_tst').manage()  # Matches groups starting with 'channel_' and ending with '_tst'
        ]) \
        .sync()

    assert isinstance(envelope.result, PNGrantTokenResult)
    assert envelope.result.token


@pn_vcr.use_cassette(
    'tests/integrational/fixtures/native_sync/pam/grant_token_regex_patterns.json', serializer='pn_json',
    filter_query_parameters=['uuid', 'seqn', 'pnsdk', 'timestamp', 'signature']
)
def test_grant_token_regex_patterns():
    pubnub = PubNub(pnconf_pam_env_copy())
    pubnub.config.uuid = "test_regex_patterns"

    envelope = pubnub.grant_token() \
        .ttl(60) \
        .users([
            UUID().pattern('^user-[0-9]+$').get(),  # Matches user-123, user-456, etc.
        ]) \
        .spaces([
            Space().pattern('^space-[a-zA-Z]+$').read().write()  # Matches space-abc, space-XYZ, etc.
        ]) \
        .sync()

    assert isinstance(envelope.result, PNGrantTokenResult)
    assert envelope.result.token


@pn_vcr.use_cassette(
    'tests/integrational/fixtures/native_sync/pam/grant_token_mixed_patterns.json', serializer='pn_json',
    filter_query_parameters=['uuid', 'seqn', 'pnsdk', 'timestamp', 'signature']
)
def test_grant_token_mixed_patterns():
    pubnub = PubNub(pnconf_pam_env_copy())
    pubnub.config.uuid = "test_mixed_patterns"

    envelope = pubnub.grant_token() \
        .ttl(60) \
        .channels([
            Channel().id('specific-channel').read().write(),  # Exact channel
            Channel().pattern('channel_*').read()  # Pattern-based channel
        ]) \
        .groups([
            Group().id('specific-group').manage(),  # Exact group
            Group().pattern('group_*').read()  # Pattern-based group
        ]) \
        .sync()

    assert isinstance(envelope.result, PNGrantTokenResult)
    assert envelope.result.token


@pn_vcr.use_cassette(
    'tests/integrational/fixtures/native_sync/pam/grant_token_authorization.json', serializer='pn_json',
    filter_query_parameters=['uuid', 'seqn', 'pnsdk', 'timestamp', 'signature']
)
def test_grant_token_authorization():
    pubnub = PubNub(pnconf_pam_env_copy())
    pubnub.config.uuid = "test_authorization"

    # Test with authorized_uuid
    uuid_envelope = pubnub.grant_token() \
        .ttl(60) \
        .authorized_uuid('specific-uuid') \
        .channels([Channel().id('test-channel').read()]) \
        .sync()

    assert isinstance(uuid_envelope.result, PNGrantTokenResult)
    assert uuid_envelope.result.token

    # Test with authorized_user
    user_envelope = pubnub.grant_token() \
        .ttl(60) \
        .authorized_user('specific-user') \
        .channels([Channel().id('test-channel').read()]) \
        .sync()

    assert isinstance(user_envelope.result, PNGrantTokenResult)
    assert user_envelope.result.token


@pn_vcr.use_cassette(
    'tests/integrational/fixtures/native_sync/pam/grant_token_metadata.json', serializer='pn_json',
    filter_query_parameters=['uuid', 'seqn', 'pnsdk', 'timestamp', 'signature']
)
def test_grant_token_metadata():
    pubnub = PubNub(pnconf_pam_env_copy())
    pubnub.config.uuid = "test_metadata"

    # Test with custom metadata
    custom_meta = {
        "app_id": "my-app",
        "user_type": "admin",
        "custom_field": "value"
    }

    envelope = pubnub.grant_token() \
        .ttl(60) \
        .meta(custom_meta) \
        .channels([Channel().id('test-channel').read()]) \
        .sync()

    assert isinstance(envelope.result, PNGrantTokenResult)
    assert envelope.result.token


@pn_vcr.use_cassette(
    'tests/integrational/fixtures/native_sync/pam/grant_token_large_metadata.json', serializer='pn_json',
    filter_query_parameters=['uuid', 'seqn', 'pnsdk', 'timestamp', 'signature']
)
def test_grant_token_large_metadata():
    pubnub = PubNub(pnconf_pam_env_copy())
    pubnub.config.uuid = "test_large_metadata"

    # Test with large metadata payload
    large_meta = {
        "app_data": {
            "version": "1.0.0",
            "environment": "production",
            "features": ["chat", "presence", "push", "storage"],
            "config": {
                "timeout": 5000,
                "retries": 3,
                "cache_size": 1000,
                "debug": False
            }
        },
        "user_data": {
            "id": "12345",
            "roles": ["admin", "moderator", "user"],
            "permissions": ["read", "write", "delete"],
            "settings": {
                "notifications": True,
                "theme": "dark",
                "language": "en"
            }
        }
    }

    envelope = pubnub.grant_token() \
        .ttl(60) \
        .meta(large_meta) \
        .channels([Channel().id('test-channel').read()]) \
        .sync()

    assert isinstance(envelope.result, PNGrantTokenResult)
    assert envelope.result.token
