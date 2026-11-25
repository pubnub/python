"""Marker lint of the live tier. Static: no keys, no network, nothing is executed.

Marker rules (the docs extractor, src/helper/codeSnippetFetcher.ts in the docs repo, defines what a marker is):
  M1  syntax "# snippet.<id>", "# snippet.end", "# snippet.hide", "# snippet.show", with the space after "#",
      id charset [a-zA-Z0-9_-]
  M2  every snippet has snippet.end, no start marker inside an open snippet
  M3  snippet.hide has snippet.show, a hidden block has at most MAX_HIDDEN_LINES lines and holds code
  M4  an id appears once per docset folder (sync/, asyncio/): the docs address a snippet by file and id
  M5  a snippet is not empty
  M6  no test-only code in the visible text: assert, pytest, the waits, anything imported from support or shared
  M7  no try/except, traceback or logging.exception in the visible text, except the ids in ERROR_HANDLING_SNIPPETS
  M8  the visible text, unindented, compiles on its own (await allowed in asyncio files)
Honesty rules (every snippet runs and is checked):
  H1  a snippet runs inside a test_* function (or a top-level helper a test calls), or sits in a @compile_only function
  H2  the test asserts after the snippet's end line (an assert statement, a call of an assertion helper, a helper of
      the file or of its shared module that asserts), or carries "# lint: asserted-via <helper>"
  H3  no return of the function that holds the snippet inside the snippet
  H4  no pytest.mark.skip, skipif or xfail and no pytest.skip() or pytest.xfail() in a test file
  H5  a whole-file sample (a .py file under a docset folder that is not test_*.py) is run by a test that names it
Asyncio rule:
  P1  in asyncio files, every name a snippet binds from "await ....future()" is used in an assertion after the end
      line (the call returns an error object instead of raising), except the ids in P1_EXEMPT
Warnings (do not fail): ids that exist in one docset only for the same page, a test whose docstring does not name its
snippet ids, allow-list entries no snippet needs.
"""
import ast
import re
import textwrap
from collections import defaultdict

from . import snippet_scan
from .snippet_scan import ASSERT_NAMES

MAX_HIDDEN_LINES = 3

# Snippets whose purpose is to show the error handling of the docs page (M7 does not apply). Keep it short.
ERROR_HANDLING_SNIPPETS = {
    # The published sample shows what a CBC-only client does with GCM messages (examples/crypto.py)
    ('sync', 'cipher_mode_experiment'),
}

# Hidden blocks that may hold more than MAX_HIDDEN_LINES lines, each with its reason. Empty: every hidden block is
# short. An entry no snippet needs is reported as a warning.
LONG_HIDDEN_BLOCKS = set()

# Regions that do not compile on their own (M8), for example a region that ends inside a block, each with its
# reason. Empty: every region compiles. An entry no snippet needs is reported as a warning.
NOT_STANDALONE = set()

# Asyncio snippets whose envelope no assertion after the end line can check (P1), each with its reason.
P1_EXEMPT = {
    # The envelope is a local of the sample's recursive function, so no assertion after the end line can read it. The
    # sample checks is_error() itself and returns, and the test compares the printed pages with an independent read
    # of the same history, so an error leaves the output empty and fails the test.
    ('asyncio', 'history_paging'),
}

TEST_ONLY_NAMES = {'pytest', 'eventually', 'aeventually', 'settled', 'asettled', 'watch', 'expect_event',
                   'expect_status', 'connected', 'a'}
ESCAPE = re.compile(r'^\s*#\s*lint:\s*asserted-via\s+([A-Za-z_]\w*)\s*$')


def _support_names(f):
    return {name for name, (module, _) in f.imports.items() if module.split('.')[0] in ('support', 'shared')}


def _asserting_helpers(f):
    """Top-level helpers (file and imported shared ones) that hold an assertion."""
    out = set()
    for name, func in f.funcs.items():
        if not func.is_test and _first_assertion(func.node, 0, set()) is not None:
            out.add(name)
    for name, (module, original) in f.imports.items():
        shared = snippet_scan.shared_file(module, getattr(f, 'root', snippet_scan.LIVE_DIR))
        if shared and original in shared.funcs and _first_assertion(shared.funcs[original].node, 0, set()):
            out.add(name)
    return out


