# Developers manual

## Supported Python versions
We support Python 2.7 and >=3.4

## Supported platforms
We maintain and test our SDK using Travis.CI and Ubuntu.
Windows/MacOS/BSD platforms support was verified only once, after SDK v4.0 release. We did not test the newer releases with these platforms. 

## Event Loop Frameworks
### Native (`threading`)
Native implementation concerns using `requests` library (https://github.com/requests/requests), a wrapper for a lower level urllib3 (https://github.com/shazow/urllib3).
urllib2 is not supported, there is an outline of request handler for it (which doesn't work, just the outline) can be found at (https://github.com/pubnub/python/blob/master/pubnub/request_handlers/urllib2_handler.py).
All listed Python versions are supported. 

#### sync
Synchronous calls can be invoked by using `sync()` call. This will return Envelope object https://github.com/pubnub/python/blob/037a6829c341471c2c78a7a429f02dec671fd791/pubnub/structures.py#L79-L82 which wraps both Result and Status. All exceptions are triggered natively using `raise Exception` syntax. The idea was to use 2 types of final execution methods like in Asyncio/Tornado. These fixes are postponed until next major release (v5.0.0):
- `result()` should return just Response and natively raise an exception if there is one
- `sync()` should return Envelope(as is now), but do not raise any exceptions 
The work on it has been started in branch 'fix-errors-handling', but as were mentioned above, was postponed.

#### async
Asynchronous calls are implemented by using threads (`threading` module https://docs.python.org/3/library/threading.html). The passed-in to async() functinon callback will be called with a response or an error.

### Asyncio
Asyncio library is supported since Python 3.4.
There are 2 types of calls:
- using `result()` - only a result will be returned; in case of exception it will be raised natively
- using `future()` - a wrapper (Envelope) for a result and a status; in case of exception it can be checked using env.is_error()

You can find more examples here https://github.com/pubnub/python/blob/master/tests/integrational/asyncio/test_invocations.py

### Tornado
Tornado supports by Python 2.7 and Python >= 3.3.
There are 2 types of calls:
- using `result()` - only a result will be returned; in case of exception it will be raised natively
- using `future()` - a wrapper (Envelope) for a result and a status; in case of exception it can be checked using env.is_error()

You can find more examples here https://github.com/pubnub/python/blob/master/tests/integrational/tornado/test_invocations.py

### Twisted
Twisted is supported by Python 2.7 only.

## Tests
* Test runner: py.test
* Source code checker: flake

## Crypto library
We have 2 crypto libraries. By default we use PubNubCryptodome. But for some legacy environment such as Google Cloud PubNubCryptoLegacy should be manually configured, see example here https://github.com/pubnub/python/blob/master/examples/native_threads/custom_crypto.py

## Daemon mode with Native SDK
Daemon mode for all requests are disabled by default. This means that all asynchronous requests including will block the main thread until all the children be closed. If SDK user want to use Java-like behaviour when it's up to him to decide should he wait for response completion or continue program execution, he has to explicitly set daemon mode to true:

```python
pubnub.config.daemon = true
```

## SubscribeListener
SubscribeListeners for all implementations are helpers developed to simplify tests behaviour.  They can be used by SDK end-user, but  are not well tested and can't be found in any documentation.
