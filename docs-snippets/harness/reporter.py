"""pytest plugin: writes report/run.json and report/summary.md, with every value scrubbed."""
import json
import os
import platform
import time
from pathlib import Path

from . import redact, registry, step

_records = []
_sections = {}  # nodeid -> list of (phase, title, text), everything pytest captured for that step
_t0 = time.monotonic()


def pytest_runtest_logreport(report):
    for title, text in getattr(report, 'sections', []):
        _sections.setdefault(report.nodeid, []).append((report.when, title, text))
    if report.when == 'call' or (report.when == 'setup' and report.outcome != 'passed'):
        _records.append({
            'test': report.nodeid,
            'outcome': report.outcome,
            'duration': round(report.duration, 2),
            'error': redact.scrub(str(report.longreprtext))[-2000:] if report.outcome == 'failed' else '',
            'full_error': redact.scrub(str(report.longreprtext)) if report.outcome == 'failed' else '',
        })


def _write_step_logs(out):
    """One log file per step in report/<shard>/steps/: outcome, snippet ids, assertions, captured output, error."""
    folder = out / 'steps'
    folder.mkdir(exist_ok=True)
    for r in _records:
        name = r['test'].split('::')[-1]
        module = r['test'].split('::')[0].replace('/', '__').replace('.py', '')
        info = step.results().get(r['test'], {})
        lines = [f"test:        {r['test']}", f"outcome:     {r['outcome']}", f"seconds:     {r['duration']}",
                 f"snippet ids: {', '.join(info.get('ids', []))}", f"assertions:  {info.get('assertions', 0)}", '']
        for phase, title, text in _sections.get(r['test'], []):
            lines += [f'--- {title} ({phase}) ---', text.rstrip(), '']
        if r['full_error']:
            lines += ['--- failure ---', r['full_error'].rstrip(), '']
        (folder / f'{module}__{name}.log').write_text(redact.scrub('\n'.join(lines)) + '\n')


def pytest_sessionfinish(session, exitstatus):
    out = Path(os.environ.get('DOCS_SNIPPETS_REPORT', registry.ROOT / 'report'))
    out.mkdir(parents=True, exist_ok=True)
    try:
        import pubnub
        from pubnub.pubnub_core import PubNubCore
        sdk = {'version': PubNubCore.SDK_VERSION, 'file': pubnub.__file__}
    except Exception:  # the report must never hide the real failure
        sdk = {}
    counts = {}
    for r in _records:
        counts[r['outcome']] = counts.get(r['outcome'], 0) + 1
    run = {
        'sdk': sdk,
        'python': platform.python_version(),
        'seconds': round(time.monotonic() - _t0, 1),
        'counts': counts,
        'steps': step.results(),
        'tests': [{k: v for k, v in r.items() if k != 'full_error'} for r in _records],
    }
    text = redact.scrub(json.dumps(run, indent=2))
    (out / 'run.json').write_text(text)
    head = f"SDK {sdk.get('version', '?')} on Python {run['python']}, {run['seconds']} s"
    lines = ['# Docs snippet run', '', head, '', '| outcome | count |', '| :-- | --: |']
    lines += [f'| {k} | {v} |' for k, v in sorted(counts.items())]
    lines += ['', '| test | outcome | seconds | assertions | snippet ids |', '| :-- | :-- | --: | --: | :-- |']
    for r in sorted(_records, key=lambda x: -x['duration']):
        ids = ', '.join(step.results().get(r['test'], {}).get('ids', []))
        n = step.results().get(r['test'], {}).get('assertions', 0)
        lines.append(f"| {r['test']} | {r['outcome']} | {r['duration']} | {n} | {ids} |")
    _write_step_logs(out)
    (out / 'summary.md').write_text(redact.scrub('\n'.join(lines)) + '\n')
    leaked = redact.leaks(text)
    if leaked:
        session.exitstatus = 1
        print('reporter self-test failed: a loaded secret appears in the report')
