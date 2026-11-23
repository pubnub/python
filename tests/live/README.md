# Live tier: docs samples against the real service

These tests run the code samples of the Python and asyncio SDK docs against the real PubNub service. They check that each sample does what its docs page says. The design follows the JavaScript live tier (`test/integration/live/` in `pubnub/javascript`).

A mocked test never runs the docs code and never talks to the service, so it cannot find a wrong docs sample. The other tests in `tests/` check request shape against recorded cassettes. This tier checks what the service does.

## Layout

| Path | Purpose |
| :-- | :-- |
| `sync/api_reference/test_<page>.py` | One file per docs page of the sync `PubNub` client. The docs embed these files |
| `asyncio/api_reference/test_<page>.py` | The same pages for `PubNubAsyncio` |
| `shared/<page>.py` | Shared scenario data per page: literal resource names (`NAMES`) and the helpers both docsets call outside the markers |
| `support/` | Shared support package: env and keys, clients, cleanup, waits, janitor, preflight, lint, manifest, groups, docs-check |
| `groups.py` | API groups (data only). One group is one CI job |
| `coverage.json` | Generated manifest, one entry per snippet id per file |
| `snippet-exceptions.json` | Hand-kept list of embeds that are not run, with a reason |
| `port-map.json` | Generated proof that the port from `docs-snippets/` kept every id and step |
| `port-text-changes.md` | Sample text changes of the port, with their approval status (applied 2026-11-23) |
| `fixtures/` | Files the samples upload |
| `.env.example` | Env names. Copy to `.env.local` (git-ignored) |

`sync/` and `asyncio/` have no `__init__.py` on purpose, so `asyncio/` can never shadow the standard library module.

## How a test is written

A test is a `test_*` function. The docs sample sits between `# snippet.<id>` and `# snippet.end` inside the test body, with the literal names the docs show. Client setup and every assertion sit outside the markers. The first docstring paragraph names the snippet ids.

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

The docs embed the region with `EmbeddedCode` from `https://raw.githubusercontent.com/pubnub/python/refs/heads/master/tests/live/<docset>/api_reference/test_<page>.py` and `snippets={['signal_message']}`. The extractor removes the common indentation. Nothing is staged or rewritten.

Rules the marker lint enforces (`support/lint_markers.py` lists them all):

* Marker syntax is `# snippet.<id>` with a space after `#`. The docs extractor ignores `#snippet.x`.
* No assertion, wait or support name inside the visible text. Keys go on one hidden line between `# snippet.hide` and `# snippet.show`.
* Every test asserts after each snippet's end line.
* asyncio: `await ....future()` returns an error object instead of raising, so every envelope a snippet binds is checked by an assertion after the end line (rule P1).
* No `skip`, `skipif` or `xfail`.

Fixtures: `clients` hands out sync clients (`clients.sync('open', 'user')`, `clients.sync('pam', 'admin')`), `aclients` asyncio clients (`aclients.asyncio(...)`). Both stop every client after the test. `support.cleanup.cleanup_after_test(label, fn)` registers a removal that runs after the test body, before the clients stop.

## Keys

| Role | Env names | Keyset features |
| :-- | :-- | :-- |
| `open` | `PUBLISH_KEY`, `SUBSCRIBE_KEY` | Message Persistence with Delete-From-History, Presence with a tracking rule on `*`, App Context with user, channel and membership events and referential integrity off, Files, Mobile Push, Stream Controller with wildcard subscribe, no Access Manager |
| `pam` | `PAM_PUBLISH_KEY`, `PAM_SUBSCRIBE_KEY`, `PAM_SECRET_KEY` | Access Manager with token revocation, Message Persistence with Delete-From-History (the janitor needs it), Presence |
| preflight (optional) | `PUBNUB_ADMIN_API_KEY`, `DOCS_SNIPPETS_OPEN_KEYSET_ID`, `DOCS_SNIPPETS_PAM_KEYSET_ID` | Read only Admin API feature check |

Real env vars win over `tests/live/.env.local` (or the file in `LIVE_ENV_FILE`). The loader never falls back to demo keys and prints only `set` or `missing`.

## Run it

Python 3.9 or later and the dev requirements (`pip install -r requirements-dev.txt`). The tier imports `pubnub` from this checkout. Run pytest from this folder, because pytest applies `testpaths` only when it runs in its rootdir (from the repository root, `-c tests/live/pytest.ini` alone collects the whole repository).

```bash
python -u tests/live/cli.py lint                 # offline: compile, markers, self-test, manifest, groups, port map
cd tests/live
python -u -m pytest --collect-only -q --allow-hosts=127.0.0.1,::1   # no keys, no network
python -u -m pytest                              # the whole tier: needs both roles
LIVE_GROUP=messaging python -u -m pytest         # one group
LIVE_JANITOR=off python -u -m pytest -k publish  # one page, without the full cleanup
python -u cli.py janitor                         # cleanup alone
```

A run does: role check, janitor (cleans every name in `support/resources.py`, revokes the application-level Access Manager (v2) grant), a wait until a client without a token is refused on the `pam` keyset, preflight, the tests, janitor again. Check `gh run list --workflow live-integration.yml --repo pubnub/python` first: a local run on the same keysets collides with a CI run.

## CI

`.github/workflows/live-integration.yml` runs on every non-draft pull request into `master` and on dispatch (inputs `group` and `grep`). No schedule. An offline job runs the lint, flake8 and a collect, and builds the job matrix from `groups.py`. Then one live job per group runs, one at a time. `cancel-superseded-live-runs.yml` cancels older runs of the same pull request.

## Not done yet (plan in the documentation repo, `work/python-sdk-snippet-tests/PORT-PLAN.md`)

* No live run of the new tier yet (plan Phase 5 pilot and Phase 6 page by page). The step bodies are ported mechanically: literal names instead of run suffixes, cleanup registry instead of the ledger. Exact-count assertions on shared names, `settled` reads and the classification of `support/resources.py` by kind come with Phase 6.
* The getting-started pages and the docs repoint (Phase 9). There is no endpoint tier: the real-network tests stay in `tests/` (plan Q4).
