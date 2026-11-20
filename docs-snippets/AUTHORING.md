# Authoring a page module

Read `README.md` and `sync/publish.py` (the template) first. This page lists the rules for adding a page.

## Files

* `sync/<page>.py` and, where the asyncio docs have the page, `asyncio/<page>.py`. Page names follow the new docs names: `publish`, `subscribe`, `presence`, `message_persistence`, `message_actions`, `channel_groups`, `file_sharing`, `mobile_push`, `encryption`, `misc`, `configuration`, `access_manager`, `objects`.
* One step per operation. A step lists the snippet ids it contains: `@step('id_a', 'id_b', role='open')`. A step has a timeout (default 120 s, `timeout=` to change).
* Snippet ids are snake_case: `<operation>_<variant>`, for example `fetch_history_builder`, `fetch_history_named`. Builder pattern and Named Arguments are different code paths, so both get a snippet and the same step covers both when one result proves both.
* Do not edit anything outside your own page modules. Needed harness changes go into your report.

## What goes between the markers

* Only what a reader should copy: the call, and the lines that use its result. No `main()`, no `PNConfiguration`, no `os.getenv(..., 'demo')`, no imports that the page's other code does not need. The variable `pubnub` (and `pubnub_a`, `pubnub_b` only when the docs example needs a second client) already exists. Imports that the sample needs go in `# snippet.hide` ... `# snippet.show` lines or, if a reader needs to see them, inside the region.
* Start from the code in the current docs page (`docs/sdks/python/api-reference/*.md` and `docs/sdks/asyncio/api-reference/*.md` in `/Users/mateusz.wiktor/repos/documentation`, read only). Keep its idioms and literal names (`my_channel`, `ch1`, ...). Do not invent a new style, but fix code that is wrong. Report each docs claim the live service or the SDK source contradicts.
* Literal channel, group, user and file names inside a region are rewritten by staging to carry the run suffix. The names registered globally are in `harness/names.py` (`REGISTERED`). A literal that is not registered is not rewritten, so for your own names add a module-level list `REGISTERED_NAMES = ['name', ...]` near the top of your module. Outside the markers write `names.with_suffix('my_channel')` to get the same value the region uses.
* The extractor removes the common indentation. A `print()` of the result is fine. `pubnub.publish()` style calls stay on their own lines.
* Asyncio samples use `await ... .future()` for builders (the asyncio SDK has no `.sync()`). `unsubscribe_all()` is not awaited.

## What goes outside the markers

* Client creation with `clients.sync(role, 'name')` or `aclients.asyncio(role, 'name')`, listeners (`harness.listeners.listen / alisten`), seeding and every assertion.
* Assertions use `harness.assertions` (`ok`, `eq`, `contains`, `not_contains`, `timetoken`, `raises`). Reads of eventually consistent data use `eventually` (`aeventually` in asyncio). No fixed sleeps. Prove the effect through a second client, a listener or a read back, not through the response of the call alone. Do not repeat what `tests/` (cassettes) already checks.
* Never weaken an assertion to make a step pass. A failure the service causes is a finding for the report.
* Clean up what you create (channel groups, App Context objects, files, messages) in a `finally` or fixture, and register leftovers with `world.record(kind, name)` where the janitor knows the kind.
* Check return types and attribute names in the SDK source under `/Users/mateusz.wiktor/repos/python/pubnub/` before asserting. Cite nothing from memory.

## Blocks that cannot run

* Signature blocks: keep them out of the suite for now and list them in the report (a drift test comes later).
* Response blocks (JSON): assert the keys at runtime inside the step that makes the call, treat values such as timetokens as illustrative.
* A sample that cannot run in CI (push delivery, a host with no network) is registered with `@compile_only(...)` or `@stub(...)` and a reason, in a function that is never collected (its name must not start with `test_`). Never use skip, skipif or xfail.

## Checks to run

From `docs-snippets/`, with `PY=/tmp/pyvenv-docs/bin/python`:

```bash
$PY -m harness.cli lint
$PY -m harness.cli manifest            # regenerates coverage.json, the lead merges it, do not commit
$PY -m flake8 . --ignore F811,E402 --max-line-length 120 --exclude .run
$PY -u -m harness.cli run --shard open -k "<your module name>"     # or --shard pam
```

Live runs are shared with other people working at the same time, so keep each run small (your modules only). The run prints key status as set or missing and nothing else. Never print, log or open any env value or file.
