# PubNub Python SDK

[![Build Status](https://app.travis-ci.com/pubnub/python.svg?branch=master)](https://app.travis-ci.com/pubnub/python)
[![PyPI](https://img.shields.io/pypi/v/pubnub.svg)](https://pypi.python.org/pypi/pubnub/)
[![PyPI](https://img.shields.io/pypi/pyversions/pubnub.svg)](https://pypi.python.org/pypi/pubnub/)
[![Docs](https://img.shields.io/badge/docs-online-blue.svg)](https://www.pubnub.com/docs/python/pubnub-python-sdk-v4)

This is the official PubNub Python SDK repository.

**Note:** Python SDK version 5.0 no longer supports Python 2.7, Twisted or Tornado, if you still require support for these please use SDK version 4.8.1

PubNub takes care of the infrastructure and APIs needed for the realtime communication layer of your application. Work on your app's logic and let PubNub handle sending and receiving data across the world in less than 100ms.

## Get keys

You will need the publish and subscribe keys to authenticate your app. Get your keys from the [Admin Portal](https://dashboard.pubnub.com/login).

## Configure PubNub

1. Integrate the Python SDK into your project using `pip`:

    ```bash
    pip install pubnub
    ```

2. Configure your keys:

    ```python
    pnconfig = PNConfiguration()

    pnconfig.subscribe_key = 'mySubscribeKey'
    pnconfig.publish_key = 'myPublishKey'
    pnconfig.uuid = 'myUniqueUUID'
    pubnub = PubNub(pnconfig)
    ```

## Add event listeners

```python
class SubscribeHandler(SubscribeCallback):
  def status(self, pubnub, event):
    print("Is there an error? ", event.is_error())
    print("Status value for category: %s" % event.category)
    print("Status value for error_data: %s" % event.error_data)
    print("Status value for error: %s" % event.error)
    print("Status value for status_code: %s" % event.status_code)
    print("Status value for operation: %s" % event.operation)
    print("Status value for tls_enabled: %s" % event.tls_enabled)
    print("Status value for uuid: %s" % event.uuid)
    print("Status value for auth_key: %s" % event.auth_key)
    print("Status value for origin: %s" % event.origin)
    print("Status value for client_request: %s" % event.client_request)
    print("Status value for client_response: %s" % event.client_response)
    print("Status value for original_response: %s" % event.original_response)
    print("Status value for affected_channels: %s" % event.affected_channels)
    print("Status value for affected_groups: %s" % event.affected_groups)

  def presence(self, pubnub, presence):
      pass  # Handle incoming presence data

  def message(self, pubnub, message):
      pass  # Handle incoming messages

  def signal(self, pubnub, signal):
      pass # Handle incoming signals

pubnub.add_listener(SubscribeHandler())
```

## Publish/subscribe

```python
def my_publish_callback(envelope, status):
  if status.is_error():
    ... #handle error here
  else:
    ... #handle result here

pubnub.publish().channel('my_channel').message('Hello world!').pn_async(my_publish_callback)

pubnub.subscribe().channels('my_channel').execute()
```

## Documentation

* [Build your first realtime Python app with PubNub](https://www.pubnub.com/docs/general/basics/set-up-your-account)
* [API reference for Python](https://www.pubnub.com/docs/sdks/python)

## Support

If you **need help** or have a **general question**, contact support@pubnub.com.
