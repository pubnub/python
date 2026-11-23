"""Unsubscribing with the default asyncio client sends a leave request unless suppress_leave_events is set.

The event engine subscription manager used to send it only when presence heartbeats were on, so a default client
stayed an occupant of the channel until the presence timeout. The sync client, the legacy asyncio manager and the
JavaScript SDK all send the leave by default.
"""
import asyncio
from types import SimpleNamespace
from unittest.mock import Mock, patch

import pytest

from pubnub.dtos import UnsubscribeOperation
from pubnub.event_engine.models import events
from pubnub.pubnub_asyncio import PubNubAsyncio
from tests.helper import pnconf_copy as _pnconf_copy


def pnconf_copy():
    config = _pnconf_copy()
    config.enable_subscribe = True
    return config


class FakeLeave:
    """Stands in for the Leave endpoint: records the channels and groups, and answers with an acknowledgement."""

    calls = []

    def __init__(self, pubnub):
        self._channels, self._groups = [], []

    def channels(self, channels):
        self._channels = channels
        return self

    def channel_groups(self, groups):
        self._groups = groups
        return self

    async def future(self):
        FakeLeave.calls.append((self._channels, self._groups))
        return SimpleNamespace(status=SimpleNamespace(category='ack'))


@pytest.fixture(autouse=True)
def fake_leave():
    FakeLeave.calls = []
    with patch('pubnub.pubnub_asyncio.Leave', FakeLeave):
        yield


async def unsubscribe(config, channels=(), groups=()):
    pubnub = PubNubAsyncio(config)
    manager = pubnub._subscription_manager
    manager.presence_engine.trigger = Mock()
    announced = []
    manager._listener_manager.announce_status = announced.append
    manager.adapt_unsubscribe_builder(UnsubscribeOperation(channels=list(channels), channel_groups=list(groups)))
    await asyncio.sleep(0)
    await asyncio.sleep(0)
    await pubnub.stop()
    return manager, announced


@pytest.mark.asyncio
async def test_default_config_sends_leave_for_channels_and_groups():
    manager, announced = await unsubscribe(pnconf_copy(), ['my_channel'], ['my_group'])

    assert FakeLeave.calls == [(['my_channel'], ['my_group'])]
    assert [s.category for s in announced] == ['ack']
    manager.presence_engine.trigger.assert_not_called()


@pytest.mark.asyncio
async def test_presence_channels_are_not_left_twice():
    await unsubscribe(pnconf_copy(), ['my_channel', 'my_channel-pnpres'])

    assert FakeLeave.calls == [(['my_channel'], [])]


@pytest.mark.asyncio
async def test_suppress_leave_events_sends_no_leave():
    config = pnconf_copy()
    config.suppress_leave_events = True

    await unsubscribe(config, ['my_channel'])

    assert FakeLeave.calls == []


@pytest.mark.asyncio
async def test_nothing_to_leave_sends_no_request():
    await unsubscribe(pnconf_copy())

    assert FakeLeave.calls == []


@pytest.mark.asyncio
async def test_with_presence_heartbeat_the_presence_engine_leaves_and_no_second_request_is_sent():
    config = pnconf_copy()
    config.enable_presence_heartbeat = True
    config.set_presence_timeout_with_custom_interval(30, 10)

    manager, _ = await unsubscribe(config, ['my_channel'])

    assert FakeLeave.calls == []
    event = manager.presence_engine.trigger.call_args.kwargs['event']
    assert isinstance(event, events.HeartbeatLeftEvent)
    assert event.channels == ['my_channel']
    assert event.suppress_leave is False
