"""Static registry: reads the suite modules with ast, no import, so the dry stage needs no network or keys."""
import ast
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DOCSETS = ('sync', 'asyncio')
DECORATORS = {'step': 'live', 'compile_only': 'compile-only', 'stub': 'stub'}


@dataclass
class Entry:
    docset: str
    file: str  # relative to docs-snippets
    func: str
    first: int
    last: int
    ids: list
    role: str
    mode: str
    reason: str
    is_async: bool


def _literal(node):
    return ast.literal_eval(node)


def scan():
    entries = []
    for docset in DOCSETS:
        for path in sorted((ROOT / docset).glob('*.py')):
            if path.name.startswith('_'):
                continue
            tree = ast.parse(path.read_text(), filename=str(path))
            for node in ast.walk(tree):
                if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    continue
                for deco in node.decorator_list:
                    if isinstance(deco, ast.Call) and isinstance(deco.func, ast.Name) and deco.func.id in DECORATORS:
                        kwargs = {k.arg: _literal(k.value) for k in deco.keywords}
                        entries.append(Entry(
                            docset=docset,
                            file=str(path.relative_to(ROOT)),
                            func=node.name,
                            first=node.lineno,
                            last=node.end_lineno,
                            ids=[_literal(a) for a in deco.args],
                            role=kwargs.get('role', 'open'),
                            mode=DECORATORS[deco.func.id],
                            reason=kwargs.get('reason', ''),
                            is_async=isinstance(node, ast.AsyncFunctionDef),
                        ))
    return entries
