"""Per step record: which snippet regions started and ended, how many assertions ran. Installed as builtin __snip__."""
import builtins
import threading

_local = threading.local()
_current = None


class Record:
    def __init__(self, name, snippets):
        self.name = name
        self.snippets = list(snippets)
        self.started = []
        self.ended = []
        self.assertions = 0
        self.after_snippet_assertions = 0


def begin(name, snippets):
    global _current
    _current = Record(name, snippets)
    return _current


def current():
    if _current is None:
        raise RuntimeError('assertion used outside a step')
    return _current


def finish():
    global _current
    rec, _current = _current, None
    return rec


class _Snip:
    """Staged copies call __snip__.start(id) and __snip__.end(id) on the marker lines."""

    def start(self, snippet_id):
        import os
        if os.environ.get('DOCS_SNIPPETS_MUTATE') == snippet_id:
            raise RuntimeError(f'mutation: {snippet_id} was made to fail on purpose')
        current().started.append(snippet_id)

    def end(self, snippet_id):
        current().ended.append(snippet_id)


def install():
    builtins.__snip__ = _Snip()
