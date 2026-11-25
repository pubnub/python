"""Event collector used by tests outside the snippet markers. Works for PubNub and PubNubAsyncio.

Callbacks of sync clients arrive on SDK threads, so the collector guards its lists with a lock. listen() registers the
listener before subscribe().execute() and then waits for PNConnectedCategory: the sync client
(NativeSubscriptionManager, pubnub/pubnub.py) and the asyncio client (EventEngineSubscriptionManager,
pubnub/pubnub_asyncio.py) both announce it on the first connect. Later subscription changes differ per docset
(the asyncio manager sends PNSubscriptionChangedCategory), so status assertions are written per docset.
"""
import threading

from pubnub.callbacks import SubscribeCallback
from pubnub.enums import PNStatusCategory

from .wait import aeventually, eventually

CONNECT_TIMEOUT = 15


class Collector(SubscribeCallback):
    def __init__(self):
        self._lock = threading.Lock()
        self.categories = []
        self.statuses = []
        self.messages = []
        self.signals = []
        self.presence_events = []
        self.message_actions = []
        self.files = []

    def status(self, pubnub, status):
        with self._lock:
            self.categories.append(status.category)
            self.statuses.append(status)

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

    def observation(self):
        """Short text of what arrived so far, for failure messages."""
        with self._lock:
            return (f'categories={[c.name for c in self.categories]} messages={len(self.messages)} '
                    f'signals={len(self.signals)} presence={len(self.presence_events)} '
                    f'actions={len(self.message_actions)} files={len(self.files)}')

    def _connected(self):
        if PNStatusCategory.PNConnectedCategory not in self.categories:
            raise AssertionError('no PNConnectedCategory yet: ' + self.observation())


def _subscribe(client, channels, groups, presence):
    collector = Collector()
    client.subscribed_by_suite = True
    client.add_listener(collector)
    builder = client.subscribe().channels(list(channels))
    if groups:
        builder = builder.channel_groups(list(groups))
    if presence:
        builder = builder.with_presence()
    builder.execute()
    return collector


def listen(client, *channels, groups=None, presence=False):
    """Sync client: add a collector, subscribe, wait for PNConnectedCategory."""
    collector = _subscribe(client, channels, groups, presence)
    eventually(collector._connected, timeout=CONNECT_TIMEOUT, what='PNConnectedCategory')
    return collector


async def alisten(client, *channels, groups=None, presence=False):
    """Asyncio client: same as listen()."""
    collector = _subscribe(client, channels, groups, presence)
    await aeventually(collector._connected, timeout=CONNECT_TIMEOUT, what='PNConnectedCategory')
    return collector