def _call_name(call):
    f = call.func
    if isinstance(f, ast.Name):
        return f.id
    if isinstance(f, ast.Attribute):
        return f.attr
    return None


def _root(expr):
    while isinstance(expr, (ast.Attribute, ast.Call, ast.Subscript, ast.Await)):
        expr = expr.value if not isinstance(expr, ast.Call) else expr.func
    return expr.id if isinstance(expr, ast.Name) else None


def _is_assertion(node, helpers):
    if isinstance(node, ast.Assert):
        return True
    if isinstance(node, ast.Call):
        name = _call_name(node)
        if name in ASSERT_NAMES:
            return True
        if isinstance(node.func, ast.Name) and node.func.id in helpers:
            return True
        if isinstance(node.func, ast.Attribute) and _root(node.func) == 'a':
            return True
    return False


def _first_assertion(node, after_line, helpers):
    lines = [n.lineno for n in ast.walk(node) if _is_assertion(n, helpers) and n.lineno > after_line]
    return min(lines) if lines else None


def _assertion_nodes(node, after_line, helpers):
    return [n for n in ast.walk(node) if _is_assertion(n, helpers) and n.lineno > after_line]


def _region_compiles(text, is_async):
    flags = ast.PyCF_ALLOW_TOP_LEVEL_AWAIT if is_async else 0
    try:
        compile(text, '<snippet>', 'exec', flags=flags | ast.PyCF_ONLY_AST)
        return None
    except SyntaxError as e:
        return f'{e.msg} (line {e.lineno} of the snippet)'


def _future_bindings(func_node, region):
    """Names bound inside the region by `name = await <...>.future()`."""
    out = []
    for n in ast.walk(func_node):
        if not isinstance(n, ast.Assign) or not (region.start < n.lineno < region.end):
            continue
        if isinstance(n.value, ast.Await) and isinstance(n.value.value, ast.Call) \
                and _call_name(n.value.value) == 'future':
            out += [t.id for t in n.targets if isinstance(t, ast.Name)]
    return out


def _derived(func_node, after_line, name):
    """Names assigned after after_line from an expression that reads `name` (one data-flow step, transitive)."""
    out, changed = {name}, True
    while changed:
        changed = False
        for n in ast.walk(func_node):
            if isinstance(n, (ast.Assign, ast.AnnAssign)) and n.lineno > after_line and n.value is not None:
                reads = {x.id for x in ast.walk(n.value) if isinstance(x, ast.Name)}
                if reads & out:
                    targets = n.targets if isinstance(n, ast.Assign) else [n.target]
                    for t in targets:
                        for x in ast.walk(t):
                            if isinstance(x, ast.Name) and x.id not in out:
                                out.add(x.id)
                                changed = True
    return out - {name}


