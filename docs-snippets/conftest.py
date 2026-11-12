"""pytest wiring for the docs snippet suite: recorder, key loader, client fixtures, no-skip policy, reporter."""
import os
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))  # for "harness"; there is no __init__.py in sync or asyncio

from harness import env, recorder, world  # noqa: E402

recorder.install()
env.load()

pytest_plugins = ['harness.reporter']


def pytest_addoption(parser):
    parser.addoption('--shard', action='store', default='all', help='open, pam or all. Refused: -k in CI')


def pytest_collection_modifyitems(config, items):
    if os.environ.get('CI') and (config.getoption('-k') or config.getoption('-m') and not config.getoption('--shard')):
        raise pytest.UsageError('subset selection (-k) is refused in CI, every run must run all valid tests')
    for item in items:
        for mark in item.iter_markers():
            if mark.name in ('skip', 'skipif', 'xfail'):
                raise pytest.UsageError(f'{item.nodeid}: skip, skipif and xfail are not allowed in this suite')
    shard = config.getoption('--shard')
    if shard != 'all':
        items[:] = [i for i in items if i.get_closest_marker(shard)]
    live = [i for i in items if i.get_closest_marker('open') or i.get_closest_marker('pam')]
    roles = {m for i in live for m in ('open', 'pam') if i.get_closest_marker(m)}
    if config.option.collectonly:
        return
    live = [i for i in items if i.get_closest_marker('open') or i.get_closest_marker('pam')]
    if live and os.environ.get('DOCS_SNIPPETS_STAGED') != '1':
        raise pytest.UsageError('run the suite through "python -m harness.cli run" so that it is staged')
    gone = [n for r in sorted(roles) for n in env.missing(r)]
    if live and gone:
        raise pytest.UsageError('missing env: ' + ', '.join(gone))


@pytest.fixture
def clients():
    c = world.Clients()
    yield c
    c.close_sync()


@pytest.fixture
async def aclients():
    c = world.Clients()
    yield c
    await c.close_asyncio()


@pytest.fixture(scope='session', autouse=True)
def _no_lingering_threads():
    yield
    left = world.lingering_threads()
    assert not left, 'non-daemon threads still alive after the run: ' + ', '.join(left)


@pytest.fixture(autouse=True)
def _remove_channel_groups_after_each_step():
    """Channel groups a step recorded in the ledger are removed right after that step, so a failing step cannot leave
    members behind for the next step. The end-of-run janitor still covers anything this misses."""
    import json
    path = world.ledger_path()
    before = len(path.read_text().splitlines()) if path.exists() else 0
    yield
    if not path.exists():
        return
    created = [json.loads(line) for line in path.read_text().splitlines()[before:]]
    groups = [c['name'] for c in created if c['kind'] == 'channel_group']
    if not groups:
        return
    client = world.Clients()
    try:
        pubnub = client.sync('open', 'group-cleanup')
        for group in groups:
            try:
                pubnub.remove_channel_group().channel_group(group).sync()
            except Exception:  # the step may already have removed it
                pass
    finally:
        client.close_sync()


@pytest.fixture(autouse=True)
def _own_names_per_step(request):
    """Every step gets its own channel, group and user names (see names.test_tag)."""
    from harness import names
    rel = Path(request.node.fspath).resolve().relative_to(Path(__file__).resolve().parent).as_posix()
    names.set_tag(names.test_tag(rel, request.node.originalname or request.node.name))
    yield
    names.set_tag('')
