"""Docs page: miscellaneous utility methods (sync). Source: docs/sdks/python/api-reference/misc.md.

The sync page has no Time section, the asyncio page has. The time_get step covers the SDK method for both pages.
"""
import time

from harness import assertions as a
from harness import names, world
from harness.listeners import listen
from harness.step import compile_only
from harness.step import step
from harness.wait import eventually


@step('disconnect_method', 'reconnect_method', role='open')
def test_disconnect_and_reconnect(clients):
    pubnub = clients.sync('open', 'subscriber')
    publisher = clients.sync('open', 'publisher')
    channel = names.with_suffix('my_channel')
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


@compile_only('reconnect_documented', role='open',
              reason='pubnub.reconnect() raises AttributeError: PNSubscriptionRegistry has no reconnect (SDK bug)')
def reconnect_documented(pubnub):
    # snippet.reconnect_documented
    pubnub.reconnect()
    # snippet.end
    return None


@step('get_subscribed_channels', 'get_subscribed_channel_groups', role='open')
def test_get_subscribed(clients):
    pubnub = clients.sync('open', 'subscriber')
    admin = clients.sync('open', 'group_admin')
    channel_a, channel_b = names.with_suffix('ch1'), names.with_suffix('ch2')
    group = names.with_suffix('cg1')
    a.eq(pubnub.get_subscribed_channels(), [], 'nothing subscribed yet')
    world.record('channel_group', group)
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


@step('time_get', role='open')
def test_time(clients):
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
