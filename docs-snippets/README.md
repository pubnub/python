# Live docs snippet tests

These tests run the code samples of the Python and asyncio SDK docs against the real PubNub service. They check that each sample does what its docs page says.

## Why they exist

A mocked test never runs the docs code and never talks to the service, so it cannot find a wrong docs sample. The existing tests in `tests/` check request shape against recorded cassettes. This suite checks what the service does.

## Layout

| Path | Purpose |
| :-- | :-- |
| `sync/` | One module per docs page for the sync `PubNub` client (threads and callbacks) |
| `asyncio/` | The same pages for `PubNubAsyncio` |
| `harness/` | Key loader, staging, marker lint, manifest, janitor, reporter, `eventually` |
| `selftest/` | Dry checks of the harness itself |
| `coverage.json` | Generated manifest, one entry per snippet id |
| `.run/`, `report/` | Git-ignored output |

The `asyncio/` folder has no `__init__.py` on purpose, so it can never shadow the standard library module.

## How a step is written

A step is a test function. The docs code sits between `# snippet.<id>` and `# snippet.end` inside the step body. Client setup and every assertion sit outside the markers. A marker lint enforces it.

```python
@step('signal_message', role='open')
def test_signal(clients):
    pubnub = clients.sync('open', 'signaler')
    seen = listen(clients.sync('open', 'subscriber'), names.with_suffix('my_channel'))

    # snippet.signal_message
    envelope = pubnub.signal() \
        .channel("my_channel") \
        .message("typing_on") \
        .sync()
    # snippet.end

    a.timetoken(envelope.result.timetoken)
    eventually(lambda: a.eq([s.message for s in seen.signals], ['typing_on']))
```

Docs pages embed the region with `EmbeddedCode` and `snippets={['signal_message']}`. The extractor removes the common indentation.

## What a run does

| Stage | What happens |
| :-- | :-- |
| 1. Load keys | The loader reads the env names below and prints `set` or `missing` per role. It never falls back to demo keys |
| 2. Stage | The suite is copied to `.run/<runId>/`. Registered names get the run suffix and every marker line is instrumented in place, so line numbers never move |
| 3. Steps | Each step runs its snippet, then asserts the effect through the service |
| 4. Honesty | A step fails when a snippet did not reach its `snippet.end` line or when no assertion ran after it started |
| 5. Janitor | Revokes application-level Access Manager (v2/v3) grants and removes leftovers older than six hours |
| 6. Report | `report/<shard>/run.json` and `summary.md`, with every key and token masked |

## Run it locally

You need Python 3.9 or later, the dev requirements (`pip install -r requirements-dev.txt`) and your own keysets. The suite imports `pubnub` from this checkout. Run from `docs-snippets/`.

```bash
cp .env.example .env.local        # fill in your keys, never commit this file
python -u -m harness.cli env      # prints set or missing per role
python -u -m harness.cli dry      # no network: compile, selftest, marker lint, manifest check
python -u -m harness.cli run      # all shards
python -u -m harness.cli run --shard open
python -u -m harness.cli manifest [--check]
python -u -m harness.cli janitor
```

## Keys

| Role | Env names | Used for |
| :-- | :-- | :-- |
| `open` | `PUBLISH_KEY`, `SUBSCRIBE_KEY` | Publish, subscribe, presence, storage, message actions, App Context, files, push, channel groups, encryption, misc |
| `pam` | `PAM_PUBLISH_KEY`, `PAM_SUBSCRIBE_KEY`, `PAM_SECRET_KEY` | Access Manager (v2/v3) samples and the 403 branches |

The names differ from the `PN_KEY_*` names of the existing tests on purpose, so the suite never reads those keys by accident. Real env vars win over the env file (`DOCS_SNIPPETS_ENV_FILE`, default `docs-snippets/.env.local`).

The Python SDK has no DataSync API, so there is no `datasync` role.

In CI the workflow [`docs-snippets.yml`](../.github/workflows/docs-snippets.yml) maps the `SDK_DOCS_OPEN_*` and `SDK_DOCS_PAM_*` secrets onto these names on the shard steps only. Without a GitHub Environment that has required reviewers, anyone with push access can read these secrets through a pull request.

## Rules

| Rule | Why |
| :-- | :-- |
| No skips, no `xfail`, no `-k` in CI | Every run must run all valid tests. A missing key fails the run with its exact name |
| Samples that cannot run are `compile_only` or `stub` with a reason in `coverage.json` | They are listed honestly, never skipped silently |
| Never weaken an assertion | Waiting longer with `eventually` is fine. Loosening a check is not |
| No fixed sleeps | Use `eventually(fn, timeout=15, interval=0.5)` for every read after a write |
| Names carry the run suffix and the marker `dsn` | Parallel and repeated runs never collide, and the janitor can tell leftovers apart |
| Assertions sit outside the markers | The region stays byte for byte what the docs show |
| Keys and tokens never reach output | The reporter masks values, URL-encoded forms and key shapes, and a self-test proves it |

## Mutation check

`DOCS_SNIPPETS_MUTATE=<snippet id> python -u -m harness.cli run --shard open` makes the named step throw at its start marker. That step must fail. It is refused in CI.
