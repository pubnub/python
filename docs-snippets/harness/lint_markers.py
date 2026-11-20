"""Marker lint. Fails on: unclosed or implicit-ended regions, duplicate ids, a marker outside a registered step,
a step whose ids differ from the markers in its body, and assertions inside a visible region."""
import re
import sys
from collections import Counter

from . import markers as mk
from . import registry

# Calls and statements that belong outside the markers (hidden lines are allowed)
FORBIDDEN = re.compile(
    r'(^|\W)(assert\b|ok\(|eq\(|contains\(|not_contains\(|timetoken\(|raises\(|eventually\(|aeventually\(|__snip__)')


def lint():
    problems = []
    entries = registry.scan()
    seen = Counter()
    for entry in entries:
        for i in entry.ids:
            seen[(entry.docset, i)] += 1
    for (docset, i), n in seen.items():
        if n > 1:
            problems.append(f'{docset}: snippet id {i!r} is registered {n} times')

    on_disk = {str(p.relative_to(registry.ROOT)) for d in registry.DOCSETS
               for p in (registry.ROOT / d).glob('*.py') if not p.name.startswith('_')}
    files = sorted({e.file for e in entries} | on_disk)
    for rel in files:
        text = (registry.ROOT / rel).read_text()
        regions = mk.regions(text)
        file_entries = [e for e in entries if e.file == rel]
        for r in regions:
            if not r.end:
                problems.append(f'{rel}:{r.start}: snippet {r.id!r} has no snippet.end')
            owner = [e for e in file_entries if e.first <= r.start and r.end <= e.last]
            if not owner:
                problems.append(f'{rel}:{r.start}: snippet {r.id!r} is not inside a registered step')
            elif r.id not in owner[0].ids:
                problems.append(f'{rel}:{r.start}: snippet {r.id!r} is not listed in {owner[0].func}')
            for n, line in r.visible:
                if FORBIDDEN.search(line):
                    problems.append(f'{rel}:{n}: assertion, helper or recorder call inside snippet {r.id!r}')
        for e in file_entries:
            inside = sorted(r.id for r in regions if e.first <= r.start and r.end <= e.last)
            if inside != sorted(e.ids):
                problems.append(f'{rel}: {e.func} lists {sorted(e.ids)} but its body has {inside}')
    ids = Counter((e.docset, i) for e in entries for i in e.ids)
    return problems, len(entries), sum(ids.values())


def main():
    problems, steps, snippets = lint()
    for p in problems:
        print('lint:', p)
    print(f'marker lint: {steps} entries, {snippets} snippet ids, {len(problems)} problems')
    return 1 if problems else 0


if __name__ == '__main__':
    sys.exit(main())
