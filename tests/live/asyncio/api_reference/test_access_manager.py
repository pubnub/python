"""Docs page: access-manager (asyncio), Access Manager v3 tokens. Same steps as sync/access_manager.py with await.

The asyncio client does not raise on an HTTP or validation error. future() resolves with a PubNubAsyncioException
object instead, so the helpers below inspect the resolved value.
"""
from pubnub.models.consumer.v3.channel import Channel
import pytest

from support import assertions as a
from support import redact
from support.wait import aeventually
from shared.access_manager import (
    allowed_async as allowed, failure, holder_async as holder, perms, refused_async as refused,
)


async def test_grant_token_builder(aclients):
    """Snippets: grant_token_builder, parse_token."""
    pubnub = aclients.asyncio('pam', 'admin')

    # snippet.grant_token_builder
    from pubnub.models.consumer.v3.channel import Channel

    envelope = await pubnub.grant_token() \
        .channels([
            Channel.id('readonly-channel').read(),
            Channel.id('readwrite-channel').read().write(),
        ]) \
        .authorized_uuid("my-authorized-uuid") \
        .ttl(15) \
        .future()
    if envelope.is_error():
        print(f"Error: {envelope.status.error_data}")
    # snippet.end
    token = envelope.result.token
    redact.register(token)
    a.ok(isinstance(token, str) and len(token) > 40, 'the result carries a token')
    a.eq(envelope.result.get_token(), token)

    # snippet.parse_token
    parsed_token = pubnub.parse_token(token)
    # snippet.end

    a.eq(parsed_token['version'], 2)
    a.eq(parsed_token['ttl'], 15)
    a.eq(parsed_token['authorized_uuid'], 'my-authorized-uuid')
    a.eq(parsed_token['resources']['channels'], {
        'readonly-channel': perms('read'),
        'readwrite-channel': perms('read', 'write'),
    })
    a.eq(parsed_token['resources'].get('groups', {}), {})
    a.eq(parsed_token['resources'].get('uuids', {}), {})
    a.eq(parsed_token['patterns'].get('channels', {}), {})
    a.ok('categories' not in parsed_token, 'no category in a token granted without categories')


async def test_set_token(aclients):
    """Snippet: set_token."""
    admin = aclients.asyncio('pam', 'admin')
    readonly = 'readonly-channel'
    readwrite = 'readwrite-channel'
    fresh = 'set_token_other_channel'
    granted = await admin.grant_token() \
        .channels([Channel.id(readonly).read(), Channel.id(readwrite).read().write()]) \
        .authorized_uuid('my-authorized-uuid') \
        .ttl(15) \
        .future()
    token = granted.result.token
    redact.register(token)
    without = holder(aclients, 'my-authorized-uuid')
    pubnub = holder(aclients, 'my-authorized-uuid')

    # snippet.set_token
    pubnub.set_token(token)
    # snippet.end

    await aeventually(lambda: allowed(pubnub, readwrite), timeout=30, what='publish on the granted channel')
    await refused(pubnub, readonly)
    await refused(pubnub, fresh)
    await refused(without, readwrite)


@pytest.mark.timeout(240)
async def test_revoke_token(aclients):
    """Snippet: revoke_token."""
    admin = aclients.asyncio('pam', 'admin')
    pubnub = admin
    channel = 'revoke-channel'
    granted = await admin.grant_token() \
        .channels([Channel.id(channel).read().write()]) \
        .authorized_uuid('my-authorized-uuid') \
        .ttl(15) \
        .future()
    token = granted.result.token
    redact.register(token)
    holder_client = holder(aclients, 'my-authorized-uuid', token)
    await aeventually(lambda: allowed(holder_client, channel), timeout=30, what='publish with the fresh token')

    # A client without a secret key cannot revoke. The SDK refuses before it sends the request.
    keyless = holder(aclients, 'my-authorized-uuid')
    a.contains(failure(await keyless.revoke_token(token).future()), 'Secret key is not configured')

    # snippet.revoke_token
    envelope = await pubnub.revoke_token(token).future()
    if envelope.is_error():
        print(f"Error: {envelope.status.error_data}")
    # snippet.end

    a.eq(envelope.result.status, 200)
    a.eq(str(envelope.result), 'Revoke token success with status: 200')
    await aeventually(lambda: refused(holder_client, channel), timeout=100, interval=2,
                      what='the revoked token is refused')
    for number in (1, 2):
        await refused(holder(aclients, 'my-authorized-uuid', token), channel)


