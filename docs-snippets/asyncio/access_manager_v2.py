"""Docs page: access-manager-v2 (asyncio), the legacy grant(). Same steps as sync/access_manager_v2.py with await.

Every grant is closed in a finally (all flags false, ttl 1). The step that grants at application level is the last one
of this file. The asyncio client does not raise on an HTTP error, future() resolves with a PubNubAsyncioException.
"""
from pubnub.exceptions import PubNubAsyncioException

from harness import assertions as a
from harness import names
from harness.listeners import alisten
from harness.step import step
from harness.wait import aeventually

REGISTERED_NAMES = ['my_channel-pnpres', 'girish', 'girish2', 'cg2', 'cg3']

ALL_FALSE = ('read', 'write', 'manage', 'delete', 'get', 'update', 'join')


def holder(aclients, user_id, auth_key=None):
    """A client that has no secret key, so every request is checked against its auth key."""
    client = aclients.asyncio('pam', user_id, secret=False)
    client.config.auth_key = auth_key
    return client


async def close_grant(admin, channels=None, groups=None, uuids=None, auth_keys=None):
    """Take back what a step granted: every flag false, ttl 1."""
    builder = admin.grant()
    for flag in ALL_FALSE:
        builder = getattr(builder, flag)(False)
    if channels:
        builder = builder.channels(channels)
    if groups:
        builder = builder.channel_groups(groups)
    if uuids:
        builder = builder.uuids(uuids)
    if auth_keys:
        builder = builder.auth_keys(auth_keys)
    return await builder.ttl(1).future()


async def publish(client, channel):
    return await client.publish().channel(channel).message('docs').future()


async def refused(client, channel):
    resolved = await publish(client, channel)
    a.ok(isinstance(resolved, PubNubAsyncioException), 'the publish was refused')
    a.eq(resolved.status.status_code, 403, 'status code of the refusal')


async def allowed(client, channel):
    resolved = await publish(client, channel)
    a.ok(not isinstance(resolved, PubNubAsyncioException), 'the publish went through')
    a.timetoken(resolved.result.timetoken)


def good(resolved):
    """A future() that resolved with a result, not with an error object. Returns the result."""
    a.ok(not isinstance(resolved, PubNubAsyncioException), 'the call succeeded')
    return resolved.result


def failure(resolved):
    a.ok(isinstance(resolved, PubNubAsyncioException), 'the call resolved with an error object')
    return str(resolved.value())


def key_flags(key_data):
    return (key_data.read_enabled, key_data.write_enabled, key_data.manage_enabled, key_data.delete_enabled)


@step('grant_channel_auth', role='pam')
async def test_grant_channel_and_auth_key(aclients):
    pubnub = aclients.asyncio('pam', 'admin')
    channels = [names.with_suffix(name) for name in ('ch1', 'ch2', 'ch3')]
    groups = [names.with_suffix(name) for name in ('cg1', 'cg2')]
    other = names.with_suffix('ch_no_grant')
    try:
        # snippet.grant_channel_auth
        envelope = await pubnub.grant().channels(["ch1", "ch2", "ch3"]).\
            channel_groups(["cg1", "cg2"]).\
            auth_keys(["key1", "key2"]).\
            read(True).write(True).manage(True).\
            future()
        # snippet.end

        result = good(envelope)
        a.eq(result.level, 'channel-group+auth')
        a.eq(result.ttl, 1440)
        a.ok(isinstance(result.subscribe_key, str) and result.subscribe_key, 'the result names the subscribe key')
        a.eq(sorted(result.channels), sorted(channels))
        a.eq(sorted(result.groups), sorted(groups))
        for data in list(result.channels.values()) + list(result.groups.values()):
            a.eq(sorted(data.auth_keys), ['key1', 'key2'])
            for key_data in data.auth_keys.values():
                a.eq(key_flags(key_data)[:3], (True, True, True))
        await aeventually(lambda: allowed(holder(aclients, 'granted', 'key1'), channels[0]), timeout=30,
                          what='a granted auth key publishes')
        await refused(holder(aclients, 'stranger', 'key3'), channels[0])
        await refused(holder(aclients, 'granted', 'key1'), other)
    finally:
        await close_grant(pubnub, channels, groups, auth_keys=['key1', 'key2'])


