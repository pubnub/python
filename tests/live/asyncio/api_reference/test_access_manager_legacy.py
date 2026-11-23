"""Docs page: access-manager-legacy (asyncio). The samples of the legacy page."""
from support import assertions as a
from support import redact
from shared.access_manager import perms


async def test_grant_token_spaces_builder(aclients):
    """Snippets: grant_token_spaces_builder, grant_token_spaces_multi, grant_token_spaces_regex,
    grant_token_spaces_multi_regex."""
    pubnub = aclients.asyncio('pam', 'admin')

    # snippet.grant_token_spaces_builder
    from pubnub.models.consumer.v3.space import Space
    from pubnub.models.consumer.v3.user import User

    envelope = await pubnub.grant_token() \
        .spaces([
            Space.id("my_space").read().write().manage(),
        ]) \
        .users([
            User.id("my_user").get().update(),
        ]) \
        .ttl(15) \
        .authorized_user("my-authorized-userId") \
        .future()
    if envelope.is_error():
        print(f"Error: {envelope.status.error_data}")
    else:
        token = envelope.result.token
    # snippet.end
    redact.register(token)
    parsed = pubnub.parse_token(token)
    a.eq(parsed['ttl'], 15)
    a.eq(parsed['authorized_uuid'], 'my-authorized-userId')
    a.eq(parsed['resources']['channels'], {'my_space': perms('read', 'write', 'manage')})
    a.eq(parsed['resources']['uuids'], {'my_user': perms('get', 'update')})

    # snippet.grant_token_spaces_multi
    from pubnub.models.consumer.v3.space import Space
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
    envelope = await pubnub.grant_token() \
        .spaces(spaces) \
        .ttl(15) \
        .users(users) \
        .authorized_user("my-authorized-userId") \
        .future()
    if envelope.is_error():
        print(f"Error: {envelope.status.error_data}")
    # snippet.end
    parsed = pubnub.parse_token(envelope.result.token)
    redact.register(envelope.result.token)
    a.eq(parsed['resources']['channels'], {
        'space-a': perms('read'),
        'space-b': perms('read', 'write'),
        'space-c': perms('read', 'write'),
        'space-d': perms('read', 'write'),
    })
    a.eq(parsed['resources']['uuids'], {'userId-c': perms('get'), 'userId-d': perms('get', 'update')})

    # snippet.grant_token_spaces_regex
    from pubnub.models.consumer.v3.space import Space

    envelope = await pubnub.grant_token() \
        .spaces([Space.pattern("space-[A-Za-z0-9]").read()]) \
        .ttl(15) \
        .authorized_user("my-authorized-userId") \
        .future()
    if envelope.is_error():
        print(f"Error: {envelope.status.error_data}")
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
    envelope = await pubnub.grant_token() \
        .spaces(spaces) \
        .ttl(15) \
        .users(users) \
        .authorized_user("my-authorized-userId") \
        .future()
    if envelope.is_error():
        print(f"Error: {envelope.status.error_data}")
    # snippet.end
    parsed = pubnub.parse_token(envelope.result.token)
    redact.register(envelope.result.token)
    a.eq(parsed['patterns']['channels'], {'space-[A-Za-z0-9]': perms('read')})
    a.eq(sorted(parsed['resources']['channels']), ['space-a', 'space-b', 'space-c', 'space-d'])
    a.eq(parsed['resources']['uuids'], {'user-c': perms('get'), 'user-d': perms('get', 'update')})
