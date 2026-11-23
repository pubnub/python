"""Group logic over the data in tests/live/groups.py.

    python -u tests/live/cli.py groups --check           consistency check (also run by cli.py lint)
    python -u tests/live/cli.py groups --matrix [name]   the CI job matrix, as JSON ("all" or empty: every group)

LIVE_GROUP=<name> selects a group for a pytest run (support/hooks.py).
"""
import importlib.util
import json
import re

from . import LIVE_DIR, REPO_ROOT

WORKFLOW = REPO_ROOT / '.github' / 'workflows' / 'live-integration.yml'
TIERS = ('docs',)


def load():
    spec = importlib.util.spec_from_file_location('live_groups_data', LIVE_DIR / 'groups.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.GROUPS


def names():
    return [g['name'] for g in load()]


def by_name(name):
    for g in load():
        if g['name'] == name:
            return g
    raise KeyError(f'unknown group {name!r}, known: {", ".join(names())}')


def _split(group):
    files = {e for e in group['files'] if '::' not in e}
    nodes = {e for e in group['files'] if '::' in e}
    return files, nodes


def claimed_nodes(groups=None):
    """Node ids that some group lists explicitly."""
    out = {}
    for g in groups or load():
        for node in _split(g)[1]:
            out[node] = g['name']
    return out


def group_of(file_rel, test_name, groups=None):
    """Name of the group that runs one test (file relative to tests/live)."""
    groups = groups or load()
    node = f'{file_rel}::{test_name}'
    claimed = claimed_nodes(groups)
    if node in claimed:
        return claimed[node]
    for g in groups:
        if file_rel in _split(g)[0]:
            return g['name']
    return None


def _workflow_options():
    if not WORKFLOW.exists():
        return None
    text = WORKFLOW.read_text()
    m = re.search(r'\n      group:\n(?:.*\n)*?\s+options:\n((?:\s+- .*\n)+)', text)
    if not m:
        return []
    return [line.strip()[2:].strip().strip("'\"") for line in m.group(1).splitlines()]


def check():
    from . import snippet_scan
    problems = []
    groups = load()
    seen = {}
    for g in groups:
        if g.get('tier') not in TIERS:
            problems.append(f'group {g["name"]}: tier must be one of {TIERS}')
        if g['name'] in seen:
            problems.append(f'group {g["name"]} is listed twice')
        seen[g['name']] = g
    files, snippets = snippet_scan.scan_tier()
    tests = {f.live_rel: f for f in files if f.kind == 'test'}
    whole = {}
    for g in groups:
        listed, nodes = _split(g)
        for rel in listed:
            if rel not in tests:
                problems.append(f'group {g["name"]}: {rel} does not exist (or is not a test_*.py file)')
            if rel in whole:
                problems.append(f'{rel} is in two groups: {whole[rel]} and {g["name"]}')
            whole[rel] = g['name']
        for node in nodes:
            rel, _, name = node.partition('::')
            if rel not in tests or name not in tests[rel].funcs or not tests[rel].funcs[name].is_test:
                problems.append(f'group {g["name"]}: {node} does not name a test')
    for rel in sorted(set(tests) - set(whole)):
        problems.append(f'{rel} is in no group (add it to tests/live/groups.py)')
    for rel, f in tests.items():
        for func in f.funcs.values():
            if not func.is_test:
                continue
            name = group_of(rel, func.name, groups)
            if name is None:
                continue
            roles = set(snippet_scan.roles_of(f, func))
            extra = roles - set(seen[name]['roles'])
            if extra:
                problems.append(f'{rel}::{func.name} uses role {", ".join(sorted(extra))}, its group {name} does '
                                'not list it')
    options = _workflow_options()
    wanted = ['all'] + [g['name'] for g in groups]
    if options is None:
        problems.append(f'{WORKFLOW.relative_to(REPO_ROOT)} is missing')
    elif options != wanted:
        problems.append(f'workflow dispatch input "group" options {options} differ from {wanted}')
    return problems


def matrix(selection='all'):
    groups = load()
    if selection and selection != 'all':
        groups = [by_name(selection)]
    return json.dumps({'include': [{'group': g['name'], 'tier': g['tier']} for g in groups]}, separators=(',', ':'))


def main(argv):
    if '--matrix' in argv:
        i = argv.index('--matrix')
        print(matrix(argv[i + 1] if len(argv) > i + 1 else 'all'))
        return 0
    problems = check()
    for p in problems:
        print('groups:', p)
    print(f'groups: {len(load())} groups, {len(problems)} problems')
    return 1 if problems else 0