@step('grant_channel_all_users', 'grant_channel_level', role='pam')
async def test_grant_channel_level(aclients):
    pubnub = aclients.asyncio('pam', 'admin')
    channel = names.with_suffix('my_channel')
    other = names.with_suffix('ch_no_grant')
    try:
        # snippet.grant_channel_all_users
        envelope = await pubnub.grant().channels("my_channel").read(True).write(True).future()
        # snippet.end

        result = good(envelope)
        a.eq(result.level, 'channel')
        a.eq(result.ttl, 1440)
        a.eq((result.channels[channel].read_enabled, result.channels[channel].write_enabled), (True, True))
        client = holder(aclients, 'anyone')
        await aeventually(lambda: allowed(client, channel), timeout=30, what='publish without an auth key')
        await refused(client, other)

        # snippet.grant_channel_level
        envelope = await pubnub.grant().channels("my_channel"). \
            read(True).write(True). \
            future()
        # snippet.end

        result = good(envelope)
        a.eq(result.level, 'channel')
        a.eq(result.channels[channel].read_enabled, True)
    finally:
        await close_grant(pubnub, [channel])


@step('grant_channel_ro_auth', 'grant_user_level', role='pam', timeout=900)
async def test_grant_user_level(aclients):
    pubnub = aclients.asyncio('pam', 'admin')
    channel = names.with_suffix('my_channel')
    other = names.with_suffix('ch_no_grant')
    try:
        # snippet.grant_channel_ro_auth
        envelope = await pubnub.grant().channels("my_channel").read(True).write(False).\
            auth_keys("my_ro_authkey").ttl(5).future()
        # snippet.end

        result = good(envelope)
        a.eq(result.level, 'user')
        a.eq(result.ttl, 5)
        a.eq(list(result.channels), [channel])
        a.eq(list(result.channels[channel].auth_keys), ['my_ro_authkey'])
        key_data = result.channels[channel].auth_keys['my_ro_authkey']
        a.eq((key_data.read_enabled, key_data.write_enabled), (True, False))
        reader = holder(aclients, 'reader', 'my_ro_authkey')
        # The read grant is proved by a subscribe that connects. The missing write grant by a refused publish.
        await alisten(reader, channel)
        await aeventually(lambda: refused(reader, channel), timeout=300,
                          what='reader write refused, a channel level downgrade can take minutes')
        await aeventually(lambda: refused(holder(aclients, 'stranger', 'other_authkey'), channel), timeout=300,
                          what='a stranger auth key refused, a channel level downgrade can take minutes')
    finally:
        await close_grant(pubnub, [channel], auth_keys=['my_ro_authkey'])

    try:
        # snippet.grant_user_level
        envelope = await pubnub.grant().channels("my_channel"). \
            auth_keys("my_authkey"). \
            read(True).write(True). \
            ttl(5). \
            future()
        # snippet.end

        result = good(envelope)
        a.eq(result.level, 'user')
        a.eq(key_flags(result.channels[channel].auth_keys['my_authkey'])[:2], (True, True))
        await aeventually(lambda: allowed(holder(aclients, 'writer', 'my_authkey'), channel), timeout=30,
                          what='publish with the granted auth key')
        await aeventually(lambda: refused(holder(aclients, 'writer', 'my_authkey'), other), timeout=300,
                          what='a channel without a grant refused, a channel level downgrade can take minutes')
    finally:
        await close_grant(pubnub, [channel], auth_keys=['my_authkey'])


@step('grant_presence', role='pam')
async def test_grant_presence_channel(aclients):
    pubnub = aclients.asyncio('pam', 'admin')
    presence = names.with_suffix('my_channel-pnpres')
    try:
        # snippet.grant_presence
        envelope = await pubnub.grant(). \
            channels("my_channel-pnpres").read(True).write(True).future()
        # snippet.end

        result = good(envelope)
        a.eq(result.level, 'channel')
        a.eq(list(result.channels), [presence])
        a.eq((result.channels[presence].read_enabled, result.channels[presence].write_enabled), (True, True))
        client = holder(aclients, 'presence_reader')

        async def here_now_not_refused():
            resolved = await client.here_now().channels(presence).future()
            a.ok(not isinstance(resolved, PubNubAsyncioException), 'here_now on the presence channel was refused')

        await aeventually(here_now_not_refused, timeout=30, what='here_now on the presence channel')
    finally:
        await close_grant(pubnub, [presence])


