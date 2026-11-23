"""Shared scenario data of the access-manager page for both docsets: literal resource names (NAMES,
read by the janitor through support/resources.py) and the helpers the sync and asyncio tests call outside
the snippet markers. Moved from the old docs-snippets/<docset>/ modules. Coroutine twins of a sync helper
carry an "_async" suffix, and the asyncio tests import them under the sync name.
"""
from pubnub.exceptions import PubNubException
from pubnub.exceptions import PubNubAsyncioException

from support import assertions as a

NAMES = ['my-authorized-uuid', 'readonly-channel', 'readwrite-channel', 'revoke-channel', 'set_token_other_channel']


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


def holder_async(aclients, user_id, token=None):
    """A client that holds a token. It has no secret key, so every request is checked against the token."""
    client = aclients.asyncio('pam', user_id, secret=False)
    if token:
        client.set_token(token)
    return client


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


def failure(resolved):
    """The error text of a future() that resolved with an error."""
    a.ok(isinstance(resolved, PubNubAsyncioException), 'the call resolved with an error object')
    return str(resolved.value())
