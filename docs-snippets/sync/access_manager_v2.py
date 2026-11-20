"""Docs page: access-manager-v2 (sync), the legacy grant().

Needs the pam keyset. Every grant is closed in a finally (all flags false, ttl 1). The step that grants at application
level is the last one of this file, because a downgrade is not guaranteed to apply at once and would otherwise leak
into the 403 checks of later steps. Tokens and keys never reach output.
"""
from pubnub.exceptions import PubNubException

from harness import assertions as a
from harness import names
from harness.listeners import listen
from harness.step import step
from harness.wait import eventually

REGISTERED_NAMES = ['my_channel-pnpres', 'girish', 'girish2', 'cg2', 'cg3']

ALL_FALSE = ('read', 'write', 'manage', 'delete', 'get', 'update', 'join')


def holder(clients, user_id, auth_key=None):
    """A client that has no secret key, so every request is checked against its auth key."""
    client = clients.sync('pam', user_id, secret=False)
    client.config.auth_key = auth_key
    return client


def close_grant(admin, channels=None, groups=None, uuids=None, auth_keys=None):
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
    return builder.ttl(1).sync()


def publish(client, channel):
    return client.publish().channel(channel).message('docs').sync()


def refused(client, channel):
    error = a.raises(PubNubException, publish, client, channel)
    a.eq(error.get_status_code(), 403, 'status code of the refusal')


def allowed(client, channel):
    a.timetoken(publish(client, channel).result.timetoken)


def key_flags(key_data):
    return (key_data.read_enabled, key_data.write_enabled, key_data.manage_enabled, key_data.delete_enabled)


@step('grant_channel_auth', role='pam')
def test_grant_channel_and_auth_key(clients):
    pubnub = clients.sync('pam', 'admin')
    channels = [names.with_suffix(name) for name in ('ch1', 'ch2', 'ch3')]
    groups = [names.with_suffix(name) for name in ('cg1', 'cg2')]
    other = names.with_suffix('ch_no_grant')
    try:
        # snippet.grant_channel_auth
        envelope = pubnub.grant().channels(["ch1", "ch2", "ch3"]).\
            channel_groups(["cg1", "cg2"]).\
            auth_keys(["key1", "key2"]).\
            read(True).write(True).manage(True).delete(True).\
            ttl(12337).\
            sync()
        # snippet.end

        result = envelope.result
        a.eq(result.level, 'channel-group+auth')
        a.eq(result.ttl, 12337)
        a.ok(isinstance(result.subscribe_key, str) and result.subscribe_key, 'the result names the subscribe key')
        a.eq(sorted(result.channels), sorted(channels))
        a.eq(sorted(result.groups), sorted(groups))
        for data in list(result.channels.values()) + list(result.groups.values()):
            a.eq(sorted(data.auth_keys), ['key1', 'key2'])
            for key_data in data.auth_keys.values():
                a.eq(key_flags(key_data), (True, True, True, True))
        eventually(lambda: allowed(holder(clients, 'granted', 'key1'), channels[0]), timeout=30,
                   what='a granted auth key publishes')
        refused(holder(clients, 'stranger', 'key3'), channels[0])
        refused(holder(clients, 'granted', 'key1'), other)
    finally:
        close_grant(pubnub, channels, groups, auth_keys=['key1', 'key2'])


@step('grant_channel_all_users', 'grant_channel_level', role='pam')
def test_grant_channel_level(clients):
    pubnub = clients.sync('pam', 'admin')
    channel = names.with_suffix('my_channel')
    other = names.with_suffix('ch_no_grant')
    try:
        # snippet.grant_channel_all_users
        envelope = pubnub.grant().channels("my_channel").read(True).write(True).sync()
        # snippet.end

        a.eq(envelope.result.level, 'channel')
        a.eq(envelope.result.ttl, 1440)
        a.eq(envelope.result.channels[channel].read_enabled, True)
        a.eq(envelope.result.channels[channel].write_enabled, True)
        client = holder(clients, 'anyone')
        eventually(lambda: allowed(client, channel), timeout=30, what='publish without an auth key')
        refused(client, other)

        # snippet.grant_channel_level
        envelope = pubnub.grant().channels("my_channel").\
            read(True).write(True).\
            sync()
        # snippet.end

        a.eq(envelope.result.level, 'channel')
        a.eq(envelope.result.channels[channel].read_enabled, True)
    finally:
        close_grant(pubnub, [channel])