def lint(scan=None):
    files, snippets = scan or snippet_scan.scan_tier()
    errors, warnings, notes = [], [], []
    used_allow = defaultdict(set)

    def err(f, line, rule, message):
        errors.append(f'{f.rel}:{line}: {rule} {message}')

    for f in files:
        errors += [f'{p.file}:{p.line}: M1/M2/M3 {p.message}' for p in f.problems]
        warnings += [str(w) for w in f.warnings]
        support = _support_names(f)
        helpers = _asserting_helpers(f)
        lines = f.lines
        for n in ast.walk(f.tree):
            if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute) and n.func.attr in ('skip', 'xfail') \
                    and _root(n.func) == 'pytest':
                err(f, n.lineno, 'H4', 'pytest.skip() or pytest.xfail() is not allowed in the live tier')
        for func in f.funcs.values():
            for mark in func.skip_marks:
                err(f, func.start, 'H4', f'{mark} on {func.name} is not allowed in the live tier')
        for region in f.regions:
            key = (f.docset, region.id)
            visible = region.visible_lines(lines)
            if not any(text.strip() for _, text in visible):
                err(f, region.start, 'M5', f'snippet "{region.id}" is empty')
            for hide, show in region.hidden:
                size = (show or region.end) - hide - 1
                if size > MAX_HIDDEN_LINES:
                    if key in LONG_HIDDEN_BLOCKS:
                        used_allow['LONG_HIDDEN_BLOCKS'].add(key)
                    else:
                        err(f, hide, 'M3', f'hidden block of "{region.id}" has {size} lines (max {MAX_HIDDEN_LINES})')
                if not any(lines[i - 1].strip() and not lines[i - 1].strip().startswith('#')
                           for i in range(hide + 1, show or region.end)):
                    err(f, hide, 'M3', f'hidden block of "{region.id}" holds no code')
            visible_set = {n for n, _ in visible}
            # Sample data constants of a shared module (UPPER_CASE, for example FIXTURE) may appear in a sample.
            sample_data = {n for n in support if f.imports[n][0].startswith('shared.') and n.isupper()}
            forbidden = TEST_ONLY_NAMES | (support - sample_data)
            for n in ast.walk(f.tree):
                line = getattr(n, 'lineno', None)
                if line not in visible_set:
                    continue
                if isinstance(n, ast.Assert):
                    err(f, line, 'M6', f'assert statement inside snippet "{region.id}"')
                elif isinstance(n, ast.Name) and n.id in forbidden:
                    err(f, line, 'M6', f'test-only name "{n.id}" inside snippet "{region.id}"')
                elif isinstance(n, (ast.Try, getattr(ast, 'TryStar', ast.Try))) or (
                        isinstance(n, ast.Attribute) and n.attr == 'exception' and _root(n) == 'logging') or (
                        isinstance(n, ast.Name) and n.id == 'traceback'):
                    if key in ERROR_HANDLING_SNIPPETS:
                        used_allow['ERROR_HANDLING_SNIPPETS'].add(key)
                    else:
                        err(f, line, 'M7', f'error handling inside snippet "{region.id}" (not in '
                                           'ERROR_HANDLING_SNIPPETS)')
            text = '\n'.join(textwrap.dedent('\n'.join(t for _, t in visible)).split('\n'))
            problem = _region_compiles(text, f.docset == 'asyncio')
            if problem:
                if key in NOT_STANDALONE:
                    used_allow['NOT_STANDALONE'].add(key)
                else:
                    err(f, region.start, 'M8', f'snippet "{region.id}" does not compile on its own: {problem}')
    by_docset = defaultdict(list)
    for s in snippets:
        by_docset[(s.file.docset, s.id)].append(s)
    for (docset, ident), found in sorted(by_docset.items()):
        if len(found) > 1:
            where = ', '.join(f'{s.file.rel}:{s.region.start}' for s in found)
            errors.append(f'{found[0].file.rel}:{found[0].region.start}: M4 snippet id "{ident}" appears '
                          f'{len(found)} times in {docset}/ ({where})')
    for s in snippets:
        f, region = s.file, s.region
        key = (f.docset, s.id)
        if s.owner == 'none':
            err(f, region.start, 'H1', f'snippet "{s.id}" is not inside a test_* function, a helper a test '
                                       'calls, or a @compile_only function')
            continue
        if s.owner == 'compile-only':
            notes.append(f'compile-only: {f.live_rel} {s.id} ({s.func.compile_only})')
            continue
        nested = [n for n in ast.walk(s.test.node if s.test else s.func.node)
                  if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)) and n is not s.func.node]
        helpers = _asserting_helpers(f) | {n.name for n in nested if _first_assertion(n, 0, set()) is not None}
        holder = s.func
        for n in ast.walk(holder.node):
            if isinstance(n, ast.Return) and region.start < n.lineno < region.end:
                kinds = (ast.FunctionDef, ast.AsyncFunctionDef, ast.Lambda)
                inner = [x for x in ast.walk(holder.node) if isinstance(x, kinds) and x is not holder.node
                         if x.lineno <= n.lineno <= getattr(x, 'end_lineno', x.lineno)]
                if not inner:
                    err(f, n.lineno, 'H3', f'return inside snippet "{s.id}" can skip the rest of {holder.name}')
        test = s.test
        escape = next((ESCAPE.match(f.lines[i - 1]) for i in range(test.start, test.end + 1)
                       if ESCAPE.match(f.lines[i - 1])), None)
        if s.owner == 'test':
            asserted = _first_assertion(test.node, region.end, helpers)
        else:
            asserted = _first_assertion(holder.node, region.end, helpers) or _first_assertion(test.node, 0, helpers)
        if asserted is None:
            if escape:
                notes.append(f'asserted-via {escape.group(1)}: {f.live_rel}::{test.name} ({s.id})')
            else:
                err(f, region.end, 'H2', f'no assertion after snippet "{s.id}" in {test.name}')
        if f.docset == 'asyncio':
            bound = _future_bindings(holder.node, region)
            checked = {x.id for node in _assertion_nodes(holder.node, region.end, helpers)
                       for x in ast.walk(node) if isinstance(x, ast.Name)}
            returns = [n for n in ast.walk(holder.node) if isinstance(n, ast.Return) and n.value is not None]
            returned = {x.id for n in returns if n.lineno > region.end for x in ast.walk(n.value)
                        if isinstance(x, ast.Name)}
            checked |= returned  # a helper that returns the envelope leaves the check to its caller
            loose = [b for b in bound if b not in checked and not (_derived(holder.node, region.start, b) & checked)]
            if loose:
                if key in P1_EXEMPT:
                    used_allow['P1_EXEMPT'].add(key)
                else:
                    err(f, region.end, 'P1', f'"{", ".join(loose)}" from await ....future() in snippet "{s.id}" is '
                                             'not checked by an assertion after the end line')
        doc = ast.get_docstring(test.node) or ''
        if s.id not in doc.split('\n\n')[0]:
            warnings.append(f'{f.rel}:{test.start}: {test.name} docstring does not name snippet "{s.id}"')
    for f in files:
        if f.kind == 'sample' and f.regions:
            base = f.path.name

            def names_it(t):
                return any(isinstance(n, ast.Constant) and isinstance(n.value, str) and n.value.endswith(base)
                           for n in ast.walk(t.tree))
            runners = [t for t in files if t.kind == 'test' and t.path.parent == f.path.parent and names_it(t)]
            if not runners:
                err(f, 1, 'H5', f'whole-file sample {base} is not run by a test that names it')
    # parity between the docsets, per page
    pages = defaultdict(lambda: defaultdict(set))
    for s in snippets:
        pages[s.file.path.name][s.file.docset].add(s.id)
    one_sided = 0
    for page, sets in sorted(pages.items()):
        if len(sets) == 2:
            one_sided += len(sets['sync'] ^ sets['asyncio'])
    if one_sided:
        warnings.append(f'parity: {one_sided} snippet ids exist in one docset only for the same page '
                        '(cli.py lint --parity lists them)')
    for name, allowed in (('ERROR_HANDLING_SNIPPETS', ERROR_HANDLING_SNIPPETS), ('LONG_HIDDEN_BLOCKS',
                          LONG_HIDDEN_BLOCKS), ('NOT_STANDALONE', NOT_STANDALONE), ('P1_EXEMPT', P1_EXEMPT)):
        for key in sorted(allowed - used_allow[name]):
            warnings.append(f'allow-list {name}: {key} is not needed any more')
        if used_allow[name]:
            notes.append(f'allow-list {name}: {len(used_allow[name])} entries used')
    return errors, warnings, notes, len(files), len(snippets)


def parity():
    files, snippets = snippet_scan.scan_tier()
    pages = defaultdict(lambda: defaultdict(set))
    for s in snippets:
        pages[s.file.path.name][s.file.docset].add(s.id)
    out = []
    for page, sets in sorted(pages.items()):
        if len(sets) == 1:
            out.append(f'{page}: {next(iter(sets))} only')
            continue
        for docset, other in (('sync', 'asyncio'), ('asyncio', 'sync')):
            only = sorted(sets[docset] - sets[other])
            if only:
                out.append(f'{page}: {docset} only: {", ".join(only)}')
    return out


def main(argv=()):
    errors, warnings, notes, files, count = lint()
    for e in errors:
        print('lint: ERROR', e)
    for w in warnings:
        print('lint: warning', w)
    if '--notes' in argv:
        for n in notes:
            print('lint: note', n)
    if '--parity' in argv:
        for line in parity():
            print('parity:', line)
    print(f'marker lint: {files} files, {count} snippets, {len(errors)} errors, {len(warnings)} warnings')
    return 1 if errors else 0
