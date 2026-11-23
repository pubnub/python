"""Scenario data and helpers of the access-manager-v2 page, shared by the sync and asyncio tests: literal resource names
(NAMES, read by the janitor through support/resources.py) and the helpers the tests call outside the snippet markers.
Coroutine twins of a sync helper carry an "_async" suffix, and the asyncio tests import them under the sync name.
"""
from pubnub.exceptions import PubNubException
from pubnub.exceptions import PubNubAsyncioException

from support import assertions as a

NAMES = ['cg2', 'cg3', 'ch_no_grant', 'girish', 'girish2', 'group_member', 'my_channel-pnpres']


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


FLAGS = ('read', 'write', 'manage', 'delete', 'get', 'update', 'join')


def close_application_level(admin):
    builder = admin.grant()
    for flag in FLAGS:
        builder = getattr(builder, flag)(False)
    return builder.ttl(1).sync()


def holder_async(aclients, user_id, auth_key=None):
    """A client that has no secret key, so every request is checked against its auth key."""
    client = aclients.asyncio('pam', user_id, secret=False)
    client.config.auth_key = auth_key
    return client


async def close_grant_async(admin, channels=None, groups=None, uuids=None, auth_keys=None):
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


async def publish_async(client, channel):
    return await client.publish().channel(channel).message('docs').future()


async def refused_async(client, channel):
    resolved = await publish_async(client, channel)
    a.ok(isinstance(resolved, PubNubAsyncioException), 'the publish was refused')
    a.eq(resolved.status.status_code, 403, 'status code of the refusal')


async def allowed_async(client, channel):
    resolved = await publish_async(client, channel)
    a.ok(not isinstance(resolved, PubNubAsyncioException), 'the publish went through')
    a.timetoken(resolved.result.timetoken)


def good(resolved):
    """A future() that resolved with a result, not with an error object. Returns the result."""
    a.ok(not isinstance(resolved, PubNubAsyncioException), 'the call succeeded')
    return resolved.result


def failure(resolved):
    a.ok(isinstance(resolved, PubNubAsyncioException), 'the call resolved with an error object')
    return str(resolved.value())


async def close_application_level_async(admin):
    builder = admin.grant()
    for flag in FLAGS:
        builder = getattr(builder, flag)(False)
    return await builder.ttl(1).future()


def accepted(resolved):
    a.ok(not isinstance(resolved, PubNubAsyncioException), 'the grant was accepted')
    return resolved.result
