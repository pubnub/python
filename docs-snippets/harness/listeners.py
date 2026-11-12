"""Event collector used by steps outside the snippet markers. Works for PubNub and PubNubAsyncio."""
import threading

from pubnub.callbacks import SubscribeCallback
from pubnub.enums import PNStatusCategory

from . import assertions
from .wait import aeventually, eventually


class Collector(SubscribeCallback):
    def __init__(self):
        self._lock = threading.Lock()
        self.categories = []
        self.messages = []
        self.signals = []
        self.presence_events = []
        self.message_actions = []
        self.files = []

    def status(self, pubnub, status):
        with self._lock:
            self.categories.append(status.category)

    def message(self, pubnub, message):
        with self._lock:
            self.messages.append(message)

    def signal(self, pubnub, signal):
        with self._lock:
            self.signals.append(signal)

    def presence(self, pubnub, presence):
        with self._lock:
            self.presence_events.append(presence)

    def message_action(self, pubnub, message_action):
        with self._lock:
            self.message_actions.append(message_action)

    def file(self, pubnub, file_message):
        with self._lock:
            self.files.append(file_message)

    def _connected(self):
        assertions.ok(PNStatusCategory.PNConnectedCategory in self.categories, 'no PNConnectedCategory yet')


def listen(client, *channels, groups=None, presence=False):
    """Sync client: add a collector, subscribe, wait for PNConnectedCategory."""
    collector = Collector()
    client.subscribed_by_suite = True
    client.add_listener(collector)
    builder = client.subscribe().channels(list(channels))
    if groups:
        builder = builder.channel_groups(list(groups))
    if presence:
        builder = builder.with_presence()
    builder.execute()
    eventually(collector._connected, timeout=15, what='PNConnectedCategory')
    return collector


async def alisten(client, *channels, groups=None, presence=False):
    """Asyncio client: same as listen()."""
    collector = Collector()
    client.subscribed_by_suite = True
    client.add_listener(collector)
    builder = client.subscribe().channels(list(channels))
    if groups:
        builder = builder.channel_groups(list(groups))
    if presence:
        builder = builder.with_presence()
    builder.execute()
    await aeventually(collector._connected, timeout=15, what='PNConnectedCategory')
    return collector
