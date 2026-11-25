"""Scenario data and helpers of the subscribe page, shared by the sync and asyncio tests: literal resource names (NAMES,
read by the janitor through support/resources.py) and the helpers the tests call outside the snippet markers.
Coroutine twins of a sync helper carry an "_async" suffix, and the asyncio tests import them under the sync name.
"""
from pubnub.enums import PNStatusCategory

from support import assertions as a
from support.listen import Collector
from support.wait import eventually
from support.listen import Collector
from support.wait import aeventually

NAMES = [
    'awesome_channel_group',
    'bar',
    'cg_1',
    'channelGroupName',
    'channelMetadata',
    'group-test',
    'grouped_channel',
    'grouped_one',
    'grouped_two',
    'my_channel1',
    'my_channel2',
    'my_group1',
    'my_group2',
    'user_metadata',
]


def attach(client):
    """Add a collector to a client without subscribing. The docs code does the subscribing."""
    collector = Collector()
    client.subscribed_by_suite = True
    client.add_listener(collector)
    return collector


def connected(collector):
    eventually(lambda: a.ok(PNStatusCategory.PNConnectedCategory in collector.categories, 'not connected yet'),
               what='PNConnectedCategory')


def texts(collector):
    return [m.message for m in collector.messages]


class AppContextCollector(Collector):
    """Collector that also keeps App Context events."""
    def __init__(self):
        super().__init__()
        self.channel_events = []
        self.uuid_events = []

    def channel(self, pubnub, channel):
        with self._lock:
            self.channel_events.append(channel)

    def uuid(self, pubnub, uuid):
        with self._lock:
            self.uuid_events.append(uuid)


class Printed:
    """Everything the docs listeners printed so far. Callbacks run on SDK threads, capsys sees their output."""

    def __init__(self, capsys):
        self._capsys = capsys
        self._parts = []

    def text(self):
        self._parts.append(self._capsys.readouterr().out)
        return ''.join(self._parts)


class StatusCollector(Collector):
    """Collector that keeps the status objects, not only their categories."""

    def __init__(self):
        super().__init__()
        self.statuses = []

    def status(self, pubnub, status):
        super().status(pubnub, status)
        with self._lock:
            self.statuses.append(status)


def attach_status(client):
    collector = StatusCollector()
    client.subscribed_by_suite = True
    client.add_listener(collector)
    return collector


async def connected_async(collector):
    await aeventually(lambda: a.ok(PNStatusCategory.PNConnectedCategory in collector.categories, 'not connected yet'),
                      what='PNConnectedCategory')
