"""Command line of the live tier. Run from anywhere: python -u tests/live/cli.py <command>

  lint                       offline checks: compile, marker lint, self-test, manifest --check, groups --check,
                             exceptions shape, resources shape, port-map --check. No keys, no network.
  manifest [--check]         write or check coverage.json
  groups --check             group consistency (also part of lint)
  groups --matrix [name]     the CI job matrix as JSON ("all" or empty: every group)
  docs-check [<docs>] [--report-only] [--allow-ref <branch>] [--verbose]
                             classify every docs embed from pubnub/python
  port-map [--check]         old-id to new-test mapping of the port from docs-snippets/
  extractor --regen <docs>   regenerate the extractor fixtures from the docs function
  parity                     ids that exist in one docset only, per page
  env                        which roles have keys (never prints a value)
  janitor [--role open|pam]  clean the listed resources (NEEDS KEYS AND NETWORK)
  preflight                  keyset feature check (NEEDS KEYS AND NETWORK)

The tests themselves run with pytest from this folder (testpaths only apply when pytest runs in its rootdir):
  cd tests/live && python -u -m pytest
"""
import compileall
import re
import sys
from pathlib import Path

LIVE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(LIVE_DIR))

from support import env, groups, lint_markers, lint_selftest, manifest, port_map, resources  # noqa: E402


def _compile():
    ok = compileall.compile_dir(str(LIVE_DIR), quiet=1, rx=re.compile(r'__pycache__'))
    print('compile:', 'ok' if ok else 'FAILED')
    return 0 if ok else 1


def lint(argv):
    rc = _compile()
    rc |= lint_markers.main(argv)
    rc |= lint_selftest.main()
    rc |= manifest.main(['--check'])
    rc |= groups.main(['--check'])
    problems = resources.problems()
    for p in problems:
        print('resources:', p)
    print(f'resources: {len(resources.all_names())} names, {len(problems)} problems')
    rc |= 1 if problems else 0
    if port_map.base_available():
        rc |= port_map.main(['--check'])
    else:
        # A shallow CI checkout, or a clone after the squash merge, has no old suite to compare with. The proof was made
        # once, on the port branch, and stays available as `cli.py port-map --check` wherever the base commit exists.
        print(f'port-map: skipped, base commit {port_map.BASE} is not in this checkout')
    print('lint:', 'ok' if rc == 0 else 'FAILED')
    return rc


def main(argv):
    cmd, rest = (argv[0], argv[1:]) if argv else ('', [])
    if cmd == 'lint':
        return lint(rest)
    if cmd == 'manifest':
        return manifest.main(rest)
    if cmd == 'groups':
        return groups.main(rest)
    if cmd == 'docs-check':
        from support import docs_check
        return docs_check.main(rest)
    if cmd == 'port-map':
        return port_map.main(rest)
    if cmd == 'extractor' and '--regen' in rest:
        from support import extractor
        return extractor.regen(rest[rest.index('--regen') + 1])
    if cmd == 'parity':
        for line in lint_markers.parity():
            print(line)
        return 0
    if cmd == 'env':
        print('\n'.join(env.status()))
        return 0
    if cmd == 'janitor':
        from support import janitor
        return janitor.main(rest)
    if cmd == 'preflight':
        from support import preflight
        return preflight.main(rest)
    print(__doc__)
    return 2


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
