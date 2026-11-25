"""Shared scanner of the tier: lists the files that can hold markers, scans the markers with the syntax of the docs
extractor (snippets.scan), and uses ast to find the test function that runs each snippet. The marker lint, the
coverage manifest and the docs cross-check build on it. Pure file reads: nothing is imported or
executed, no keys, no network.

Owner of a region:
  test          the innermost top-level `def test_*` / `async def test_*` that contains the region (mode live)
  compile-only  a top-level function decorated with @compile_only(reason) (support/marks.py)
  helper        a top-level function of the same file, called by a test (mode live, the first caller names it)
  none          anything else (the lint reports it)
"""
import ast
from dataclasses import dataclass, field
from pathlib import Path

from . import DOCSETS, LIVE_DIR, LIVE_REL
from . import snippets

ASSERT_NAMES = {
    'ok', 'eq', 'contains', 'not_contains', 'timetoken', 'raises', 'assert_ok', 'assert_timetoken', 'raises_pubnub',
    'assert_server_time', 'eventually', 'aeventually', 'settled', 'asettled', 'settle_seeded', 'asettle_seeded',
}
ROLE_METHODS = {'sync', 'asyncio', 'make', 'config'}
ROLE_FUNCS = {'client_config', 'config', 'unreachable_config', 'use_pam_keys', 'use_open_keys'}
ROLES = ('open', 'pam')


@dataclass
class Func:
    name: str
    node: ast.AST
    start: int  # first line, decorators included
    end: int
    is_async: bool
    is_test: bool
    compile_only: str = ''  # the reason, when decorated with @compile_only
    skip_marks: list = field(default_factory=list)


@dataclass
class ScannedFile:
    rel: str  # repository relative, forward slashes
    path: Path
    docset: str
    kind: str  # 'test' | 'sample' | 'shared'
    text: str
    tree: ast.AST
    regions: list
    problems: list
    warnings: list
    funcs: dict  # top-level functions by name
    imports: dict  # local name -> (module, original name)

    @property
    def lines(self):
        return self.text.split('\n')

    @property
    def live_rel(self):
        """Path relative to tests/live."""
        return self.rel[len(LIVE_REL) + 1:]


@dataclass
class Snippet:
    id: str
    file: ScannedFile
    region: snippets.Region
    owner: str  # 'test' | 'compile-only' | 'helper' | 'none'
    func: Func = None
    test: Func = None  # the test that runs it
    roles: list = field(default_factory=list)

    @property
    def mode(self):
        return {'test': 'live', 'helper': 'live', 'compile-only': 'compile-only'}.get(self.owner, 'invalid')

    @property
    def test_id(self):
        return f'{self.file.live_rel}::{self.test.name}' if self.test else None


def list_files(root=LIVE_DIR):
    """Every *.py under tests/live/<docset>/ (tests and whole-file samples), sorted."""
    out = []
    for docset in DOCSETS:
        for path in sorted((root / docset).rglob('*.py')):
            if '__pycache__' in path.parts:
                continue
            out.append((path, docset, 'test' if path.name.startswith('test_') else 'sample'))
    return out


def _decorator_name(deco):
    target = deco.func if isinstance(deco, ast.Call) else deco
    parts = []
    while isinstance(target, ast.Attribute):
        parts.insert(0, target.attr)
        target = target.value
    if isinstance(target, ast.Name):
        parts.insert(0, target.id)
    return '.'.join(parts)


def _funcs(tree):
    out = {}
    for node in tree.body:
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        start = min([node.lineno] + [d.lineno for d in node.decorator_list])
        f = Func(node.name, node, start, node.end_lineno, isinstance(node, ast.AsyncFunctionDef),
                 node.name.startswith('test_'))
        for deco in node.decorator_list:
            name = _decorator_name(deco)
            if name == 'compile_only' and isinstance(deco, ast.Call) and deco.args:
                f.compile_only = ast.literal_eval(deco.args[0])
            if name.split('.')[-1] in ('skip', 'skipif', 'xfail') and 'mark' in name:
                f.skip_marks.append(name)
        out[node.name] = f
    return out