async def test_grant_token_categories(aclients):
    """Snippets: grant_token_categories, parse_token_categories."""
    pubnub = aclients.asyncio('pam', 'admin')

    # snippet.grant_token_categories
    from pubnub.models.consumer.v3.category import Category

    envelope = await pubnub.grant_token(
        categories=[Category.channels().get(), Category.uuids().get()],
        authorized_user_id='my_authorized_uuid',
        ttl=15
    ).future()
    if envelope.is_error():
        print(f"Error: {envelope.status.error_data}")
    else:
        token = envelope.result.get_token()
    # snippet.end
    redact.register(token)

    # snippet.parse_token_categories
    categories = pubnub.parse_token(token)['categories']
    # snippet.end

    a.eq(categories, {'channels': {'get': True}, 'uuids': {'get': True}})
    parsed = pubnub.parse_token(token)
    a.eq(parsed['authorized_uuid'], 'my_authorized_uuid')
    a.eq(parsed['resources'].get('channels', {}), {})
    a.eq(parsed['resources'].get('uuids', {}), {})

    # A token with a single category carries only that category.
    single = await pubnub.grant_token().categories([Category.channels().get()]).ttl(15).future()
    redact.register(single.result.token)
    a.eq(pubnub.parse_token(single.result.token)['categories'], {'channels': {'get': True}})

    # The SDK refuses an invalid category before it sends the request.
    resolved = await pubnub.grant_token().categories([Channel.id('x').get()]).ttl(15).future()
    a.contains(failure(resolved), 'Unsupported category. Only Category.channels() and Category.uuids() are supported')
    resolved = await pubnub.grant_token().categories([Category.channels()]).ttl(15).future()
    a.contains(failure(resolved), "Category permissions must be exactly the 'get' permission")


async def test_grant_token_multi(aclients):
    """Snippets: grant_token_multi, grant_token_regex, grant_token_multi_regex."""
    pubnub = aclients.asyncio('pam', 'admin')
    authorized = 'my-authorized-uuid'

    # snippet.grant_token_multi
    from pubnub.models.consumer.v3.channel import Channel
    from pubnub.models.consumer.v3.group import Group
    from pubnub.models.consumer.v3.uuid import UUID

    channels = [
        Channel.id("channel-a").read(),
        Channel.id("channel-b").read().write(),
        Channel.id("channel-c").read().write(),
        Channel.id("channel-d").read().write()
    ]
    groups = [
        Group.id("channel-group-b").read()
    ]
    uuids = [
        UUID.id("uuid-c").get(),
        UUID.id("uuid-d").get().update()
    ]
    envelope = await pubnub.grant_token() \
        .channels(channels) \
        .groups(groups) \
        .ttl(15) \
        .uuids(uuids) \
        .authorized_uuid("my-authorized-uuid") \
        .future()
    if envelope.is_error():
        print(f"Error: {envelope.status.error_data}")
    # snippet.end
    parsed = pubnub.parse_token(envelope.result.token)
    redact.register(envelope.result.token)
    a.eq(parsed['authorized_uuid'], authorized)
    a.eq(parsed['resources']['channels'], {
        'channel-a': perms('read'),
        'channel-b': perms('read', 'write'),
        'channel-c': perms('read', 'write'),
        'channel-d': perms('read', 'write'),
    })
    a.eq(parsed['resources']['groups'], {'channel-group-b': perms('read')})
    a.eq(parsed['resources']['uuids'], {'uuid-c': perms('get'), 'uuid-d': perms('get', 'update')})
    a.eq(parsed['patterns'].get('channels', {}), {})

    # snippet.grant_token_regex
    from pubnub.models.consumer.v3.channel import Channel

    envelope = await pubnub.grant_token() \
        .channels([Channel.pattern("channel-[A-Za-z0-9]").read()]) \
        .ttl(15) \
        .authorized_uuid("my-authorized-uuid") \
        .future()
    if envelope.is_error():
        print(f"Error: {envelope.status.error_data}")
    # snippet.end
    parsed = pubnub.parse_token(envelope.result.token)
    redact.register(envelope.result.token)
    a.eq(parsed['patterns']['channels'], {'channel-[A-Za-z0-9]': perms('read')})
    a.eq(parsed['resources'].get('channels', {}), {})

    # snippet.grant_token_multi_regex
    from pubnub.models.consumer.v3.channel import Channel
    from pubnub.models.consumer.v3.group import Group
    from pubnub.models.consumer.v3.uuid import UUID

    channels = [
        Channel.id("channel-a").read(),
        Channel.pattern("channel-[A-Za-z0-9]").read(),
        Channel.id("channel-b").read().write(),
        Channel.id("channel-c").read().write(),
        Channel.id("channel-d").read().write()
    ]
    groups = [
        Group.id("channel-group-b").read()
    ]
    uuids = [
        UUID.id("uuid-c").get(),
        UUID.id("uuid-d").get().update()
    ]
    envelope = await pubnub.grant_token() \
        .channels(channels) \
        .ttl(15) \
        .groups(groups) \
        .uuids(uuids) \
        .authorized_uuid("my-authorized-uuid") \
        .future()
    if envelope.is_error():
        print(f"Error: {envelope.status.error_data}")
    # snippet.end
    parsed = pubnub.parse_token(envelope.result.token)
    redact.register(envelope.result.token)
    a.eq(parsed['patterns']['channels'], {'channel-[A-Za-z0-9]': perms('read')})
    a.eq(sorted(parsed['resources']['channels']), ['channel-a', 'channel-b', 'channel-c', 'channel-d'])
    a.eq(parsed['resources']['groups'], {'channel-group-b': perms('read')})
    a.eq(parsed['resources']['uuids'], {'uuid-c': perms('get'), 'uuid-d': perms('get', 'update')})
