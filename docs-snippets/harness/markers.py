"""Snippet marker parser. Follows the docs extractor (src/helper/codeSnippetFetcher.ts in the docs repo)."""
import re
from dataclasses import dataclass, field

MARKER = re.compile(r'^(\s*)#\s*snippet\.([a-zA-Z0-9_-]+)\s*$')


@dataclass
class Region:
    id: str
    start: int  # 1-based line of the start marker
    end: int  # 1-based line of the end marker, 0 if missing
    visible: list = field(default_factory=list)  # (line_no, text) of lines the docs show
    hidden: list = field(default_factory=list)  # (line_no, text) between hide and show


@dataclass
class Marker:
    line: int
    kind: str  # 'start' | 'end' | 'hide' | 'show'
    id: str
    indent: str


def markers(text):
    out = []
    for i, line in enumerate(text.splitlines(), 1):
        m = MARKER.match(line)
        if not m:
            continue
        name = m.group(2)
        kind = name if name in ('end', 'hide', 'show') else 'start'
        out.append(Marker(i, kind, name if kind == 'start' else '', m.group(1)))
    return out


def regions(text):
    lines = text.splitlines()
    result, cur, hiding = [], None, False
    for mk in markers(text):
        if mk.kind == 'start':
            if cur is not None:  # the docs extractor ends a region at the next start. Lint reports it
                cur.end = 0
                result.append(cur)
            cur, hiding = Region(mk.id, mk.line, 0), False
        elif mk.kind == 'end' and cur is not None:
            cur.end = mk.line
            result.append(cur)
            cur = None
        elif mk.kind == 'hide':
            hiding = True
        elif mk.kind == 'show':
            hiding = False
        if cur is not None and mk.kind in ('hide', 'show'):
            pass
    if cur is not None:
        result.append(cur)
    # fill body lines
    for r in result:
        stop = r.end or len(lines) + 1
        hiding = False
        for n in range(r.start + 1, stop):
            text_line = lines[n - 1]
            m = MARKER.match(text_line)
            if m and m.group(2) == 'hide':
                hiding = True
                continue
            if m and m.group(2) == 'show':
                hiding = False
                continue
            (r.hidden if hiding else r.visible).append((n, text_line))
    return result
