"""Stage the suite: copy it to .run/<runId>/, add the run suffix to registered names and instrument the markers.

Staging rewrites only registered names and replaces each marker line in place, so line numbers never move and a
failure points at the same line of the source file.
"""
import ast
import re
import shutil

from . import markers as mk
from . import names, registry

IGNORE = shutil.ignore_patterns('.run', 'report', '__pycache__', '.env*', '*.pyc', '.pytest_cache')


def module_names(text):
    """A module may declare more literal names the staging rewrites: REGISTERED_NAMES = ['a', 'b'] (a plain list)."""
    m = re.search(r'^REGISTERED_NAMES\s*=\s*(\[[^\]]*\])', text, re.M)
    return ast.literal_eval(m.group(1)) if m else []


def _rewrite_names(line, suffix, extra=()):
    for name in list(names.REGISTERED) + list(extra):
        line = re.sub(r'(["\'])' + re.escape(name) + r'\1', lambda m: f'{m.group(1)}{name}-{suffix}{m.group(1)}', line)
    return line


def instrument(text, suffix, relpath=''):
    extra = module_names(text)
    out = []
    current = None
    func = ''
    for line in text.splitlines():
        fm = re.match(r'(?:async )?def (test_\w+)', line)
        if fm:
            func = fm.group(1)
        m = mk.MARKER.match(line)
        if m:
            name, indent = m.group(2), m.group(1)
            if name == 'end':
                out.append(f"{indent}__snip__.end({current!r})  # snippet.end")
                current = None
            elif name in ('hide', 'show'):
                out.append(line)
            else:
                current = name
                out.append(f"{indent}__snip__.start({name!r})  # snippet.{name}")
            continue
        # Only the lines the docs show carry the docs names. Test code outside the markers adds the suffix itself.
        tagged = f'{suffix}-{names.test_tag(relpath, func)}' if relpath else suffix
        out.append(_rewrite_names(line, tagged, extra) if current else line)
    return '\n'.join(out) + '\n'


def stage(run_id=None):
    suffix = names.run_suffix()
    run_id = run_id or suffix
    target = registry.ROOT / '.run' / run_id
    if target.exists():
        shutil.rmtree(target)
    shutil.copytree(registry.ROOT, target, ignore=IGNORE)
    for docset in registry.DOCSETS:
        for path in (target / docset).glob('*.py'):
            path.write_text(instrument(path.read_text(), suffix, str(path.relative_to(target)).replace('\\', '/')))
    return target
