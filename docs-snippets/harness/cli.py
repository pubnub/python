"""Command line: python -m harness.cli <env|lint|dry|manifest|stage|run|janitor>"""
import compileall
import os
import subprocess
import sys

from . import env, janitor, lint_markers, manifest, preflight, registry, redact, stage


def _compile():
    ok = compileall.compile_dir(str(registry.ROOT), quiet=1, rx=__import__('re').compile(r'(\.run|report)'))
    print('compile:', 'ok' if ok else 'FAILED')
    return 0 if ok else 1


def _reporter_selftest():
    redact.register('pub-c-00000000-0000-0000-0000-000000000000')
    text = redact.scrub('GET /publish/pub-c-00000000-0000-0000-0000-000000000000/x')
    bad = redact.leaks(text)
    print('reporter self-test:', 'ok' if not bad else 'FAILED, a secret survived scrub()')
    return 1 if bad else 0


def dry():
    rc = _compile() | main(['selftest']) | lint_markers.main() | manifest.main(['--check']) | _reporter_selftest()
    if os.environ.get('DOCS_SNIPPETS_DRY_COLLECT', '1') == '1':
        rc |= subprocess.call([sys.executable, '-m', 'pytest', '--collect-only', '-q', '--shard', 'all'],
                              cwd=registry.ROOT, env={**os.environ, 'DOCS_SNIPPETS_STAGED': '1'}) and 0
    print('dry:', 'ok' if rc == 0 else 'FAILED')
    return rc


def run(argv):
    shard = 'all'
    if '--shard' in argv:
        shard = argv[argv.index('--shard') + 1]
    extra = [a for a in argv if a not in ('--shard', shard, '--keep')]
    if os.environ.get('CI') and ('-k' in extra or os.environ.get('DOCS_SNIPPETS_MUTATE')):
        print('subset selection and mutation are refused in CI')
        return 2
    needed = ('open', 'pam') if shard == 'all' else (shard,)
    for line in env.status():
        if line.split(':')[0] in needed:
            print('keys', line)
    if env.missing('admin'):
        print('preflight: not run, PUBNUB_ADMIN_API_KEY is missing')
    elif preflight.main():
        print('preflight: a keyset lacks a feature, see above. The steps that need it will fail.')
    target = stage.stage()
    print('staged:', target.name)
    # The staged copy lives in .run/<id>/, so its harness cannot find the checkout by itself. Put the repository root on
    # the import path, otherwise pytest only works where pubnub is installed.
    repo_root = str(registry.ROOT.parent)
    python_path = os.pathsep.join(p for p in (repo_root, os.environ.get('PYTHONPATH', '')) if p)
    environ = {**os.environ, 'DOCS_SNIPPETS_STAGED': '1', 'PYTHONUNBUFFERED': '1', 'PYTHONPATH': python_path,
               'DOCS_SNIPPETS_REPORT': str(registry.ROOT / 'report' / shard),
               'DOCS_SNIPPETS_LEDGER_DIR': str(registry.ROOT / '.run')}
    import pubnub
    from pubnub.pubnub_core import PubNubCore
    print('sdk:', pubnub.__file__, PubNubCore.SDK_VERSION)
    rc = subprocess.call([sys.executable, '-u', '-m', 'pytest', '--shard', shard, *extra], cwd=target, env=environ)
    if '--keep' not in argv:
        import shutil
        shutil.rmtree(target, ignore_errors=True)
    print('janitor...')
    rc |= janitor.main(shard)
    return rc


def main(argv):
    cmd = argv[0] if argv else 'dry'
    if cmd == 'env':
        print('\n'.join(env.status()))
        return 0
    if cmd == 'lint':
        return lint_markers.main()
    if cmd == 'manifest':
        return manifest.main(argv[1:])
    if cmd == 'dry':
        return dry()
    if cmd == 'stage':
        print(stage.stage())
        return 0
    if cmd == 'run':
        return run(argv[1:])
    if cmd == 'selftest':
        return subprocess.call([sys.executable, '-m', 'pytest', '-q', 'selftest'], cwd=registry.ROOT)
    if cmd == 'janitor':
        return janitor.main()
    print(__doc__)
    return 2


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
