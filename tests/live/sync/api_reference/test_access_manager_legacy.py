"""Docs page: access-manager-legacy (sync). The samples of the legacy page, moved from the old
docs-snippets/sync/access_manager.py.
"""
from support import assertions as a
from support import redact
from shared.access_manager import perms


def test_grant_token_spaces_builder(clients):
    """Snippets: grant_token_spaces_builder, grant_token_spaces_named, grant_token_spaces_multi,
    grant_token_spaces_regex, grant_token_spaces_multi_regex."""
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
    from pubnub.models.consumer.v3.space import Space

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
    from pubnub.models.consumer.v3.space import Space

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
    from pubnub.models.consumer.v3.space import Space

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
    from pubnub.models.consumer.v3.space import Space
    from pubnub.models.consumer.v3.user import User

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
