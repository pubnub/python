"""pytest hooks and fixtures of the live tier (loaded by tests/live/conftest.py).

Before the first test: role check (a full run needs every keyset role, a group run the group's roles, a partial run
with -k, -m or file arguments the roles of its selected tests, from coverage.json), then the janitor (cleans every
name of resources.py on every role that has keys), then, when the run uses the pam role, a wait until a client
without a token is refused again, then the preflight (keyset features). A failed cleanup or preflight fails the run.

After each test: the registered cleanups (support/cleanup.py) run while the clients still live, then the clients stop.
After the run: the janitor again (failures are printed, a failed revoke of the application-level grant fails the run),
and the check that no non-daemon thread is left.

LIVE_GROUP=<name> runs one group (groups.py). LIVE_JANITOR=off and LIVE_PREFLIGHT=off skip those steps.
--collect-only never touches keys or the network.
"""
import json
import os
import sys

import pytest

from . import LIVE_DIR, cleanup, env, groups, janitor, preflight
from .clients import lingering_threads
from .clients_asyncio import AsyncioClients
from .clients_sync import SyncClients


def pytest_configure(config):
    env.load()
    if sys.flags.optimize > 0:
        raise pytest.UsageError('the live tier refuses python -O: it strips the assert statements')
    if config.pluginmanager.hasplugin('rerunfailures'):
        raise pytest.UsageError('the live tier refuses pytest-rerunfailures: retries hide real failures')
    config.addinivalue_line('markers', 'timeout(seconds): per-test timeout (pytest-timeout)')


def _rel(item):
    return item.path.resolve().relative_to(LIVE_DIR).as_posix()


def _is_full_run(config):
    selected = config.getoption('keyword') or config.getoption('markexpr') or os.environ.get('LIVE_GROUP')
    return config.args_source == pytest.Config.ArgsSource.TESTPATHS and not selected


def pytest_collection_modifyitems(session, config, items):
    for item in items:
        for mark in item.iter_markers():
            if mark.name in ('skip', 'skipif', 'xfail'):
                raise pytest.UsageError(f'{item.nodeid}: skip, skipif and xfail are not allowed in the live tier')
    name = os.environ.get('LIVE_GROUP', '').strip()
    if name:
        try:
            groups.by_name(name)
        except KeyError as error:
            raise pytest.UsageError(str(error))
        data = groups.load()
        keep = [i for i in items if groups.group_of(_rel(i), i.originalname or i.name, data) == name]
        deselected = [i for i in items if i not in keep]
        if deselected:
            config.hook.pytest_deselected(items=deselected)
        items[:] = keep
        if not items:
            raise pytest.UsageError(f'group {name} selects no test')


def _roles_of_items(items):
    manifest = LIVE_DIR / 'coverage.json'
    by_test = {}
    if manifest.exists():
        for entries in json.loads(manifest.read_text()).get('files', {}).values():
            for entry in entries.values():
                if entry.get('test') and entry.get('role'):
                    by_test[entry['test']] = entry['role'].split(',')
    roles = set()
    for item in items:
        roles.update(by_test.get(f'{_rel(item)}::{item.originalname or item.name}', ['open']))
    return roles


def _required_roles(config, items):
    name = os.environ.get('LIVE_GROUP', '').strip()
    if name:
        group_roles = set(groups.by_name(name)['roles'])
        if config.getoption('keyword') or config.args_source != pytest.Config.ArgsSource.TESTPATHS:
            return _roles_of_items(items) & group_roles or group_roles
        return group_roles
    if _is_full_run(config):
        return set(env.KEYSET_ROLES)
    return _roles_of_items(items)


def pytest_collection_finish(session):
    config = session.config
    if config.option.collectonly or not session.items:
        return
    roles = _required_roles(config, session.items)
    config._live_roles = sorted(roles)
    gone = [f'{role} ({", ".join(env.missing(role))})' for role in sorted(roles) if env.missing(role)]
    if gone:
        listed = '; '.join(gone)
        raise pytest.UsageError(f'the selected tests need keyset roles that are not set: {listed}. Set them in the '
                                'environment or in tests/live/.env.local (see .env.example).')


@pytest.fixture(scope='session', autouse=True)
def _live_session(request):
    roles = getattr(request.config, '_live_roles', list(env.KEYSET_ROLES))
    use_janitor = env.switch_on('LIVE_JANITOR')
    if use_janitor:
        report = janitor.run()
        lines = list(janitor.format_report(report))
        for line in lines:
            print(line)
        if report.failed or report.critical:
            pytest.exit('the cleanup before the run failed, the tests would start on a dirty keyset. '
                        'Run "python -u tests/live/cli.py janitor" to retry it alone.\n' + '\n'.join(lines),
                        returncode=1)
        if 'pam' in roles and env.has('pam'):
            print(f'janitor: a client without a token is refused on the pam keyset '
                  f'({janitor.verify_application_grant_closed()} s)')
    else:
        print('janitor: skipped before the run')
    if env.switch_on('LIVE_PREFLIGHT'):
        notes, problems = preflight.run(roles)
        for note in notes:
            print('preflight:', note)
        if problems:
            pytest.exit('keyset preflight failed:\n' + '\n'.join(f'  - {p}' for p in problems), returncode=1)
        print('preflight: keyset features ok')
    yield
    if use_janitor:
        report = janitor.run()
        for line in janitor.format_report(report):
            print(line)
        if report.critical:
            pytest.fail('cleanup after the run may have left the pam keyset open: ' + ' | '.join(report.critical))
    left = lingering_threads()
    assert not left, 'non-daemon threads still alive after the run: ' + ', '.join(left)


@pytest.fixture
def clients():
    c = SyncClients()
    yield c
    try:
        cleanup.run_cleanups()
    finally:
        c.close()


@pytest.fixture
async def aclients():
    c = AsyncioClients()
    yield c
    try:
        cleanup.run_cleanups()
    finally:
        await c.close()


@pytest.fixture(autouse=True)
def _cleanups_without_clients():
    """Tests that use no client fixture still get their registered cleanups."""
    yield
    cleanup.run_cleanups()
