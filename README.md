# PubNub Python SDK

[![PyPI](https://img.shields.io/pypi/v/pubnub.svg)](https://pypi.org/project/pubnub/)

PubNub provides global infrastructure for real-time, interactive applications.

Publish and receive messages in Python. Use this SDK for Python server, CLI, desktop, IoT, and Asyncio applications.

[Documentation](https://www.pubnub.com/docs/sdks/python) · [API reference](https://www.pubnub.com/docs/sdks/python/api-reference/publish-and-subscribe) · [Changelog](https://www.pubnub.com/docs/sdks/python/changelog) · [Support](https://support.pubnub.com/)

## Requirements

| Requirement | Supported version or setup |
| --- | --- |
| Python | [Python 3.9 or later](https://www.pubnub.com/docs/sdks/python) |
| Supported Python versions | [Python 3.9–3.13 and supported operating systems](https://www.pubnub.com/docs/sdks/python/platform-support) |
| pip | Install the package into the same Python environment used to run the application. A virtual environment is recommended. |

## Installation

From the project or active virtual environment:

```sh
pip install pubnub
```

For other installation methods, see [environment setup](https://www.pubnub.com/docs/sdks/python).

## Quickstart

This example runs in Python 3.9 or later. It subscribes to `hello_world`, publishes one message, and prints the received text.

### Get your keys

1. Open the [PubNub Admin Portal](https://admin.pubnub.com/).
2. Create an app and a keyset for development, or select an existing development keyset.
3. Copy its publish key and subscribe key.

If Access Manager is enabled, obtain a token from your trusted backend and call `pubnub.set_token(token)`. Keep the secret key on the backend.

### Send and receive a message

Create `app.py` in the project directory and add:

Replace the key placeholders. Use a User ID that identifies the user or device in your app.

```python
from threading import Event

from pubnub.callbacks import SubscribeCallback
from pubnub.enums import PNStatusCategory
from pubnub.pnconfiguration import PNConfiguration
from pubnub.pubnub import PubNub


class Listener(SubscribeCallback):
    def __init__(self):
        self.connected = Event()
        self.received = Event()

    def status(self, pubnub, status):
        if status.category == PNStatusCategory.PNConnectedCategory:
            self.connected.set()

    def message(self, pubnub, message):
        print(message.message)
        self.received.set()

    def presence(self, pubnub, presence):
        pass


config = PNConfiguration()
config.subscribe_key = "YOUR_SUBSCRIBE_KEY"
config.publish_key = "YOUR_PUBLISH_KEY"
config.user_id = "hello-world-user"

pubnub = PubNub(config)
listener = Listener()
pubnub.add_listener(listener)

try:
    pubnub.subscribe().channels("hello_world").execute()

    if not listener.connected.wait(timeout=10):
        raise TimeoutError("Timed out waiting for the subscription to connect")

    pubnub.publish().channel("hello_world").message("Hello world").sync()

    if not listener.received.wait(timeout=10):
        raise TimeoutError("Timed out waiting for the message")
finally:
    pubnub.unsubscribe().channels("hello_world").execute()
    pubnub.remove_listener(listener)
    pubnub.stop()
```

### Run the example

```sh
python app.py
```

The terminal should show:

```
Hello world
```

The example unsubscribes from `hello_world`, removes its listener with `pubnub.remove_listener(listener)`, and calls `pubnub.stop()` before exit.

For a complete application, see the [getting started guide](https://www.pubnub.com/docs/sdks/python).

## Next steps

| Task | Documentation |
| --- | --- |
| Configure the client | [Configuration](https://www.pubnub.com/docs/sdks/python/api-reference/configuration) |
| Work with subscriptions and messages | [Publish & Subscribe](https://www.pubnub.com/docs/sdks/python/api-reference/publish-and-subscribe) |
| Check channel occupancy | [Presence](https://www.pubnub.com/docs/sdks/python/api-reference/presence) |
| Read message history | [Message Persistence](https://www.pubnub.com/docs/sdks/python/api-reference/storage-and-playback) |

## Build with an AI coding assistant

The [PubNub MCP server](https://www.pubnub.com/docs/ai/pubnub-mcp-server) gives an AI coding assistant access to PubNub SDK documentation and PubNub APIs. Connect the assistant to the hosted server at `https://mcp.pubnub.com`, or run `npx @pubnub/mcp@latest` locally.

The [server repository](https://github.com/pubnub/pubnub-mcp-server) has setup steps for VS Code, Cursor, Claude Code, Claude Desktop, Codex, Gemini CLI, and OpenCode.

## Before production

Use [Access Manager](https://www.pubnub.com/docs/sdks/python/api-reference/access-manager) to grant each client the permissions it needs. Keep the secret key on your backend. Never include it in a distributed client.

Reuse the PubNub client for the application/service lifetime. Unsubscribe streams that are no longer required, remove listeners with `pubnub.remove_listener(listener)`, and call `pubnub.stop()` when the client is shutting down.

Live delivery through PubNub SDKs is at-most-once. A subscriber can miss messages while disconnected or if its buffer overflows. For longer-gap recovery, see [Message Persistence](https://www.pubnub.com/docs/sdks/python/api-reference/storage-and-playback).

## Troubleshooting

| Symptom | Check |
| --- | --- |
| Python reports `ModuleNotFoundError: No module named 'pubnub'` | Install PubNub into the same Python environment that runs the application and verify Python 3.9+. See the [Python SDK guide](https://www.pubnub.com/docs/sdks/python). |
| A publish succeeds but no message appears | Check the message handler, subscription readiness, keyset, and channel name. |
| The Python process remains active after the application no longer needs PubNub | Unsubscribe active streams, remove listeners, and call `pubnub.stop()` during shutdown. See [Python troubleshooting](https://www.pubnub.com/docs/sdks/python/troubleshoot). |
| Extra clients or duplicate messages during development | For web frameworks and development reloaders, create the PubNub client at application/service scope instead of on every request. Stop the owned client as part of application shutdown. |

For setup help, see [troubleshooting](https://www.pubnub.com/docs/sdks/python/troubleshoot). Check [network status](https://status.pubnub.com/) for service incidents.

## Releases

Read the [changelog](https://www.pubnub.com/docs/sdks/python/changelog) before upgrading.

For a major version change, review the [Python SDK changelog](https://www.pubnub.com/docs/sdks/python/changelog) for breaking changes before upgrading.

## Support and contributions

For setup or account help, contact [PubNub Support](https://support.pubnub.com/).

For a reproducible SDK bug, use [GitHub Issues](https://github.com/pubnub/python/issues). Include the SDK version, runtime, and a small reproduction with credentials removed.

Install the repository development dependencies, run the supported Python test matrix, and include tests for behavioral changes before opening a pull request.

## License

See the [PubNub Software Development Kit License](https://github.com/pubnub/python/blob/master/LICENSE).