@step('grant_channel_ro_auth', 'grant_user_level', role='pam', timeout=900)
def test_grant_user_level(clients):
    pubnub = clients.sync('pam', 'admin')
    channel = names.with_suffix('my_channel')
    other = names.with_suffix('ch_no_grant')
    try:
        # snippet.grant_channel_ro_auth
        envelope = pubnub.grant().channels("my_channel").read(True).write(False).\
            auth_keys("my_ro_authkey").ttl(5).sync()
        # snippet.end

        result = envelope.result
        a.eq(result.level, 'user')
        a.eq(result.ttl, 5)
        a.eq(list(result.channels), [channel])
        a.eq(list(result.channels[channel].auth_keys), ['my_ro_authkey'])
        key_data = result.channels[channel].auth_keys['my_ro_authkey']
        a.eq((key_data.read_enabled, key_data.write_enabled), (True, False))
        reader = holder(clients, 'reader', 'my_ro_authkey')
        # The read grant is proved by a subscribe that connects. The missing write grant by a refused publish.
        listen(reader, channel)
        eventually(lambda: refused(reader, channel), timeout=300,
                   what='reader write refused, a channel level downgrade can take minutes')
        eventually(lambda: refused(holder(clients, 'stranger', 'other_authkey'), channel), timeout=300,
                   what='a stranger auth key refused, a channel level downgrade can take minutes')
    finally:
        close_grant(pubnub, [channel], auth_keys=['my_ro_authkey'])

    try:
        # snippet.grant_user_level
        envelope = pubnub.grant().channels("my_channel"). \
            auth_keys("my_authkey"). \
            read(True).write(True). \
            ttl(5). \
            sync()
        # snippet.end

        a.eq(envelope.result.level, 'user')
        a.eq(key_flags(envelope.result.channels[channel].auth_keys['my_authkey'])[:2], (True, True))
        eventually(lambda: allowed(holder(clients, 'writer', 'my_authkey'), channel), timeout=30,
                   what='publish with the granted auth key')
        eventually(lambda: refused(holder(clients, 'writer', 'my_authkey'), other), timeout=300,
                   what='a channel without a grant refused, a channel level downgrade can take minutes')
    finally:
        close_grant(pubnub, [channel], auth_keys=['my_authkey'])


@step('grant_presence', role='pam')
def test_grant_presence_channel(clients):
    pubnub = clients.sync('pam', 'admin')
    presence = names.with_suffix('my_channel-pnpres')
    try:
        # snippet.grant_presence
        envelope = pubnub.grant(). \
            channels("my_channel-pnpres").read(True).write(True).sync()
        # snippet.end

        a.eq(envelope.result.level, 'channel')
        a.eq(list(envelope.result.channels), [presence])
        a.eq(envelope.result.channels[presence].read_enabled, True)
        a.eq(envelope.result.channels[presence].write_enabled, True)
        client = holder(clients, 'presence_reader')
        eventually(lambda: a.eq(client.here_now().channels(presence).sync().status.is_error(), False), timeout=30,
                   what='a here_now on the presence channel is not refused')
    finally:
        close_grant(pubnub, [presence])


@step('grant_channel_group', role='pam')
def test_grant_channel_group(clients):
    pubnub = clients.sync('pam', 'admin')
    groups = [names.with_suffix(name) for name in ('cg1', 'cg2', 'cg3')]
    member = names.with_suffix('group_member')
    try:
        # snippet.grant_channel_group
        envelope = pubnub.grant(). \
            channel_groups(["cg1", "cg2", "cg3"]). \
            auth_keys(["auth1", "auth2", "auth3"]). \
            read(True).write(True).manage(True). \
            ttl(12237). \
            sync()
        # snippet.end

        result = envelope.result
        a.eq(result.level, 'channel-group+auth')
        a.eq(result.ttl, 12237)
        a.eq(sorted(result.groups), sorted(groups))
        for data in result.groups.values():
            a.eq(sorted(data.auth_keys), ['auth1', 'auth2', 'auth3'])
            for key_data in data.auth_keys.values():
                a.eq(key_flags(key_data)[:3], (True, True, True))
        manager = holder(clients, 'group_manager', 'auth1')
        eventually(lambda: manager.add_channel_to_channel_group().channels(member).channel_group(groups[0]).sync(),
                   timeout=30, what='the manage grant lets the auth key edit the group')
        listed = pubnub.list_channels_in_channel_group().channel_group(groups[0]).sync().result.channels
        a.eq(list(listed), [member])
        error = a.raises(PubNubException, holder(clients, 'stranger', 'auth9').add_channel_to_channel_group()
                         .channels(member).channel_group(groups[1]).sync)
        a.eq(error.get_status_code(), 403)
    finally:
        try:
            pubnub.remove_channel_group().channel_group(groups[0]).sync()
        finally:
            close_grant(pubnub, groups=groups, auth_keys=['auth1', 'auth2', 'auth3'])


