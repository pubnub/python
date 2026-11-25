"""Docs cross-check: does every snippet the docs embed from pubnub/python map to a test that runs it?

    python -u tests/live/cli.py docs-check [<documentation checkout>] [--report-only] [--allow-ref <branch>]

The checkout comes from the first non-flag argument, then $DOCS_REPO, then ../documentation next to this repository.
It parses every <EmbeddedCode> tag in docs/sdks/python/ and docs/sdks/asyncio/ whose url points at pubnub/python and
classifies each requested id (or whole-file embed) as live, compile-only, exception (snippet-exceptions.json) or
NOT COVERED. A covered embed must use the url form refs/heads/master/tests/live/... (or the branch given with
--allow-ref, for a docs preview), the file must exist, docs_extract must find each id in it, and coverage.json must
list the id for that very file. A SHA pin or any other path is NOT COVERED. Exit 1 on NOT COVERED unless --report-only.
The documentation checkout is only read. No network.
"""
import os
import re
from collections import Counter
from pathlib import Path

from . import LIVE_REL, REPO_ROOT, manifest, snippets

OUT_OF_SCOPE_PAGES = [
    'docs/sdks/python/api-reference/users.md',
    'docs/sdks/python/api-reference/spaces.md',
    'docs/sdks/python/api-reference/memberships.md',
]
URL = re.compile(r"url=\{?['\"](https://raw\.githubusercontent\.com/pubnub/python/([^'\"]+))['\"]\}?")
SNIPPETS = re.compile(r'snippets=\{\[([^\]]*)\]\}')
TAG = re.compile(r'<EmbeddedCode\b[\s\S]*?/>')


def embeds(root):
    out = []
    for sub in ('python', 'asyncio'):
        base = root / 'docs' / 'sdks' / sub
        if not base.is_dir():
            continue
        for md in sorted(base.rglob('*.md*')):
            text = md.read_text()
            rel = md.relative_to(root).as_posix()
            for m in TAG.finditer(text):
                tag = m.group(0)
                u = URL.search(tag)
                if not u:
                    continue
                ids = re.findall(r"['\"]([A-Za-z0-9_/-]+)['\"]", ''.join(SNIPPETS.findall(tag)))
                out.append({'docs_file': rel, 'line': text[:m.start()].count('\n') + 1, 'url': u.group(1),
                            'tail': u.group(2), 'ids': ids})
    return out


def split_tail(tail):
    """('refs/heads/<branch>' | sha, path) from the part after pubnub/python/."""
    m = re.match(r'refs/heads/(.+?)/(tests/live/.*)$', tail)
    if m:
        return m.group(1), m.group(2)
    m = re.match(r'refs/heads/([^/]+)/(.*)$', tail)
    if m:
        return m.group(1), m.group(2)
    ref, _, path = tail.partition('/')
    return ref, path


def classify(root, allow_ref=None):
    data = manifest.read() or {'files': {}, 'whole_files': {}}
    exceptions = manifest.load_exceptions().get('exceptions', [])
    results = []
    for e in embeds(root):
        if e['docs_file'] in OUT_OF_SCOPE_PAGES:
            continue
        ref, path = split_tail(e['tail'])
        targets = e['ids'] or [None]
        for ident in targets:
            status, why = 'NOT COVERED', ''
            exc = next((x for x in exceptions if x['path'] == path and (x.get('ids') is None or ident in x['ids'])),
                       None)
            if exc:
                status, why = 'exception', exc['reason']
            elif not path.startswith(LIVE_REL + '/'):
                why = f'path {path} is outside {LIVE_REL}/'
            elif ref not in ('master', allow_ref):
                why = f'ref {ref} (only master{" or " + allow_ref if allow_ref else ""} is covered)'
            elif not (REPO_ROOT / path).exists():
                why = f'{path} does not exist'
            elif ident is None:
                if path in data.get('whole_files', {}):
                    status = 'live'
                else:
                    why = 'whole-file embed of a file that no test runs'
            elif not snippets.docs_extract((REPO_ROOT / path).read_text(), [ident]):
                why = f'docs_extract finds no "{ident}" in {path}'
            else:
                entry = data['files'].get(path, {}).get(ident)
                if entry:
                    status = entry['mode']
                    why = entry.get('test') or entry.get('reason', '')
                else:
                    why = f'coverage.json does not list "{ident}" for {path}'
            results.append({**e, 'ref': ref, 'path': path, 'id': ident, 'status': status, 'why': why})
    return results


def main(argv):
    argv = list(argv)
    allow_ref = argv[argv.index('--allow-ref') + 1] if '--allow-ref' in argv else None
    positional = [a for i, a in enumerate(argv) if not a.startswith('--') and (i == 0 or argv[i - 1] != '--allow-ref')]
    default = os.environ.get('DOCS_REPO') or REPO_ROOT.parent / 'documentation'
    root = Path(positional[0]) if positional else Path(default)
    if not (root / 'docs' / 'sdks').is_dir():
        print(f'docs-check: {root} is not a documentation checkout')
        return 2
    results = classify(root, allow_ref)
    counts = Counter(r['status'] for r in results)
    refs = Counter(r['ref'] for r in results)
    for r in results:
        if r['status'] == 'NOT COVERED' and '--verbose' in argv:
            print(f'docs-check: NOT COVERED {r["docs_file"]}:{r["line"]} {r["id"] or "(whole file)"}: {r["why"]}')
    reasons = Counter(re.sub(r'"[^"]*"|\S+\.py', '...', r['why']) for r in results if r['status'] == 'NOT COVERED')
    for reason, n in reasons.most_common():
        print(f'docs-check: NOT COVERED x{n}: {reason}')
    by_status = ', '.join(f'{k} {v}' for k, v in sorted(counts.items()))
    by_ref = ', '.join(f'{k} {v}' for k, v in sorted(refs.items()))
    print(f'docs-check: {len(results)} embedded ids from {root}: {by_status}. Refs: {by_ref}')
    if counts.get('NOT COVERED') and '--report-only' not in argv:
        return 1
    return 0
