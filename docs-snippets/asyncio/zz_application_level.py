"""Docs page: access-manager-v2 (asyncio), the application level grant. Kept in its own module so it runs last.

Same as sync/zz_application_level.py. A downgrade is not asserted to apply at once. future() resolves with an
exception object on failure, so the result type is asserted instead of a try/except.
"""
from pubnub.exceptions import PubNubAsyncioException

from harness import assertions as a
from harness.step import step

FLAGS = ('read', 'write', 'manage', 'delete', 'get', 'update', 'join')


async def close_application_level(admin):
    builder = admin.grant()
    for flag in FLAGS:
        builder = getattr(builder, flag)(False)
    return await builder.ttl(1).future()


def accepted(resolved):
    a.ok(not isinstance(resolved, PubNubAsyncioException), 'the grant was accepted')
    return resolved.result


@step('grant_subkey_all', 'grant_application_level', role='pam', timeout=300)
async def test_grant_application_level(aclients):
    pubnub = aclients.asyncio('pam', 'admin')
    try:
        # snippet.grant_subkey_all
        envelope = await pubnub.grant().read(True).write(True).future()
        # snippet.end

        result = accepted(envelope)
        a.eq(result.level, 'subkey')
        a.eq(result.ttl, 1440)
        a.eq((result.read_enabled, result.write_enabled), (True, True))
    finally:
        closed = await close_application_level(pubnub)

    try:
        # snippet.grant_application_level
        envelope = await pubnub.grant(). \
            read(True).write(True). \
            future()
        # snippet.end

        result = accepted(envelope)
        a.eq(result.level, 'subkey')
        a.eq((result.read_enabled, result.write_enabled), (True, True))
    finally:
        closed = await close_application_level(pubnub)
    result = accepted(closed)
    a.eq(result.level, 'subkey')
    a.eq((result.read_enabled, result.write_enabled), (False, False))