@step('grant_multiple_channels', role='pam')
def test_grant_multiple_channels(clients):
    pubnub = clients.sync('pam', 'admin')
    channels = [names.with_suffix('girish'), names.with_suffix('girish2')]
    try:
        # snippet.grant_multiple_channels
        envelope = pubnub.grant().\
            auth_keys("my_rw_authkey").\
            channels(["girish", "girish2"]).\
            read(True).\
            write(True).\
            ttl(5).\
            sync()
        # snippet.end

        a.eq(envelope.result.level, 'user')
        a.eq(envelope.result.ttl, 5)
        a.eq(sorted(envelope.result.channels), sorted(channels))
        for data in envelope.result.channels.values():
            a.eq(list(data.auth_keys), ['my_rw_authkey'])
            a.eq(key_flags(data.auth_keys['my_rw_authkey'])[:2], (True, True))
        client = holder(clients, 'rw', 'my_rw_authkey')
        for channel in channels:
            eventually(lambda: allowed(client, channel), timeout=30, what='publish on a granted channel')
    finally:
        close_grant(pubnub, channels, auth_keys=['my_rw_authkey'])


@step('grant_uuid', role='pam')
def test_grant_uuid(clients):
    pubnub = clients.sync('pam', 'admin')
    uuid = names.with_suffix('my_uuid')
    try:
        # snippet.grant_uuid
        envelope = pubnub.grant().uuids("my_uuid").get(True).update(True) \
            .auth_keys("my_ro_authkey").ttl(1440).sync()
        # snippet.end

        a.eq(envelope.result.level, 'uuid')
        a.eq(envelope.result.ttl, 1440)
        a.eq(list(envelope.result.uuids), [uuid])
        key_data = envelope.result.uuids[uuid].auth_keys['my_ro_authkey']
        a.eq((key_data.get, key_data.update), (True, True))
        a.eq((key_data.read_enabled, key_data.write_enabled), (False, False))
    finally:
        close_grant(pubnub, uuids=[uuid], auth_keys=['my_ro_authkey'])


@step('grant_categories', role='pam')
def test_grant_categories(clients):
    pubnub = clients.sync('pam', 'admin')
    auth_key = 'my_auth_key'
    try:
        # snippet.grant_categories
        envelope = pubnub.grant() \
            .auth_keys(auth_key) \
            .categories(['channels', 'uuids']) \
            .get(True) \
            .ttl(15) \
            .sync()
        print(f"Granted category permissions, level: {envelope.result.level}")
        # snippet.end

        result = envelope.result
        a.eq(result.level, 'category')
        a.eq(result.ttl, 15)
        a.eq(sorted(result.categories), ['channels', 'uuids'])
        for name, data in result.categories.items():
            a.eq(data.name, name)
            a.eq(list(data.auth_keys), [auth_key])
            a.eq(data.auth_keys[auth_key].get, True)
            a.eq(data.auth_keys[auth_key].read_enabled, False)
        parsed_back = pubnub.grant().auth_keys(auth_key).categories(['channels']).get(False).sync().result
        a.eq(parsed_back.categories['channels'].auth_keys[auth_key].get, False)
    finally:
        pubnub.grant().auth_keys(auth_key).categories(['channels', 'uuids']).get(False).sync()

    # The SDK refuses these before it sends the request.
    def invalid(builder):
        return a.raises(PubNubException, builder.sync)

    a.contains(str(invalid(pubnub.grant().auth_keys(auth_key).categories(['groups']).get(True).ttl(15))),
               "Unsupported categories: groups. Only 'channels' and 'uuids' are supported")
    a.contains(str(invalid(pubnub.grant().categories(['channels']).get(True).ttl(15))),
               'Category grants require providing non empty authKeys')
    a.contains(str(invalid(pubnub.grant().auth_keys(auth_key).categories(['channels']).read(True).get(True).ttl(15))),
               "Category grants allow only the 'get' permission")
    a.contains(str(invalid(pubnub.grant().auth_keys(auth_key).categories(['channels']).get(True).ttl(1))),
               'One-minute (ttl=1) category grants are not supported')
