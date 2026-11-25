# Live tier: docs samples against the real service

These tests run the code samples of the Python and asyncio SDK docs against the real PubNub service. Each test checks that its sample does what the docs page says. The docs pages embed the samples straight from these test files, so a sample that is published is a sample that runs.

A mocked test never runs the docs code and never talks to the service, so it cannot find a wrong docs sample. The other tests in `tests/` check request shape against recorded cassettes. This tier checks what the service does.

## Layout

| Path | Purpose |
| :-- | :-- |
| `sync/api_reference/test_<page>.py` | One file per docs page of the sync `PubNub` client. The docs embed these files |
| `asyncio/api_reference/test_<page>.py` | The same pages for `PubNubAsyncio` |
| `shared/<page>.py` | Scenario data per page: the literal resource names (`NAMES`) and the helpers both docsets call outside the markers |
| `support/` | Support package: env and keys, clients, cleanup, waits, janitor, preflight, lint, manifest, groups, docs-check |
| `groups.py` | API groups (data only). One group is one CI job |
| `coverage.json` | Generated manifest, one entry per snippet id per file |
| `snippet-exceptions.json` | Hand-kept list of embeds that are not run and of pages that exist in one docset only, each with a reason |
| `fixtures/` | Files the samples upload |
| `cli.py` | Command line of the tier (`python -u tests/live/cli.py` with no command prints the usage) |
| `.env.example` | Env names. Copy to `.env.local` (git-ignored) |

`sync/` and `asyncio/` have no `__init__.py` on purpose, so `asyncio/` can never shadow the standard library module.

## Groups

`groups.py` splits the test files into API groups. Every test file belongs to exactly one group. An entry can also be a `<file>::<test>` node id that takes one test out of the group that lists its file. Each group lists the keyset roles its tests need.

| Group | Roles | Pages |
| :-- | :-- | :-- |
| `messaging` | `open` | publish, subscribe, subscribe-legacy, presence, channel groups, message persistence, message-persistence-legacy, message actions, file sharing, mobile push |
| `getting-started` | `open`, `pam` | configuration, encryption, misc |
| `app-context` | `open` | App Context (sync only) |
| `access-manager` | `open`, `pam` | access manager, access-manager-legacy, access-manager-v2 |
| `access-manager-application-level` | `pam` | the application level grant of access-manager-v2 (`test_grant_subkey_all`, sync and asyncio) |

The order of the list is the order of the serial CI run. `access-manager-application-level` runs last, because its tests open the whole `pam` keyset for a moment and a downgrade is not guaranteed to apply at once.

## Keys

| Role | Env names | Keyset features |
| :-- | :-- | :-- |
| `open` | `PUBLISH_KEY`, `SUBSCRIBE_KEY` | Message Persistence with Delete-From-History, Presence with a tracking rule on `*`, App Context with user, channel and membership events and referential integrity off, Files, Mobile Push, Stream Controller with wildcard subscribe, no Access Manager |
| `pam` | `PAM_PUBLISH_KEY`, `PAM_SUBSCRIBE_KEY`, `PAM_SECRET_KEY` | Access Manager with token revocation, Message Persistence with Delete-From-History (the janitor needs it), Presence |
| preflight (optional) | `PUBNUB_ADMIN_API_KEY`, `DOCS_SNIPPETS_OPEN_KEYSET_ID`, `DOCS_SNIPPETS_PAM_KEYSET_ID` | Read only Admin API feature check |

Real env vars win over `tests/live/.env.local` (or the file in `LIVE_ENV_FILE`). The loader never falls back to demo keys and prints only `set` or `missing` (`python -u tests/live/cli.py env`).

A full run needs every role. A group run needs the roles of its group. A run narrowed with `-k`, `-m` or file arguments needs the roles of the selected tests, read from `coverage.json`. A missing role stops the run before the first test, with the names of the missing env vars.

## Run it

Python 3.9 or later and the dev requirements (`pip install -r requirements-dev.txt`). The tier imports `pubnub` from this checkout. Run pytest from this folder, because pytest applies `testpaths` only when it runs in its rootdir (from the repository root, `-c tests/live/pytest.ini` alone collects the whole repository).

