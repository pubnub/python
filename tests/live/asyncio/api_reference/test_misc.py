"""Docs page: miscellaneous utility methods (asyncio). Source: docs/sdks/asyncio/api-reference/misc.md."""
import time

from support import assertions as a
from support import cleanup as live_cleanup
from support.listen import alisten
from support.wait import aeventually


async def test_time_get(aclients):
    """Snippet: time_get."""
    pubnub = aclients.asyncio('open', 'timekeeper')

    # snippet.time_get
    envelope = await pubnub.time().future()
    if envelope.is_error():
        print(f"Error: {envelope.status.error_data}")
    else:
        print(f"Current time: {envelope.result}")
    # snippet.end
    a.timetoken(str(envelope.result))
    a.eq(int(envelope.result), envelope.result.value_as_int)
    a.ok(abs(int(envelope.result) / 10000000 - time.time()) < 120, 'server time is within two minutes of this host')
    a.ok(abs(pubnub.timestamp() - int(time.time())) <= 1, 'timestamp() is int(time.time())')
    a.eq(envelope.result.date_time().year, time.gmtime().tm_year)


async def test_get_subscribed_channels(aclients):
    """Snippets: get_subscribed_channels, get_subscribed_channel_groups."""
    pubnub = aclients.asyncio('open', 'subscriber')
    admin = aclients.asyncio('open', 'group_admin')
    channel_a, channel_b = 'ch1', 'ch2'
    group = 'cg1'
    live_cleanup.record('channel_group', group)
    try:
        await admin.add_channel_to_channel_group().channels([channel_b]).channel_group(group).future()
        await alisten(pubnub, channel_a, groups=[group])

        # snippet.get_subscribed_channels
        channels = pubnub.get_subscribed_channels()
        # snippet.end
        a.eq(channels, [channel_a])

        # snippet.get_subscribed_channel_groups
        channel_groups = pubnub.get_subscribed_channel_groups()
        # snippet.end
        a.eq(channel_groups, [group])
        pubnub.unsubscribe().channels(channel_a).channel_groups(group).execute()

        async def left():
            a.eq(pubnub.get_subscribed_channels(), [], 'channels after unsubscribe')
        await aeventually(left)
        a.eq(pubnub.get_subscribed_channel_groups(), [], 'groups after unsubscribe')
    finally:
        await admin.remove_channel_group().channel_group(group).future()
