"""Docs page: access-manager-v2 (sync), the application level grant. Kept in its own module so it runs last.

An application level grant opens every channel. A downgrade is not guaranteed to apply at once, so this module
asserts only what the docs claim: the grant call succeeds and the service accepts it. The grant is closed in a finally
(all flags false, ttl 1) and the janitor revokes it again at the end of every pam run.
"""
from harness import assertions as a
from harness.step import step

FLAGS = ('read', 'write', 'manage', 'delete', 'get', 'update', 'join')


def close_application_level(admin):
    builder = admin.grant()
    for flag in FLAGS:
        builder = getattr(builder, flag)(False)
    return builder.ttl(1).sync()


@step('grant_subkey_all', 'grant_application_level', role='pam', timeout=300)
def test_grant_application_level(clients):
    pubnub = clients.sync('pam', 'admin')
    try:
        # snippet.grant_subkey_all
        envelope = pubnub.grant().read(True).write(True).sync()
        # snippet.end

        a.eq(envelope.result.level, 'subkey')
        a.eq(envelope.result.ttl, 1440)
        a.eq((envelope.result.read_enabled, envelope.result.write_enabled), (True, True))
    finally:
        closed = close_application_level(pubnub)

    try:
        # snippet.grant_application_level
        envelope = pubnub.grant(). \
            read(True).write(True). \
            sync()
        # snippet.end

        a.eq(envelope.result.level, 'subkey')
        a.eq((envelope.result.read_enabled, envelope.result.write_enabled), (True, True))
    finally:
        closed = close_application_level(pubnub)
    a.eq(closed.result.level, 'subkey')
    a.eq((closed.result.read_enabled, closed.result.write_enabled), (False, False))
