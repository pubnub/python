"""Coverage manifest: one entry per snippet id with file, step, role, mode and reason.

--check fails on a stale manifest. It also reports, without failing, the docs ids that the manifest does not know
(read from EmbeddedCode tags in a docs checkout, DOCS_REPO or ../documentation).
"""
import json
import re
import sys
from pathlib import Path

from . import registry

PATH = registry.ROOT / 'coverage.json'


def build():
    data = {}
    for e in registry.scan():
        for i in e.ids:
            data.setdefault(e.docset, {})[i] = {
                'file': e.file,
                'step': e.func,
                'role': e.role,
                'mode': e.mode,
                'reason': e.reason,
            }
    return {d: dict(sorted(v.items())) for d, v in sorted(data.items())}


def docs_ids():
    import os
    root = Path(os.environ.get('DOCS_REPO') or registry.ROOT.parent.parent / 'documentation')
    found = {}
    for docset, sub in (('sync', 'python'), ('asyncio', 'asyncio')):
        base = root / 'docs' / 'sdks' / sub
        if not base.is_dir():
            continue
        for md in base.rglob('*.md*'):
            for tag in re.findall(r'<EmbeddedCode[^>]*docs-snippets/[^>]*>', md.read_text()):
                lists = ''.join(re.findall(r'snippets=\{\[[^\]]*\]\}', tag))
                found.setdefault(docset, set()).update(re.findall(r"'([a-zA-Z0-9_-]+)'", lists))
    return found


def main(argv):
    text = json.dumps(build(), indent=2, sort_keys=True) + '\n'
    if '--check' in argv:
        current = PATH.read_text() if PATH.exists() else ''
        if current != text:
            print('manifest: coverage.json is stale, run "python -m harness.cli manifest"')
            return 1
        total = sum(len(v) for v in build().values())
        print(f'manifest: ok, {total} snippet ids')
        known = {d: set(v) for d, v in build().items()}
        for docset, ids in docs_ids().items():
            gone = sorted(ids - known.get(docset, set()))
            if gone:
                print(f'manifest: docs ids without a snippet in {docset} (not a failure): ' + ', '.join(gone))
        return 0
    PATH.write_text(text)
    print(f'manifest: wrote {PATH.name}')
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
