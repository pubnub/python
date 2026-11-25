"""Equivalence check of the Python extractor (support/snippets.py) against the docs function.

    python -u tests/live/cli.py extractor --regen <documentation checkout>

runs extractSnippets() of <docs>/src/helper/codeSnippetFetcher.ts with `npx tsx` (from the docs checkout, read only)
on every case below and writes the outputs to support/extractor_fixtures.json. CI has no docs checkout, so the lint
self-test compares the Python extractor against the stored outputs.
"""
import json
import shutil
import subprocess  # nosec B404: fixed commands only, see the calls below
import tempfile
from pathlib import Path

FIXTURES_FILE = Path(__file__).resolve().parent / 'extractor_fixtures.json'

CASES = [
    ('plain', '# snippet.a\nx = 1\n# snippet.end\n', ['a']),
    ('indented', 'def f():\n    # snippet.a\n    x = 1\n    if x:\n        y = 2\n    # snippet.end\n', ['a']),
    ('nested start ends the outer', '# snippet.a\nx = 1\n# snippet.b\ny = 2\n# snippet.end\n', ['a']),
    ('nested start, inner id', '# snippet.a\nx = 1\n# snippet.b\ny = 2\n# snippet.end\n', ['b']),
    ('no space after hash is not a marker', '#snippet.a\nx = 1\n#snippet.end\n', ['a']),
    ('two spaces after hash', '#  snippet.a\nx = 1\n#  snippet.end\n', ['a']),
    ('id with a slash', '# snippet.a/b\nx = 1\n# snippet.end\n', ['a/b']),
    ('hide and show', '# snippet.a\nx = 1\n# snippet.hide\nsecret = 2\n# snippet.show\ny = 3\n# snippet.end\n', ['a']),
    ('blank lines with whitespace', '    # snippet.a\n    x = 1\n   \n\n    y = 2\n    # snippet.end\n', ['a']),
    ('tabs', '\t# snippet.a\n\tx = 1\n\t\ty = 2\n\t# snippet.end\n', ['a']),
    ('blueprint line', '# snippet.a\nx = 1\n# blueprint._o945md2\ny = 2\n# snippet.end\n', ['a']),
    ('empty region', '# snippet.a\n# snippet.end\n', ['a']),
    ('missing id', '# snippet.a\nx = 1\n# snippet.end\n', ['zzz']),
    ('runs to the end of the file', 'z = 0\n# snippet.a\nx = 1\ny = 2\n', ['a']),
    ('first start marker wins', '# snippet.a\nx = 1\n# snippet.end\n# snippet.a\nx = 2\n# snippet.end\n', ['a']),
    ('two ids in one call', '# snippet.a\nx = 1\n# snippet.end\n# snippet.b\ny = 2\n# snippet.end\n', ['a', 'b']),
    ('trailing spaces on markers', '# snippet.a   \nx = 1\n# snippet.end  \n', ['a']),
    ('carriage returns', '# snippet.a\r\nx = 1\r\n# snippet.end\r\n', ['a']),
    ('other prefix ends the region', '# snippet.a\nx = 1\n// snippet.b\ny = 2\n# snippet.end\n', ['a']),
    ('same id with another prefix is no boundary', '# snippet.a\nx = 1\n// snippet.a\ny = 2\n# snippet.end\n', ['a']),
    ('end marker of another prefix', '# snippet.a\nx = 1\n// snippet.end\ny = 2\n# snippet.end\n', ['a']),
    ('hide without show', '# snippet.a\nx = 1\n# snippet.hide\ny = 2\n# snippet.end\n', ['a']),
]

TS = r'''
import { extractSnippets } from '%s';
import fs from 'node:fs';
const cases = JSON.parse(fs.readFileSync(process.argv[2], 'utf8'));
const prefixes = ['// ', '# ', '/* ', '<!-- ', '<%%-- '];
const out = cases.map((c: any) => ({ ...c, expected: extractSnippets(c.text, c.ids, prefixes) }));
fs.writeFileSync(process.argv[3], JSON.stringify(out));
'''


def _docs_commit(docs_root):
    """Short commit of the docs checkout, read from its .git files, so no process runs."""
    dot_git = docs_root / '.git'
    if dot_git.is_file():  # a worktree: the file points at the real git directory
        pointer = dot_git.read_text().split('gitdir:', 1)[1].strip()
        dot_git = (docs_root / pointer).resolve()
    head = (dot_git / 'HEAD').read_text().strip()
    if head.startswith('ref: '):
        ref = head[len('ref: '):]
        ref_file = dot_git / ref
        if ref_file.is_file():
            head = ref_file.read_text().strip()
        else:
            packed = dot_git / 'packed-refs'
            for line in (packed.read_text().splitlines() if packed.exists() else []):
                if line.endswith(' ' + ref):
                    head = line.split()[0]
                    break
    return head[:7]


def regen(docs_root):
    docs_root = Path(docs_root).resolve()
    source = docs_root / 'src' / 'helper' / 'codeSnippetFetcher.ts'
    if not source.exists():
        print(f'extractor: {source} not found')
        return 2
    cases = [{'name': n, 'text': t, 'ids': i} for n, t, i in CASES]
    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        (tmp / 'cases.json').write_text(json.dumps(cases))
        script = tmp / 'extract.ts'
        script.write_text(TS % source.as_posix())
        npx = shutil.which('npx')
        if npx is None:
            raise RuntimeError('npx was not found on PATH')
        # The command is fixed. Only paths vary, and this function creates them in tmp, so no user input reaches it.
        command = [npx, 'tsx', str(script), str(tmp / 'cases.json'), str(tmp / 'out.json')]
        subprocess.run(command, cwd=docs_root, check=True, shell=False)  # nosec B603
        out = json.loads((tmp / 'out.json').read_text())
    data = {'$comment': 'GENERATED by python -u tests/live/cli.py extractor --regen <docs checkout>. Expected outputs '
                        'come from extractSnippets() of the docs repo.',
            'docs_commit': _docs_commit(docs_root), 'cases': out}
    FIXTURES_FILE.write_text(json.dumps(data, indent=1) + '\n')
    print(f'extractor: wrote {len(out)} cases to {FIXTURES_FILE.name} (docs {data["docs_commit"]})')
    return 0
