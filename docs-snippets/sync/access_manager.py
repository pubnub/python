"""Docs page: access-manager (sync), Access Manager v3 tokens.

Needs the pam keyset. The client that holds a token has no secret key, because a client with a secret key signs its
requests and is never checked against a token. Tokens are registered with the redactor so they never reach output.
"""
from pubnub.exceptions import PubNubException
from pubnub.models.consumer.v3.channel import Channel

from harness import assertions as a
from harness import names, redact
from harness.step import step
from harness.wait import eventually

REGISTERED_NAMES = ['readonly-channel', 'readwrite-channel', 'my-authorized-uuid', 'revoke-channel']

FLAGS = ('read', 'write', 'manage', 'delete', 'get', 'update', 'join')


def perms(*on):
    """The seven flags parse_token returns for one resource, True only for the ones named."""
    return {flag: flag in on for flag in FLAGS}


def holder(clients, user_id, token=None):
    """A client that holds a token. It has no secret key, so every request is checked against the token."""
    client = clients.sync('pam', user_id, secret=False)
    if token:
        client.set_token(token)
    return client


def publish(client, channel):
    return client.publish().channel(channel).message('docs').sync()


def refused(client, channel):
    """A publish the service answers with 403."""
    error = a.raises(PubNubException, publish, client, channel)
    a.eq(error.get_status_code(), 403, 'status code of the refusal')


def allowed(client, channel):
    a.timetoken(publish(client, channel).result.timetoken)


@step('grant_token_builder', 'grant_token_named', 'parse_token', role='pam')
def test_grant_and_parse_token(clients):
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
        a.eq(parsed['authorized_uuid'], names.with_suffix('my-authorized-uuid'))
        a.eq(parsed['resources']['channels'], {
            names.with_suffix('readonly-channel'): perms('read'),
            names.with_suffix('readwrite-channel'): perms('read', 'write'),
        })
        a.eq(parsed['resources'].get('groups', {}), {})
        a.eq(parsed['resources'].get('uuids', {}), {})
        a.eq(parsed['patterns'].get('channels', {}), {})
        a.ok('categories' not in parsed, 'no category in a token granted without categories')


@step('set_token', role='pam')
def test_set_token(clients):
    admin = clients.sync('pam', 'admin')
    readonly = names.with_suffix('readonly-channel')
    readwrite = names.with_suffix('readwrite-channel')
    fresh = names.with_suffix('set_token_other_channel')
    authorized = names.with_suffix('my-authorized-uuid')
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


@step('revoke_token', role='pam', timeout=240)
def test_revoke_token(clients):
    admin = clients.sync('pam', 'admin')
    pubnub = admin
    channel = names.with_suffix('revoke-channel')
    token = admin.grant_token() \
        .channels([Channel.id(channel).read().write()]) \
        .authorized_uuid(names.with_suffix('my-authorized-uuid')) \
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


@step('grant_token_categories', 'parse_token_categories', role='pam')
def test_token_categories(clients):
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
    a.eq(parsed['authorized_uuid'], names.with_suffix('my_authorized_uuid'))
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


@step('grant_token_multi', 'grant_token_regex', 'grant_token_multi_regex', role='pam')
def test_grant_token_resources(clients):
    pubnub = clients.sync('pam', 'admin')
    authorized = names.with_suffix('my-authorized-uuid')

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


@step('grant_token_spaces_builder', 'grant_token_spaces_named', 'grant_token_spaces_multi',
      'grant_token_spaces_regex', 'grant_token_spaces_multi_regex', role='pam')
def test_grant_token_spaces_users(clients):
    pubnub = clients.sync('pam', 'admin')

    # snippet.grant_token_spaces_builder
    from pubnub.models.consumer.v3.space import Space

    envelope = pubnub.grant_token() \
        .authorized_user('some_user_id') \
        .spaces([
            Space.id('some_space_id').read().write(),
            Space.pattern('some_*').read().write()
        ]) \
        .ttl(60) \
        .sync()
    # snippet.end
    parsed = pubnub.parse_token(envelope.result.token)
    redact.register(envelope.result.token)
    a.eq(parsed['ttl'], 60)
    a.eq(parsed['authorized_uuid'], 'some_user_id')
    a.eq(parsed['resources']['channels'], {'some_space_id': perms('read', 'write')})
    a.eq(parsed['patterns']['channels'], {'some_*': perms('read', 'write')})

    # snippet.grant_token_spaces_named
    grant = pubnub.grant_token(
        spaces=[Space.id('some_space_id').read().write(), Space.pattern('some_*').read().write()],
        authorized_user_id="some_user_id",
        ttl=60
    ).sync()
    # snippet.end
    redact.register(grant.result.get_token())
    named = pubnub.parse_token(grant.result.get_token())
    for key in ('ttl', 'authorized_uuid', 'resources', 'patterns'):
        a.eq(named[key], parsed[key], key)

    # snippet.grant_token_spaces_multi
    from pubnub.models.consumer.v3.user import User

    spaces = [
        Space.id("space-a").read(),
        Space.id("space-b").read().write(),
        Space.id("space-c").read().write(),
        Space.id("space-d").read().write()
    ]
    users = [
        User.id("userId-c").get(),
        User.id("userId-d").get().update()
    ]
    envelope = pubnub.grant_token() \
        .spaces(spaces) \
        .ttl(15) \
        .users(users) \
        .authorized_user("my-authorized-userId") \
        .sync()
    # snippet.end
    parsed = pubnub.parse_token(envelope.result.token)
    redact.register(envelope.result.token)
    a.eq(parsed['authorized_uuid'], 'my-authorized-userId')
    a.eq(parsed['resources']['channels'], {
        'space-a': perms('read'),
        'space-b': perms('read', 'write'),
        'space-c': perms('read', 'write'),
        'space-d': perms('read', 'write'),
    })
    a.eq(parsed['resources']['uuids'], {'userId-c': perms('get'), 'userId-d': perms('get', 'update')})

    # snippet.grant_token_spaces_regex
    envelope = pubnub.grant_token() \
        .spaces([Space.pattern("space-[A-Za-z0-9]").read()]) \
        .ttl(15) \
        .authorized_user("my-authorized-userId") \
        .sync()
    # snippet.end
    parsed = pubnub.parse_token(envelope.result.token)
    redact.register(envelope.result.token)
    a.eq(parsed['patterns']['channels'], {'space-[A-Za-z0-9]': perms('read')})

    # snippet.grant_token_spaces_multi_regex
    spaces = [
        Space.id("space-a").read(),
        Space.pattern("space-[A-Za-z0-9]").read(),
        Space.id("space-b").read().write(),
        Space.id("space-c").read().write(),
        Space.id("space-d").read().write()
    ]
    users = [
        User.id("user-c").get(),
        User.id("user-d").get().update()
    ]
    envelope = pubnub.grant_token() \
        .spaces(spaces) \
        .ttl(15) \
        .users(users) \
        .authorized_user("my-authorized-userId") \
        .sync()
    # snippet.end
    parsed = pubnub.parse_token(envelope.result.token)
    redact.register(envelope.result.token)
    a.eq(parsed['patterns']['channels'], {'space-[A-Za-z0-9]': perms('read')})
    a.eq(sorted(parsed['resources']['channels']), ['space-a', 'space-b', 'space-c', 'space-d'])
    a.eq(parsed['resources']['uuids'], {'user-c': perms('get'), 'user-d': perms('get', 'update')})