```bash
python -u tests/live/cli.py lint                 # offline checks, no keys, no network
cd tests/live
python -u -m pytest --collect-only -q --allow-hosts=127.0.0.1,::1   # no keys, no network
python -u -m pytest                              # the whole tier: needs both roles
LIVE_GROUP=messaging python -u -m pytest         # one group
LIVE_JANITOR=off python -u -m pytest -k publish  # one page, without the full cleanup
python -u cli.py janitor                         # cleanup alone
python -u cli.py preflight                       # keyset feature check alone
```

`LIVE_JANITOR=off` and `LIVE_PREFLIGHT=off` skip those steps. Check `gh run list --workflow live-integration.yml --repo pubnub/python` first: the tier uses fixed names on shared keysets, so a local run on the same keysets collides with a CI run.

The tier refuses `python -O` (it strips the `assert` statements), `pytest-rerunfailures` (retries hide real failures) and `skip`, `skipif` or `xfail` marks. Each test has a 120 s timeout. A test that needs more carries `@pytest.mark.timeout(n)`.

## How a test is written

A test is a `test_*` function. The docs sample sits between `# snippet.<id>` and `# snippet.end` inside the test body, with the literal names the docs show. Client setup and every assertion sit outside the markers. The first paragraph of the docstring names the snippet ids.

```python
def test_signal_message(clients):
    """Snippet: signal_message."""
    pubnub = clients.sync('open', 'signaler')
    seen = listen(clients.sync('open', 'subscriber'), 'my_channel')

    # snippet.signal_message
    envelope = pubnub.signal() \
        .channel("my_channel") \
        .message("typing_on") \
        .sync()
    # snippet.end

    a.timetoken(envelope.result.timetoken)
    eventually(lambda: a.eq([s.message for s in seen.signals], ['typing_on']))
```

The docs embed the region with `EmbeddedCode` from `https://raw.githubusercontent.com/pubnub/python/refs/heads/master/tests/live/<docset>/api_reference/test_<page>.py` and `snippets={['signal_message']}`. The docs extractor removes the common indentation. Nothing is staged or rewritten.

What may be inside the snippet region:

* The sample code exactly as the docs page shows it, with the literal resource names of the page.
* Keys on one hidden line between `# snippet.hide` and `# snippet.show`. A hidden block holds at most 3 lines of code and is never published.

What may not be inside the snippet region:

* Assertions, `pytest`, the waits (`eventually`, `settled`, `connected` and the like) or any name imported from `support` or `shared`.
* `try`/`except`, `traceback` or `logging.exception`, unless the purpose of the sample is the error handling the page shows (allow-list `ERROR_HANDLING_SNIPPETS`).
* A `return` of the function that holds the snippet.

The marker lint (`support/lint_markers.py`) enforces these rules and lists them all. In short:

* Marker syntax is `# snippet.<id>` with a space after `#`. The docs extractor ignores `#snippet.x`.
* An id appears once per docset folder, because the docs address a snippet by file and id.
* The visible text compiles on its own (`await` is allowed in asyncio files).
* Every test asserts after each snippet's end line.
* asyncio: `await ....future()` returns an error object instead of raising, so every envelope a snippet binds is checked by an assertion after the end line (rule P1).
* A whole-file sample (a `.py` file under a docset folder that is not `test_*.py`) is run by a test that names it.

A sample that cannot run against the service goes in a function decorated with `@compile_only(reason)` (`support/marks.py`). pytest does not collect it, but the file is imported, so the sample still compiles, and the manifest lists it as compile-only.

Fixtures: `clients` hands out sync clients (`clients.sync('open', 'user')`, `clients.sync('pam', 'admin')`), `aclients` asyncio clients (`aclients.asyncio(...)`). Both stop every client after the test. `support.cleanup.cleanup_after_test(label, fn)` registers a removal that runs after the test body, before the clients stop. Use `eventually()` for a read that must succeed once, `settled()` for a read after a write that must succeed several times in a row (a lagging replica), and `sleep()` only to prove that something does not happen.

## Checks

All of these run offline, without keys or network.

