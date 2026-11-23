"""Snippet markers, two views of them.

docs_extract(text, ids) is a line-by-line Python copy of extractSnippets() in the docs repo
(src/helper/codeSnippetFetcher.ts): what the docs show for a list of ids. Every offline check that compares sample
text uses it. extractor_fixtures.json holds cases whose expected output came from the docs function itself
(cli.py extractor --regen <docs checkout>), and the lint compares this copy against them.

scan(rel, text) is the strict scanner of the tier: it finds the regions with the exact marker syntax of the docs
extractor for Python files (prefix "# ", with the space) and reports every near miss the extractor would silently
ignore, such as "#snippet.x".
"""
import re
from dataclasses import dataclass, field

DOCS_PREFIXES = ['// ', '# ', '/* ', '<!-- ', '<%-- ']


def _prefix_pattern(prefixes):
    return '|'.join(re.escape(p) for p in prefixes)


def _unindent(lines):
    min_indent = None
    for line in lines:
        if line.strip():
            m = re.search(r'\S', line)
            if m and (min_indent is None or m.start() < min_indent):
                min_indent = m.start()
    if not min_indent:
        return lines
    return [line if not line.strip() else line[min_indent:] for line in lines]


def docs_extract_lines(content, snippet_ids, prefixes=None):
    """Python copy of extractSnippets(content, snippetIds, prefixes). Returns the list of lines."""
    if not snippet_ids:
        return [content]
    prefixes = list(prefixes or DOCS_PREFIXES)
    lines = content.split('\n')
    result = []
    combined = _prefix_pattern(prefixes)
    any_snippet = re.compile(rf'^\s*({combined})\s*snippet\.([a-zA-Z0-9_-]+)\s*$')
    hide = re.compile(rf'^\s*({combined})\s*snippet\.hide\s*$')
    show = re.compile(rf'^\s*({combined})\s*snippet\.show\s*$')
    blueprint = re.compile(rf'^\s*({combined})\s*blueprint\.[a-zA-Z0-9_-]+\s*$')
    for snippet_id in snippet_ids:
        for prefix in prefixes:
            escaped = re.escape(prefix)
            # The docs build the start pattern from the id without escaping it, so it is a regex there too.
            start_pattern = re.compile(rf'^\s*{escaped}\s*snippet\.{snippet_id}\s*$')
            end_pattern = re.compile(rf'^\s*{escaped}\s*snippet\.end\s*$')
            start = -1
            for i, line in enumerate(lines):
                if start_pattern.search(line):
                    start = i + 1
                    break
            if start == -1:
                continue
            end = -1
            for i in range(start, len(lines)):
                line = lines[i]
                if end_pattern.search(line):
                    end = i
                    break
                m = any_snippet.search(line)
                if m:
                    matched = m.group(2)
                    if matched in ('hide', 'show') or matched == snippet_id:
                        continue
                    end = i
                    break
            if end == -1:
                end = len(lines)
            processed, hidden = [], False
            for line in lines[start:end]:
                if hide.search(line):
                    hidden = True
                    continue
                if show.search(line):
                    hidden = False
                    continue
                if blueprint.search(line):
                    continue
                if not hidden:
                    processed.append(line)
            unindented = _unindent(processed)
            if unindented:
                result.extend(unindented)
                break
    return result


def docs_extract(content, snippet_ids, prefixes=None):
    """The text the docs show (lines joined with newlines), '' when nothing is found."""
    return '\n'.join(docs_extract_lines(content, list(snippet_ids), prefixes))


# The strict scanner. Same shapes as the docs extractor with the "# " prefix.
MARKER = re.compile(r'^\s*# \s*snippet\.([A-Za-z0-9_/-]+)\s*$')
LOOSE = re.compile(r'^\s*#\s*(?:snippet\.|end\.snippet)')
LOOSE_TOKEN = re.compile(r'^\s*#\s*snippet\.(\S+)\s*$')


@dataclass
class Region:
    id: str
    start: int  # 1-based line of the start marker
    end: int  # 1-based line of snippet.end, or of the marker that closed the region implicitly
    explicit_end: bool = False
    hidden: list = field(default_factory=list)  # [hide line, show line or None]

    def is_visible(self, line):
        if line <= self.start or line >= self.end:
            return False
        return not any(h <= line <= (s or self.end) for h, s in self.hidden)

    def visible_lines(self, lines):
        """(line number, text) of the lines the docs show (blueprint lines are not used in this tier)."""
        return [(n, lines[n - 1]) for n in range(self.start + 1, self.end) if self.is_visible(n)]


@dataclass
class Issue:
    file: str
    line: int
    message: str

    def __str__(self):
        return f'{self.file}:{self.line}: {self.message}'


def scan(rel, text):
    """Returns (regions, problems, warnings)."""
    regions, problems, warnings = [], [], []
    state = {'open': None, 'hide': None}

    def bad(line, message):
        problems.append(Issue(rel, line, message))

    def close(line, explicit):
        region = state['open']
        if region is None:
            return
        region.end = line
        region.explicit_end = explicit
        if state['hide'] is not None:
            bad(state['hide'][0], f'snippet.hide in "{region.id}" has no snippet.show')
            state['hide'] = None
        regions.append(region)
        state['open'] = None

    lines = text.split('\n')
    for index, raw in enumerate(lines):
        line = index + 1
        m = MARKER.match(raw)
        if not m:
            if LOOSE.match(raw):
                token = LOOSE_TOKEN.match(raw)
                if re.match(r'^\s*#[^ ]', raw):
                    bad(line, 'marker needs a space after "#" ("# snippet.x"), the docs extractor ignores: '
                              f'{raw.strip()}')
                elif token and not re.fullmatch(r'[A-Za-z0-9_-]+', token.group(1)):
                    bad(line, f'snippet id "{token.group(1)}" has characters outside [a-zA-Z0-9_-]')
                else:
                    bad(line, 'marker-like comment is not a valid marker (the docs extractor ignores it): '
                              f'{raw.strip()}')
            continue
        word = m.group(1)
        region = state['open']
        if word == 'end':
            if region is None:
                bad(line, 'snippet.end without an open snippet')
            else:
                close(line, True)
        elif word == 'hide':
            if region is None:
                bad(line, 'snippet.hide outside a snippet')
            elif state['hide'] is not None:
                bad(line, 'snippet.hide inside a hidden block')
            else:
                state['hide'] = [line, None]
                region.hidden.append(state['hide'])
        elif word == 'show':
            if region is None or state['hide'] is None:
                bad(line, 'snippet.show without a matching snippet.hide')
            else:
                state['hide'][1] = line
                state['hide'] = None
        else:
            if '/' in word:
                warnings.append(Issue(rel, line, f'snippet id "{word}" contains "/", the docs extractor never ends '
                                                 'a snippet at it'))
            if region is not None:
                bad(line, f'snippet "{word}" starts inside snippet "{region.id}" (the docs extractor cuts '
                          f'"{region.id}" here)')
                close(line, False)
            state['open'] = Region(word, line, line)
    if state['open'] is not None:
        bad(state['open'].start, f'snippet "{state["open"].id}" has no snippet.end (the docs extractor would run to '
                                 'the end of the file)')
        close(len(lines) + 1, False)
    return regions, problems, warnings
