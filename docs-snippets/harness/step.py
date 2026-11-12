"""Decorators that register a docs snippet step. The registry itself is read statically (registry.py).

step         a live test. The docs code sits between snippet markers in its body, assertions sit outside.
compile_only code that cannot run against the service. It is compiled and linted, not executed.
stub         a snippet kept for the docs that no repository test can run (for example a push delivery). Needs a reason.
"""
import asyncio
import functools
import _thread
import os
import threading

import pytest

from . import recorder

_RESULTS = {}


def results():
    return _RESULTS


def _check(rec):
    problems = []
    if os.environ.get('DOCS_SNIPPETS_STAGED') != '1':
        problems.append('the suite is not staged, run it through "python -m harness.cli run"')
    missing_start = [i for i in rec.snippets if i not in rec.started]
    missing_end = [i for i in rec.snippets if i not in rec.ended]
    if missing_start:
        problems.append('snippet never started: ' + ', '.join(missing_start))
    if missing_end:
        problems.append('snippet did not reach its snippet.end line: ' + ', '.join(missing_end))
    if rec.after_snippet_assertions == 0:
        problems.append('the step made no assertion after its snippet started')
    _RESULTS[rec.name] = {'ids': rec.snippets, 'assertions': rec.assertions}
    if problems:
        raise AssertionError('honesty check failed: ' + '; '.join(problems))


DEFAULT_TIMEOUT = 120


def _key(fn):
    """Same text as the pytest node id, for example sync/publish.py::test_signal."""
    path = os.path.abspath(fn.__code__.co_filename)
    return f'{os.path.basename(os.path.dirname(path))}/{os.path.basename(path)}::{fn.__name__}'


def step(*snippets, role='open', reason='', timeout=DEFAULT_TIMEOUT):
    if not snippets:
        raise ValueError('step needs at least one snippet id')

    def deco(fn):
        if asyncio.iscoroutinefunction(fn):
            @functools.wraps(fn)
            async def wrapper(*a, **k):
                rec = recorder.begin(_key(fn), snippets)
                try:
                    try:
                        await asyncio.wait_for(fn(*a, **k), timeout)
                    except asyncio.TimeoutError:
                        raise AssertionError(f'step timed out after {timeout}s')
                finally:
                    rec = recorder.finish()
                _check(rec)
        else:
            @functools.wraps(fn)
            def wrapper(*a, **k):
                rec = recorder.begin(_key(fn), snippets)
                timer = threading.Timer(timeout, _thread.interrupt_main)
                timer.daemon = True
                timer.start()
                try:
                    try:
                        fn(*a, **k)
                    except KeyboardInterrupt:
                        raise AssertionError(f'step timed out after {timeout}s')
                finally:
                    timer.cancel()
                    rec = recorder.finish()
                _check(rec)
        wrapper.snippet_ids = list(snippets)
        return getattr(pytest.mark, role)(wrapper)

    return deco


def compile_only(*snippets, role='open', reason=''):
    if not reason:
        raise ValueError('compile_only needs a reason')
    return lambda fn: fn


def stub(*snippets, role='open', reason=''):
    if not reason:
        raise ValueError('stub needs a reason')
    return lambda fn: fn