def _imports(tree):
    out = {}
    for node in tree.body:
        if isinstance(node, ast.ImportFrom) and node.module:
            for alias in node.names:
                out[alias.asname or alias.name] = (node.module, alias.name)
        elif isinstance(node, ast.Import):
            for alias in node.names:
                out[alias.asname or alias.name.split('.')[0]] = (alias.name, None)
    return out


def scan_file(path, docset, kind, root=LIVE_DIR):
    text = path.read_text()
    rel = f'{LIVE_REL}/' + path.resolve().relative_to(root.resolve()).as_posix()
    regions, problems, warnings = snippets.scan(rel, text)
    tree = ast.parse(text, filename=str(path))
    f = ScannedFile(rel, path, docset, kind, text, tree, regions, problems, warnings, _funcs(tree), _imports(tree))
    f.root = root
    return f


_shared_cache = {}


def shared_file(module, root=LIVE_DIR):
    """ScannedFile of tests/live/shared/<page>.py for an import like 'shared.publish', or None."""
    if not module.startswith('shared.'):
        return None
    key = (str(root), module)
    if key not in _shared_cache:
        path = root / 'shared' / (module.split('.', 1)[1] + '.py')
        _shared_cache[key] = scan_file(path, '', 'shared', root) if path.exists() else None
    return _shared_cache[key]


def resolve_helper(file, name):
    """The Func for a name a test calls: a top-level function of the same file or of an imported shared module."""
    if name in file.funcs:
        return file, file.funcs[name]
    if name in file.imports:
        module, original = file.imports[name]
        shared = shared_file(module, getattr(file, 'root', LIVE_DIR))
        if shared and original in shared.funcs:
            return shared, shared.funcs[original]
    return None, None


def calls(node):
    """Names called directly (f(...)) inside node."""
    return {n.func.id for n in ast.walk(node) if isinstance(n, ast.Call) and isinstance(n.func, ast.Name)}


def _roles_in(node):
    found = set()
    for n in ast.walk(node):
        if not isinstance(n, ast.Call):
            continue
        name = n.func.attr if isinstance(n.func, ast.Attribute) else getattr(n.func, 'id', None)
        if name in ('pam', 'open') and isinstance(n.func, ast.Attribute):
            found.add(name)
        elif name in ROLE_METHODS | ROLE_FUNCS:
            first = n.args[0] if n.args else None
            if isinstance(first, ast.Constant) and first.value in ROLES:
                found.add(first.value)
            elif name in ('use_pam_keys',):
                found.add('pam')
            elif name in ('use_open_keys',):
                found.add('open')
    return found


def roles_of(file, func):
    """Keyset roles a test uses: role literals of client calls in its body and, transitively, in the helpers it calls
    (same file or shared module). Heuristic: a role chosen at run time is not seen."""
    roles, seen, todo = set(), set(), [(file, func)]
    while todo:
        f, fn = todo.pop()
        if (f.rel, fn.name) in seen:
            continue
        seen.add((f.rel, fn.name))
        roles |= _roles_in(fn.node)
        for name in calls(fn.node):
            owner, helper = resolve_helper(f, name)
            if helper is not None:
                todo.append((owner, helper))
    return sorted(roles)


def _owner(file, region):
    inside = [f for f in file.funcs.values() if f.node.lineno <= region.start and region.end <= f.end]
    if not inside:
        return 'none', None, None
    func = inside[0]
    if func.compile_only:
        return 'compile-only', func, None
    if func.is_test:
        return 'test', func, func
    caller = next((f for f in file.funcs.values() if f.is_test and func.name in calls(f.node)), None)
    return ('helper', func, caller) if caller else ('none', func, None)


def scan_tier(root=LIVE_DIR):
    files, out = [], []
    for path, docset, kind in list_files(root):
        f = scan_file(path, docset, kind, root)
        files.append(f)
        for region in f.regions:
            owner, func, test = _owner(f, region)
            s = Snippet(region.id, f, region, owner, func, test)
            if test is not None:
                s.roles = roles_of(f, test)
            out.append(s)
    return files, out
