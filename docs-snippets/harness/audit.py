"""Static assertion audit and coverage report: python -m harness.audit [--write]

Checks that every live step asserts after its snippet (the runtime honesty check enforces the same, this finds it
without a run), and lists coverage per docset and page. Joins the latest live results from report/<shard>/run.json.
"""
import ast
import json
import re
import sys
from collections import Counter

from . import manifest, registry

ASSERT_NAMES = {'ok', 'eq', 'contains', 'not_contains', 'timetoken', 'raises'}
WAIT_NAMES = {'eventually', 'aeventually'}


def _assertion_calls(node, helpers):
    count = 0
    for n in ast.walk(node):
        if isinstance(n, ast.Assert):
            count += 1
        elif isinstance(n, ast.Call):
            f = n.func
            is_a_call = isinstance(f, ast.Attribute) and isinstance(f.value, ast.Name) and f.value.id == 'a'
            if is_a_call and f.attr in ASSERT_NAMES:
                count += 1
            elif isinstance(f, ast.Name) and (f.id in ASSERT_NAMES or f.id in WAIT_NAMES):
                count += 1
            elif isinstance(f, ast.Name) and f.id in helpers:
                count += helpers[f.id]
    return count


def _module_helpers(tree):
    """Assertion count of module-level helpers, resolved one level, so a step that asserts through one counts."""
    plain = {}
    for n in tree.body:
        if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)) and not n.name.startswith('test_'):
            plain[n.name] = _assertion_calls(n, {})
    return plain


def audit():
    rows, bad = [], []
    for e in registry.scan():
        if e.mode != 'live':
            rows.append((e, None))
            continue
        path = registry.ROOT / e.file
        text = path.read_text()
        tree = ast.parse(text)
        helpers = _module_helpers(tree)
        funcs = (ast.FunctionDef, ast.AsyncFunctionDef)
        fn = next(n for n in ast.walk(tree) if isinstance(n, funcs) and n.name == e.func)
        inside = [(i, line) for i, line in enumerate(text.splitlines(), 1) if fn.lineno < i <= fn.end_lineno]
        ends = [i for i, line in inside if re.match(r'\s*# snippet\.end\s*$', line)]
        marker = re.compile(r'\s*# snippet\.([A-Za-z0-9_-]+)\s*$')
        starts = [i for i, line in inside
                  if marker.match(line) and marker.match(line).group(1) not in ('end', 'hide', 'show')]
        first_start = min(starts)
        local = dict(helpers)
        for n in ast.walk(fn):  # helpers defined inside the step count when the step calls them
            if n is not fn and isinstance(n, funcs):
                local[n.name] = _assertion_calls(n, helpers)
        stmts = [n for n in fn.body if getattr(n, 'end_lineno', 0) > first_start and not isinstance(n, funcs)]
        count = sum(_assertion_calls(n, local) for n in stmts)
        rows.append((e, count))
        if count == 0 or not ends:
            bad.append(e)
    return rows, bad


def latest_results():
    out = {}
    for shard in ('open', 'pam'):
        p = registry.ROOT / 'report' / shard / 'run.json'
        if p.exists():
            d = json.loads(p.read_text())
            for t in d['tests']:
                out[t['test']] = t['outcome']
            for k, v in d.get('steps', {}).items():
                out.setdefault('_steps', {})[k] = v
    return out


def report():
    rows, bad = audit()
    results = latest_results()
    steps = results.get('_steps', {})
    lines = ['# Coverage and assertion audit', '']
    modes = Counter((e.docset, e.mode) for e, _ in rows)
    ids = Counter()
    for e, _ in rows:
        ids[(e.docset, e.mode)] += len(e.ids)
    lines += ['## Snippet ids by docset and mode', '',
              '| docset | live steps | live ids | compile-only ids | stub ids |', '| :-- | --: | --: | --: | --: |']
    for ds in registry.DOCSETS:
        cells = [modes[(ds, 'live')], ids[(ds, 'live')], ids[(ds, 'compile-only')], ids[(ds, 'stub')]]
        lines.append(f'| {ds} | ' + ' | '.join(str(c) for c in cells) + ' |')
    lines += ['', f'Steps with no assertion after the snippet, or a snippet without an end marker: **{len(bad)}**', '']
    for e in bad:
        lines.append(f'* {e.file}::{e.func}')
    lines += ['', '## Per step', '',
              '| step | role | snippet ids | assertion calls (static) | assertions (last run) | last result |',
              '| :-- | :-- | :-- | --: | --: | :-- |']
    for e, count in sorted(rows, key=lambda r: (r[0].docset, r[0].file, r[0].first)):
        node = f'{e.file}::{e.func}'
        if e.mode != 'live':
            lines.append(f"| {node} | {e.role} | {', '.join(e.ids)} | n/a | n/a | {e.mode} ({e.reason}) |")
            continue
        runtime = steps.get(node, {}).get('assertions', 'n/a')
        outcome = results.get(node, 'not run')
        lines.append(f"| {node} | {e.role} | {', '.join(e.ids)} | {count} | {runtime} | {outcome} |")
    docs = manifest.docs_ids()
    known = {d: set(v) for d, v in manifest.build().items()}
    lines += ['', '## Docs pages versus the manifest', '']
    for ds, found in docs.items():
        missing = len(found - known.get(ds, set()))
        lines.append(f'* {ds}: {len(found)} snippet ids referenced by docs pages, {missing} missing from the manifest')
    return '\n'.join(lines) + '\n', bad


def main(argv):
    text, bad = report()
    if '--write' in argv:
        (registry.ROOT / 'report').mkdir(exist_ok=True)
        (registry.ROOT / 'report' / 'coverage.md').write_text(text)
        print('wrote report/coverage.md')
    else:
        print(text)
    return 1 if bad else 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