| Command | What it checks |
| :-- | :-- |
| `cli.py lint` | Compiles the tier, runs the marker lint, the lint self-test (broken fixtures, redaction, extractor cases), `manifest --check`, `groups --check`, the shape of `snippet-exceptions.json` and the shape of the resource names |
| `cli.py manifest` | Writes `coverage.json` from the markers. `--check` fails when the file is stale. Never edit it by hand |
| `cli.py groups --check` | Every test file in exactly one group, every listed file and test exists, every role a file uses is in its group, and the workflow `group` input lists `all` and then every group name in order |
| `cli.py docs-check <docs checkout>` | Classifies every `EmbeddedCode` from `pubnub/python` in `docs/sdks/python/` and `docs/sdks/asyncio/` as live, compile-only, exception or NOT COVERED. `--report-only` never fails, `--allow-ref <branch>` accepts a docs preview branch in the URL |
| `cli.py parity` | Snippet ids that exist in one docset only, per page |
| `cli.py extractor --regen <docs checkout>` | Regenerates `support/extractor_fixtures.json` with the docs extractor itself (`npx tsx`), so the self-test can compare the Python copy of the extractor against it |

`snippet-exceptions.json` is hand-kept. `exceptions` lists docs embeds that no test runs, each with a path, optional ids and a reason. `one_sided` lists pages that exist in one docset only, each with a reason. The lint checks the shape and `docs-check` reads the exceptions.

## Cleanup

The tests use the names the docs show, so the names are fixed, shared and persistent. `support/resources.py` and the `NAMES` list of each `shared/<page>.py` list every name the tier uses. The lint fails on a name with a run suffix.

* Janitor (`support/janitor.py`): before and after every run, it cleans exactly the listed names on every role that has keys (history and files of a channel, channel groups, App Context users and channels and their memberships, push devices) and revokes the application-level Access Manager (v2) grant. It never sweeps by name pattern and never lists a keyset. A failed cleanup before the run stops the run. A failed revoke after the run fails it.
* Grant check: when the run uses the `pam` role, the janitor waits until a client without a token is refused on the `pam` keyset again.
* Preflight (`support/preflight.py`): before the first test it names every keyset feature a role lacks, through the Admin API (with `PUBNUB_ADMIN_API_KEY` and the keyset ids) and through live probes on the `open` keyset.
* Per test: the registered cleanups run after the test body. Then the client fixtures unsubscribe and stop every client and send an explicit leave for every channel and group a client was still subscribed to, so a client that stays an occupant never hides the join event of the same user ID from the next test. Helper clients use a short presence timeout for the same reason.
* After the run: a check that no non-daemon thread is left.

## CI

`.github/workflows/live-integration.yml` runs on every non-draft pull request into `master` and on dispatch (inputs `group` and `grep`). There is no schedule. Fork pull requests never get the live jobs.

1. `compat`: compile and `cli.py lint` on Python 3.9 to 3.12.
2. `offline`: compile, `cli.py lint`, Ruff of the tier, a collect without keys or network, and the job matrix from `groups.py` (`cli.py groups --matrix`).
3. `live`: one job per group, one at a time, without stopping at a failed group. After a failure or a cancel, a last step runs `cli.py janitor` so a keyset is never left open.

One live run at a time runs for the whole workflow, because the keysets are shared. `cancel-superseded-live-runs.yml` cancels older runs of the same pull request when it gets a new push. The run logs in GitHub are the only failure signal.

## Add a page

1. Write `sync/api_reference/test_<page>.py` and `asyncio/api_reference/test_<page>.py`, one test per sample or group of samples, with the markers and assertions as above.
2. Put the resource names of the page in `NAMES` of `shared/<page>.py`, with the helpers both docsets call. A coroutine twin of a sync helper carries an `_async` suffix.
3. Add both files to a group in `groups.py`. A new group also needs its name in the `group` input options of the workflow.
4. Run `python -u tests/live/cli.py manifest`, then `cli.py lint` and Ruff (`ruff check tests/live`, configured by the `ruff.toml` of the repository).
5. Run the page live (`python -u -m pytest -k <page>` from `tests/live`).
6. Point the docs `EmbeddedCode` tags at the file and ids, and run `cli.py docs-check <docs checkout>`. A page that exists in one docset only goes in `one_sided` of `snippet-exceptions.json`.
