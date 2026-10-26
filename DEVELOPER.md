# Developer guide

## Supported Python versions

Python 3.9–3.13. This matches `python_requires` in `setup.py` and the CI matrix in `.github/workflows/run-tests.yml`.

## Setup

Use a virtual environment, then install the development dependencies from the repository root:

```sh
./scripts/install.sh
```

## Tests

Run the unit, functional, and integrational tests (with coverage):

```sh
python scripts/run-tests.py
```

This runs `py.test tests --cov=pubnub --ignore=tests/manual/`.

## Linting

CI runs flake8 in `.github/workflows/run-validations.yml`. To run the same check locally:

```sh
flake8 --exclude=scripts/,src/,.cache,.git,.idea,.tox,._trial_temp/,venv/ --ignore F811,E402
```

## Pull requests

- Include tests for behavioral changes and keep the test matrix green on all supported Python versions.

## Clients and call styles

`PubNub` (native threads) and `PubNubAsyncio` (`pubnub.pubnub_asyncio`) share the same endpoint builders. The method that finishes the call decides how it runs.

### Native (`threading`)

`PubNub` uses `HttpxRequestHandler` (with HTTP/2 support) by default. A different handler can be passed as `custom_request_handler`, set with `set_request_handler`, or selected with the `PUBNUB_REQUEST_HANDLER` environment variable. A `requests`-based handler is also included.

- `sync()` blocks and returns an `Envelope` (`result` and `status`). If the request fails, it raises the underlying exception.
- `pn_async(callback)` runs the request on a thread and calls `callback(result, status)`. Check `status.is_error()` for failures.

### Asyncio

Create the client with `PubNubAsyncio` and call these inside the event loop:

- `await ....result()` returns the result and raises on failure.
- `await ....future()` returns an `Envelope`. Check `envelope.status.is_error()` for failures.

For more usage, see `tests/integrational/asyncio/test_invocations.py`.

## Daemon mode (native threads)

`config.daemon` defaults to `False`. Threads started by `pn_async()` are then non-daemon, so the interpreter waits for them before exiting. To let the process exit without waiting for in-flight asynchronous requests, set it before making calls:

```python
pnconfig.daemon = True
```

This setting is read when each `pn_async()` request thread is created. It does not affect the subscribe loop or the heartbeat timer, which always run as daemon threads.

## SubscribeListener helpers

`pubnub.pubnub.SubscribeListener` (native) and `pubnub.pubnub_asyncio.SubscribeListener` (asyncio) are helpers that expose connection state and queue incoming events so code (mostly tests) can wait for them. They are documented in their docstrings and used by `examples/native_threads/subscribe.py` and the integrational tests. They are not covered by the public SDK documentation, so prefer `SubscribeCallback` in application code.
