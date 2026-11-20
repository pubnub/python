"""Dry checks of the harness itself. No network, no keys. Run: python -m harness.cli selftest"""
import os
import textwrap

import pytest

from harness import assertions as a
from harness import markers, names, recorder, redact, stage, step


def test_redaction_masks_values_encoded_forms_and_shapes():
    redact.register('secret/value+1234')
    text = 'url=secret%2Fvalue%2B1234 raw=secret/value+1234 key=pub-c-12345678-1234-1234-1234-123456789012'
    out = redact.scrub(text)
    assert 'secret' not in out and 'pub-c-' not in out
    assert not redact.leaks(out)


def test_markers_follow_the_docs_extractor_rules():
    src = textwrap.dedent('''\
        def f():
            # snippet.one
            x = 1
            # snippet.hide
            assert x
            # snippet.show
            y = 2
            # snippet.end
    ''')
    [r] = markers.regions(src)
    assert r.id == 'one' and r.end == 8
    assert [t.strip() for _, t in r.visible] == ['x = 1', 'y = 2']
    assert [t.strip() for _, t in r.hidden] == ['assert x']


def test_staging_keeps_line_numbers_and_adds_the_suffix():
    src = 'def f():\n    # snippet.one\n    c = "my_channel"\n    # snippet.end\n'
    out = stage.instrument(src, 'dsn-abc').splitlines()
    assert len(out) == 4
    assert out[1].strip() == "__snip__.start('one')  # snippet.one"
    assert 'my_channel-dsn-abc' in out[2]
    outside = stage.instrument('x = "my_channel"\n', 'dsn-abc')
    assert outside.strip() == 'x = "my_channel"', 'names outside the markers are not rewritten'
    assert out[3].strip() == "__snip__.end('one')  # snippet.end"


def _run(fn_body, ids=('one',)):
    recorder.install()
    os.environ['DOCS_SNIPPETS_STAGED'] = '1'

    @step.step(*ids)
    def sample():
        fn_body()
    return sample


def test_honesty_fails_when_snippet_does_not_reach_its_end():
    def body():
        __snip__.start('one')  # noqa: F821
        a.ok(True)
    with pytest.raises(AssertionError, match='did not reach'):
        _run(body)()


def test_honesty_fails_with_zero_assertions_after_the_snippet_started():
    def body():
        a.ok(True)  # before the snippet, does not count
        __snip__.start('one')  # noqa: F821
        __snip__.end('one')  # noqa: F821
    with pytest.raises(AssertionError, match='no assertion'):
        _run(body)()


def test_honesty_passes_for_a_proper_step():
    def body():
        __snip__.start('one')  # noqa: F821
        __snip__.end('one')  # noqa: F821
        a.eq(1, 1)
    _run(body)()


def test_mutation_makes_the_step_fail():
    def body():
        __snip__.start('one')  # noqa: F821
        __snip__.end('one')  # noqa: F821
        a.eq(1, 1)
    os.environ['DOCS_SNIPPETS_MUTATE'] = 'one'
    try:
        with pytest.raises(RuntimeError, match='mutation'):
            _run(body)()
    finally:
        del os.environ['DOCS_SNIPPETS_MUTATE']


def test_a_weakened_assertion_is_still_counted_and_wrong_values_fail():
    recorder.begin('x', [])
    with pytest.raises(AssertionError):
        a.eq(1, 2)
    recorder.finish()


def test_names_carry_marker_and_suffix():
    assert names.with_suffix('my_channel').startswith('my_channel-dsn-')
