"""Docs page: miscellaneous utility methods (sync). Source: docs/sdks/python/api-reference/misc.md.

The sync page has no Time section, the asyncio page has. The time_get step covers the SDK method for both pages.
"""
import time

from support import assertions as a
from support import cleanup as live_cleanup
from support.listen import listen
from support.wait import eventually


def test_disconnect_method(clients):
    """Snippets: disconnect_method, reconnect_method."""
    pubnub = clients.sync('open', 'subscriber')
    publisher = clients.sync('open', 'publisher')
    channel = 'my_channel'
    seen = listen(pubnub, channel)
    publisher.publish().channel(channel).message('before').sync()
    eventually(lambda: a.eq([m.message for m in seen.messages], ['before'], 'live before disconnect'))
    manager = pubnub._subscription_manager

    # snippet.disconnect_method
    pubnub._subscription_manager.disconnect()
    print("Disconnected from PubNub.")
    # snippet.end
    a.ok(manager._should_stop, 'the manager is stopped')
    publisher.publish().channel(channel).message('while-away').sync()

    # snippet.reconnect_method
    pubnub._subscription_manager.reconnect()
    # snippet.end
    a.ok(not manager._should_stop, 'the manager runs again')
    eventually(lambda: a.eq([m.message for m in seen.messages], ['before', 'while-away'], 'caught up after reconnect'))
    publisher.publish().channel(channel).message('after').sync()
    eventually(lambda: a.eq([m.message for m in seen.messages], ['before', 'while-away', 'after'], 'live again'))


def test_reconnect_documented(clients):
    """Snippet: reconnect_documented. Live since PR 242 added PubNub.reconnect() (it raised AttributeError before)."""
    pubnub = clients.sync('open', 'subscriber')
    publisher = clients.sync('open', 'publisher')
    channel = 'my_channel'
    seen = listen(pubnub, channel)
    publisher.publish().channel(channel).message('before').sync()
    eventually(lambda: a.eq([m.message for m in seen.messages], ['before'], 'live before disconnect'))
    manager = pubnub._subscription_manager
    pubnub.disconnect()
    a.ok(manager._should_stop, 'the manager is stopped')
    publisher.publish().channel(channel).message('while-away').sync()

    # snippet.reconnect_documented
    pubnub.reconnect()
    # snippet.end
    a.ok(not manager._should_stop, 'the manager runs again')
    eventually(lambda: a.eq([m.message for m in seen.messages], ['before', 'while-away'], 'caught up after reconnect'))
    publisher.publish().channel(channel).message('after').sync()
    eventually(lambda: a.eq([m.message for m in seen.messages], ['before', 'while-away', 'after'], 'live again'))


def test_get_subscribed_channels(clients):
    """Snippets: get_subscribed_channels, get_subscribed_channel_groups."""
    pubnub = clients.sync('open', 'subscriber')
    admin = clients.sync('open', 'group_admin')
    channel_a, channel_b = 'ch1', 'ch2'
    group = 'cg1'
    a.eq(pubnub.get_subscribed_channels(), [], 'nothing subscribed yet')
    live_cleanup.record('channel_group', group)
    try:
        admin.add_channel_to_channel_group().channels([channel_b]).channel_group(group).sync()
        listen(pubnub, channel_a, groups=[group])

        # snippet.get_subscribed_channels
        channels = pubnub.get_subscribed_channels()
        # snippet.end
        a.eq(channels, [channel_a])

        # snippet.get_subscribed_channel_groups
        channel_groups = pubnub.get_subscribed_channel_groups()
        # snippet.end
        a.eq(channel_groups, [group])
        pubnub.unsubscribe().channels(channel_a).channel_groups(group).execute()
        eventually(lambda: a.eq(pubnub.get_subscribed_channels(), [], 'channels after unsubscribe'))
        a.eq(pubnub.get_subscribed_channel_groups(), [], 'groups after unsubscribe')
    finally:
        admin.remove_channel_group().channel_group(group).sync()


def test_time_get(clients):
    """Snippet: time_get."""
    pubnub = clients.sync('open', 'timekeeper')

    # snippet.time_get
    envelope = pubnub.time().sync()
    print(f"Current time: {envelope.result}")
    # snippet.end
    a.timetoken(str(envelope.result))
    a.eq(int(envelope.result), envelope.result.value_as_int)
    a.ok(abs(int(envelope.result) / 10000000 - time.time()) < 120, 'server time is within two minutes of this host')
    a.ok(abs(pubnub.timestamp() - int(time.time())) <= 1, 'timestamp() is int(time.time())')
    a.eq(envelope.result.date_time().year, time.gmtime().tm_year)
