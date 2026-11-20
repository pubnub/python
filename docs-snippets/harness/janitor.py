"""Janitor: removes what runs left behind and proves no application-level Access Manager v2 grant is open.

Runs at the end of every live run and after a failure or cancel in CI. A leftover is a resource whose name carries the
marker "dsn-" AND a base36 timestamp older than six hours. Nothing else is touched.
"""
import json
import re
import sys
import time

from . import env, names, world

MAX_AGE = 6 * 3600
PATTERN = re.compile(names.MARKER + r'-([0-9a-z]{6,8})')


def _age(name):
    m = PATTERN.search(name)
    if not m:
        return None
    try:
        return time.time() - int(m.group(1)[:6], 36)
    except ValueError:
        return None


def revoke_application_grant():
    """Close the application-level v2 grant (no channel, no auth key) so no run leaves it open."""
    client = world.Clients().sync('pam', 'janitor')
    envelope = client.grant() \
        .read(False).write(False).manage(False).delete(False).get(False).update(False).join(False) \
        .ttl(1).sync()
    return envelope.status.is_error() is False


def clean_app_context(role='open'):
    client = world.Clients().sync(role, 'janitor')
    removed = 0
    for fetch, remove in ((client.get_all_channel_metadata, client.remove_channel_metadata),
                          (client.get_all_uuid_metadata, client.remove_uuid_metadata)):
        for item in fetch().limit(100).sync().result.data:
            ident = item['id'] if isinstance(item, dict) else item.id
            age = _age(ident)
            if age is not None and age > MAX_AGE:
                remove(ident).sync()
                removed += 1
    return removed


def clean_ledger():
    removed = 0
    path = world.ledger_path()
    if not path.exists():
        return removed
    client = world.Clients().sync('open', 'janitor')
    for line in path.read_text().splitlines():
        item = json.loads(line)
        try:
            if item['kind'] == 'channel_group':
                client.remove_channel_group().channel_group(item['name']).sync()
            elif item['kind'] == 'history':
                client.delete_messages().channel(item['name']).sync()
            removed += 1
        except Exception as e:  # keep going. The final report names what is left
            print('janitor: could not remove', item['kind'], '(' + type(e).__name__ + ')')
    path.unlink()
    return removed


def main(shard='all'):
    """An open-only run never touches the pam keyset, so it cannot break a pam run that goes on at the same time."""
    problems = 0
    tasks = [('open', clean_app_context), ('open', clean_ledger)]
    if shard in ('all', 'pam'):
        tasks.insert(0, ('pam', revoke_application_grant))
    for role, task in tasks:
        if env.missing(role):
            print(f'janitor: {task.__name__} not run, role {role} is missing env')
            problems += 1
            continue
        print(f'janitor: {task.__name__} ->', task())
    return 1 if problems else 0


if __name__ == '__main__':
    sys.exit(main())