@step('grant_channel_group', role='pam')
async def test_grant_channel_group(aclients):
    pubnub = aclients.asyncio('pam', 'admin')
    groups = [names.with_suffix(name) for name in ('cg1', 'cg2', 'cg3')]
    member = names.with_suffix('group_member')
    try:
        # snippet.grant_channel_group
        envelope = await pubnub.grant(). \
            channel_groups(["cg1", "cg2", "cg3"]). \
            auth_keys(["auth1", "auth2", "auth3"]). \
            read(True).write(True).manage(True). \
            ttl(12237). \
            future()
        # snippet.end

        result = good(envelope)
        a.eq(result.level, 'channel-group+auth')
        a.eq(result.ttl, 12237)
        a.eq(sorted(result.groups), sorted(groups))
        for data in result.groups.values():
            a.eq(sorted(data.auth_keys), ['auth1', 'auth2', 'auth3'])
            for key_data in data.auth_keys.values():
                a.eq(key_flags(key_data)[:3], (True, True, True))
        manager = holder(aclients, 'group_manager', 'auth1')

        async def add_member():
            resolved = await manager.add_channel_to_channel_group().channels(member).channel_group(groups[0]).future()
            a.ok(not isinstance(resolved, PubNubAsyncioException), 'the manage grant lets the auth key edit the group')

        await aeventually(add_member, timeout=30, what='the manage grant lets the auth key edit the group')
        listed = good(await pubnub.list_channels_in_channel_group().channel_group(groups[0]).future())
        a.eq(list(listed.channels), [member])
        resolved = await holder(aclients, 'stranger', 'auth9').add_channel_to_channel_group() \
            .channels(member).channel_group(groups[1]).future()
        a.ok(isinstance(resolved, PubNubAsyncioException), 'an auth key without a grant is refused')
        a.eq(resolved.status.status_code, 403)
    finally:
        try:
            await pubnub.remove_channel_group().channel_group(groups[0]).future()
        finally:
            await close_grant(pubnub, groups=groups, auth_keys=['auth1', 'auth2', 'auth3'])


@step('grant_multiple_channels', role='pam')
async def test_grant_multiple_channels(aclients):
    pubnub = aclients.asyncio('pam', 'admin')
    channels = [names.with_suffix('girish'), names.with_suffix('girish2')]
    try:
        # snippet.grant_multiple_channels
        envelope = await pubnub.grant().\
            auth_keys("my_rw_authkey").\
            channels(["girish", "girish2"]).\
            read(True).\
            write(True).\
            ttl(5).\
            future()
        # snippet.end

        result = good(envelope)
        a.eq(result.level, 'user')
        a.eq(result.ttl, 5)
        a.eq(sorted(result.channels), sorted(channels))
        for data in result.channels.values():
            a.eq(list(data.auth_keys), ['my_rw_authkey'])
            a.eq(key_flags(data.auth_keys['my_rw_authkey'])[:2], (True, True))
        client = holder(aclients, 'rw', 'my_rw_authkey')
        for channel in channels:
            await aeventually(lambda: allowed(client, channel), timeout=30, what='publish on a granted channel')
    finally:
        await close_grant(pubnub, channels, auth_keys=['my_rw_authkey'])


@step('grant_categories', role='pam')
async def test_grant_categories(aclients):
    pubnub = aclients.asyncio('pam', 'admin')
    auth_key = 'my_auth_key'
    try:
        # snippet.grant_categories
        envelope = await pubnub.grant() \
            .auth_keys(auth_key) \
            .categories(['channels', 'uuids']) \
            .get(True) \
            .ttl(15) \
            .future()
        print(f"Granted category permissions, level: {envelope.result.level}")
        # snippet.end

        result = good(envelope)
        a.eq(result.level, 'category')
        a.eq(result.ttl, 15)
        a.eq(sorted(result.categories), ['channels', 'uuids'])
        for name, data in result.categories.items():
            a.eq(data.name, name)
            a.eq(list(data.auth_keys), [auth_key])
            a.eq(data.auth_keys[auth_key].get, True)
            a.eq(data.auth_keys[auth_key].read_enabled, False)
        closed = good(await pubnub.grant().auth_keys(auth_key).categories(['channels']).get(False).future())
        a.eq(closed.categories['channels'].auth_keys[auth_key].get, False)
    finally:
        await pubnub.grant().auth_keys(auth_key).categories(['channels', 'uuids']).get(False).future()

    # The SDK refuses these before it sends the request.
    a.contains(failure(await pubnub.grant().auth_keys(auth_key).categories(['groups']).get(True).ttl(15).future()),
               "Unsupported categories: groups. Only 'channels' and 'uuids' are supported")
    a.contains(failure(await pubnub.grant().categories(['channels']).get(True).ttl(15).future()),
               'Category grants require providing non empty authKeys')
    a.contains(failure(await pubnub.grant().auth_keys(auth_key).categories(['channels']).read(True).get(True)
                       .ttl(15).future()),
               "Category grants allow only the 'get' permission")
    a.contains(failure(await pubnub.grant().auth_keys(auth_key).categories(['channels']).get(True).ttl(1).future()),
               'One-minute (ttl=1) category grants are not supported')
