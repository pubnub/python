"""Docs page: access-manager (sync), Access Manager v3 tokens.

Needs the `pam` role keyset (Access Manager). The client that holds a token has no secret key, because a client
with a secret key signs its requests and is never checked against a token. Tokens are registered with the redactor
so they never reach output.
"""
from pubnub.exceptions import PubNubException
from pubnub.models.consumer.v3.channel import Channel
import pytest

from support import assertions as a
from support import redact
from support.wait import eventually
from shared.access_manager import allowed, holder, perms, refused


def test_grant_token_builder(clients):
    """Snippets: grant_token_builder, grant_token_named, parse_token."""
    pubnub = clients.sync('pam', 'admin')

    # snippet.grant_token_builder
    from pubnub.models.consumer.v3.channel import Channel

    envelope = pubnub.grant_token() \
        .channels([
            Channel.id('readonly-channel').read(),
            Channel.id('readwrite-channel').read().write(),
        ]) \
        .authorized_uuid("my-authorized-uuid") \
        .ttl(15) \
        .sync()
    # snippet.end
    token = envelope.result.token
    redact.register(token)
    a.ok(isinstance(token, str) and len(token) > 40, 'the result carries a token')
    a.eq(envelope.result.get_token(), token)

    # snippet.grant_token_named
    from pubnub.models.consumer.v3.channel import Channel

    envelope = pubnub.grant_token(
        channels=[
            Channel.id('readonly-channel').read(),
            Channel.id('readwrite-channel').read().write(),
        ],
        authorized_user_id="my-authorized-uuid",
        ttl=15
    ).sync()
    # snippet.end
    named_token = envelope.result.token
    redact.register(named_token)

    # snippet.parse_token
    parsed_token = pubnub.parse_token(token)
    # snippet.end

    for parsed in (parsed_token, pubnub.parse_token(named_token)):
        a.eq(parsed['version'], 2)
        a.eq(parsed['ttl'], 15)
        a.eq(parsed['authorized_uuid'], 'my-authorized-uuid')
        a.eq(parsed['resources']['channels'], {
            'readonly-channel': perms('read'),
            'readwrite-channel': perms('read', 'write'),
        })
        a.eq(parsed['resources'].get('groups', {}), {})
        a.eq(parsed['resources'].get('uuids', {}), {})
        a.eq(parsed['patterns'].get('channels', {}), {})
        a.ok('categories' not in parsed, 'no category in a token granted without categories')


def test_set_token(clients):
    """Snippet: set_token."""
    admin = clients.sync('pam', 'admin')
    readonly = 'readonly-channel'
    readwrite = 'readwrite-channel'
    fresh = 'set_token_other_channel'
    authorized = 'my-authorized-uuid'
    token = admin.grant_token() \
        .channels([
            Channel.id(readonly).read(),
            Channel.id(readwrite).read().write(),
        ]) \
        .authorized_uuid(authorized) \
        .ttl(15) \
        .sync().result.token
    redact.register(token)
    without = holder(clients, 'my-authorized-uuid')
    pubnub = holder(clients, 'my-authorized-uuid')

    # snippet.set_token
    pubnub.set_token(token)
    # snippet.end

    eventually(lambda: allowed(pubnub, readwrite), timeout=30, what='publish on the granted channel')
    refused(pubnub, readonly)
    refused(pubnub, fresh)
    refused(without, readwrite)


@pytest.mark.timeout(240)
def test_revoke_token(clients):
    """Snippet: revoke_token."""
    admin = clients.sync('pam', 'admin')
    pubnub = admin
    channel = 'revoke-channel'
    token = admin.grant_token() \
        .channels([Channel.id(channel).read().write()]) \
        .authorized_uuid('my-authorized-uuid') \
        .ttl(15) \
        .sync().result.token
    redact.register(token)
    holder_client = holder(clients, 'my-authorized-uuid', token)
    eventually(lambda: allowed(holder_client, channel), timeout=30, what='publish with the fresh token')

    # A client without a secret key cannot revoke. The SDK refuses before it sends the request.
    keyless = holder(clients, 'my-authorized-uuid')
    error = a.raises(PubNubException, lambda: keyless.revoke_token(token).sync())
    a.contains(str(error), 'Secret key is not configured')

    # snippet.revoke_token
    envelope = pubnub.revoke_token(token).sync()
    # snippet.end

    a.eq(envelope.result.status, 200)
    a.eq(str(envelope.result), 'Revoke token success with status: 200')
    eventually(lambda: refused(holder_client, channel), timeout=100, interval=2, what='the revoked token is refused')
    for number in (1, 2):
        fresh_client = holder(clients, 'my-authorized-uuid', token)
        refused(fresh_client, channel)


def test_grant_token_categories(clients):
    """Snippets: grant_token_categories, parse_token_categories."""
    pubnub = clients.sync('pam', 'admin')

    # snippet.grant_token_categories
    from pubnub.models.consumer.v3.category import Category

    envelope = pubnub.grant_token() \
        .categories([Category.channels().get(), Category.uuids().get()]) \
        .authorized_uuid('my_authorized_uuid') \
        .ttl(15) \
        .sync()
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
    channels_only = pubnub.grant_token().categories([Category.channels().get()]).ttl(15).sync().result.token
    redact.register(channels_only)
    a.eq(pubnub.parse_token(channels_only)['categories'], {'channels': {'get': True}})

    # The SDK refuses an invalid category before it sends the request.
    error = a.raises(PubNubException, lambda: pubnub.grant_token().categories([Channel.id('x').get()]).ttl(15).sync())
    a.contains(str(error), 'Unsupported category. Only Category.channels() and Category.uuids() are supported')
    error = a.raises(PubNubException, lambda: pubnub.grant_token().categories([Category.channels()]).ttl(15).sync())
    a.contains(str(error), "Category permissions must be exactly the 'get' permission")


def test_grant_token_multi(clients):
    """Snippets: grant_token_multi, grant_token_regex, grant_token_multi_regex."""
    pubnub = clients.sync('pam', 'admin')
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
    envelope = pubnub.grant_token() \
        .channels(channels) \
        .groups(groups) \
        .uuids(uuids) \
        .authorized_uuid("my-authorized-uuid") \
        .ttl(15) \
        .sync()
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

    envelope = pubnub.grant_token() \
        .channels([Channel.pattern("channel-[A-Za-z0-9]").read()]) \
        .authorized_uuid("my-authorized-uuid") \
        .ttl(15) \
        .sync()
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
    envelope = pubnub.grant_token() \
        .channels(channels) \
        .groups(groups) \
        .uuids(uuids) \
        .authorized_uuid("my-authorized-uuid") \
        .ttl(15) \
        .sync()
    # snippet.end
    parsed = pubnub.parse_token(envelope.result.token)
    redact.register(envelope.result.token)
    a.eq(parsed['patterns']['channels'], {'channel-[A-Za-z0-9]': perms('read')})
    a.eq(sorted(parsed['resources']['channels']), ['channel-a', 'channel-b', 'channel-c', 'channel-d'])
    a.eq(parsed['resources']['groups'], {'channel-group-b': perms('read')})
    a.eq(parsed['resources']['uuids'], {'uuid-c': perms('get'), 'uuid-d': perms('get', 'update')})
