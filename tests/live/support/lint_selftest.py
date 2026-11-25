"""Self-test of the offline checks, run by `cli.py lint`. Every broken fixture must be reported with its rule, the clean
fixture must pass, redaction must mask a registered key, and the Python extractor must reproduce the stored outputs of
the docs function (extractor_fixtures.json)."""
import json
import tempfile
import textwrap
from pathlib import Path

from . import lint_markers, redact, snippet_scan, snippets

FIXTURES_FILE = Path(__file__).resolve().parent / 'extractor_fixtures.json'

CLEAN = '''
from support import assertions as a


def test_clean(clients):
    """Snippet: clean_sample."""
    pubnub = clients.sync('open', 'x')
    # snippet.clean_sample
    envelope = pubnub.time().sync()
    # snippet.hide
    envelope = envelope
    # snippet.show
    print(envelope.result)
    # snippet.end
    a.ok(envelope.result)
'''

# (rule the lint must report, docset, file name, text)
BROKEN = [
    ('M1', 'sync', 'test_m1.py', '''
def test_m1():
    #snippet.no_space
    x = 1
    #snippet.end
    assert x
'''),
    ('M2', 'sync', 'test_m2.py', '''
def test_m2():
    # snippet.never_closed
    x = 1
    assert x
'''),
    ('M2', 'sync', 'test_m2b.py', '''
def test_m2b():
    # snippet.outer
    x = 1
    # snippet.inner
    y = 2
    # snippet.end
    assert x and y
'''),
    ('M3', 'sync', 'test_m3.py', '''
def test_m3():
    # snippet.long_hidden
    x = 1
    # snippet.hide
    a1 = 1
    a2 = 2
    a3 = 3
    a4 = 4
    # snippet.show
    # snippet.end
    assert x and a1 and a2 and a3 and a4
'''),
    ('M4', 'sync', 'test_m4.py', '''
def test_m4():
    # snippet.twice
    x = 1
    # snippet.end
    # snippet.twice
    y = 1
    # snippet.end
    assert x and y
'''),
    ('M5', 'sync', 'test_m5.py', '''
def test_m5():
    x = 1
    # snippet.empty
    # snippet.end
    assert x
'''),
    ('M6', 'sync', 'test_m6.py', '''
def test_m6():
    # snippet.has_assert
    x = 1
    assert x
    # snippet.end
    assert x
'''),
    ('M6', 'sync', 'test_m6b.py', '''
from support.wait import eventually


def test_m6b():
    # snippet.has_wait
    x = eventually(lambda: 1)
    # snippet.end
    assert x
'''),
    ('M7', 'sync', 'test_m7.py', '''
def test_m7():
    # snippet.has_try
    try:
        x = 1
    except ValueError:
        x = 2
    # snippet.end
    assert x
'''),
    ('M8', 'sync', 'test_m8.py', '''
def test_m8():
    x = 1
    if x:
        # snippet.half_block
        y = 1
    else:
        # snippet.end
        y = 2
    assert y
'''),
    ('H1', 'sync', 'test_h1.py', '''
def helper_nobody_calls():
    # snippet.orphan
    x = 1
    # snippet.end
    return x


def test_h1():
    assert True
'''),
    ('H2', 'sync', 'test_h2.py', '''
def test_h2():
    # snippet.no_assertion
    x = 1
    # snippet.end
    print(x)
'''),
    ('H3', 'sync', 'test_h3.py', '''
def test_h3():
    x = 1
    # snippet.early_return
    if x:
        return
    # snippet.end
    assert x
'''),
    ('H4', 'sync', 'test_h4.py', '''
import pytest


@pytest.mark.skip(reason='no')
def test_h4():
    # snippet.skipped
    x = 1
    # snippet.end
    assert x
'''),
    ('H5', 'sync', 'sample_app.py', '''
# snippet.whole_sample
print('hello')
# snippet.end
'''),
    ('P1', 'asyncio', 'test_p1.py', '''
async def test_p1(aclients):
    pubnub = aclients.asyncio('open', 'x')
    # snippet.future_unchecked
    envelope = await pubnub.time().future()
    print(envelope)
    # snippet.end
    assert pubnub
'''),
]

# docs_extract cases without a docs checkout: (text, ids, expected lines). The checked-in extractor_fixtures.json
# holds the cases whose expected output came from the docs function itself.


def _write(root, docset, name, text):
    folder = root / docset / 'api_reference'
    folder.mkdir(parents=True, exist_ok=True)
    (folder / name).write_text(textwrap.dedent(text).lstrip('\n'))


def run_lint_fixtures():
    problems = []
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        (root / 'shared').mkdir()
        (root / 'shared' / '__init__.py').write_text('')
        _write(root, 'sync', 'test_clean.py', CLEAN)
        errors, *_ = lint_markers.lint(snippet_scan.scan_tier(root))
        if errors:
            problems.append('the clean fixture is reported: ' + '; '.join(errors))
    for rule, docset, name, text in BROKEN:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / 'shared').mkdir()
            _write(root, docset, name, text)
            errors, *_ = lint_markers.lint(snippet_scan.scan_tier(root))
            if not any(f' {rule} ' in e or f' {rule}/' in e or f'/{rule}/' in e or f'/{rule} ' in e for e in errors):
                problems.append(f'{name}: rule {rule} was not reported (got: {errors or "nothing"})')
    return problems


def run_redact():
    redact.register('pub-c-00000000-0000-0000-0000-000000000000')
    text = redact.scrub('GET /publish/pub-c-00000000-0000-0000-0000-000000000000/x?auth=abcdef123456&uuid=u')
    problems = []
    if redact.leaks(text):
        problems.append('redact: a registered key survived scrub()')
    if 'abcdef123456' in text:
        problems.append('redact: the auth query parameter survived scrub()')
    return problems


def run_extractor_fixtures():
    if not FIXTURES_FILE.exists():
        return ['extractor_fixtures.json is missing']
    data = json.loads(FIXTURES_FILE.read_text())
    problems = []
    for case in data['cases']:
        got = snippets.docs_extract_lines(case['text'], case['ids'])
        if got != case['expected']:
            problems.append(f'extractor case {case["name"]!r}: the Python extractor gives {got!r}, '
                            f'docs gave {case["expected"]!r}')
    return problems


def main():
    problems = run_lint_fixtures() + run_redact() + run_extractor_fixtures()
    for p in problems:
        print('selftest: FAILED', p)
    n = len(json.loads(FIXTURES_FILE.read_text())['cases']) if FIXTURES_FILE.exists() else 0
    print(f'selftest: {len(BROKEN)} broken lint fixtures, 1 clean fixture, {n} extractor cases, '
          f'{len(problems)} problems')
    return 1 if problems else 0
