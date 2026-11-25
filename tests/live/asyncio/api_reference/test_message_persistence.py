"""Docs page: message persistence (asyncio). Same steps as sync/message_persistence.py with await.

Each step seeds its own messages and reads them back through bounds made of the seeded timetokens, so leftovers on a
shared channel name from an earlier run of this page (for example the sync one) never change a result.
"""
import pytest

from support import assertions as a
from support.wait import aeventually, asettled
from shared.message_persistence import (
    seed_async as seed, seed_parallel_async as seed_parallel, wait_stored_async as wait_stored,
    window_async as window,
)


async def test_fetch_history_builder(aclients):
    """Snippets: fetch_history_builder, fetch_history_named."""
    pubnub = aclients.asyncio('open', 'fetcher')
    channel = 'my_channel'
    seeded = await seed(pubnub, channel, 3, meta={'origin': 'docs'}, custom_message_type='text-message')
    await wait_stored(pubnub, channel, [tt for _, tt in seeded])
    last_message, last_timetoken = seeded[-1]

    # snippet.fetch_history_builder
    envelope = await pubnub.fetch_messages() \
        .channels(["my_channel"]) \
        .maximum_per_channel(1) \
        .include_message_actions(True) \
        .include_meta(True) \
        .include_message_type(True) \
        .include_uuid(True) \
        .future()
    if envelope.is_error():
        print(f"Error: {envelope.status.error_data}")
    else:
        for message in envelope.result.channels["my_channel"]:
            print("Message: %s" % message.message)
            print("Meta: %s" % message.meta)
            print("Timetoken: %s" % message.timetoken)

            for action_type in message.actions:
                print("Message Action type: " + action_type)
    # snippet.end

    def check(items):
        a.eq(len(items), 1, 'maximum_per_channel(1) returns one message')
        a.eq(items[0].message, last_message)
        a.eq(int(items[0].timetoken), last_timetoken)
        a.eq(items[0].meta, {'origin': 'docs'})
        a.eq(items[0].uuid, pubnub.uuid)
        a.ok(hasattr(items[0], 'message_type'), 'include_message_type adds message_type')
        a.eq(items[0].actions, {}, 'no actions yet')

    check(envelope.result.channels[channel])

    # snippet.fetch_history_named
    envelope = await pubnub.fetch_messages(channels=["my_channel"], count=1, include_message_actions=True,
                                           include_meta=True, include_message_type=True, include_uuid=True).future()
    if envelope.is_error():
        print(f"Error: {envelope.status.error_data}")
    else:
        for message in envelope.result.channels["my_channel"]:
            print(f"Message: {message.message}")
            print(f"Meta: {message.meta}")
            print(f"Timetoken: {message.timetoken}")
    # snippet.end
    check(envelope.result.channels[channel])
    a.eq(sorted(envelope.result.channels), [channel])


async def test_fetch_history_range(aclients):
    """Snippet: fetch_history_range."""
    pubnub = aclients.asyncio('open', 'ranger')
    channel = 'my_channel'
    seeded = await seed(pubnub, channel, 5)
    tokens = [tt for _, tt in seeded]
    messages = [m for m, _ in seeded]
    await wait_stored(pubnub, channel, tokens)
    newer_timetoken, older_timetoken = tokens[3], tokens[1]

    # snippet.fetch_history_range
    envelope = await pubnub.fetch_messages() \
        .channels(["my_channel"]) \
        .start(newer_timetoken) \
        .end(older_timetoken) \
        .future()
    if envelope.is_error():
        print(f"Error: {envelope.status.error_data}")
    # snippet.end

    got = envelope.result.channels[channel]
    a.eq([int(i.timetoken) for i in got], [tokens[1], tokens[2]], 'start excluded, end included, oldest first')
    a.eq([i.message for i in got], messages[1:3])
    only_start = await pubnub.fetch_messages(channels=[channel], start=tokens[3], end=tokens[0]).future()
    a.eq([int(i.timetoken) for i in only_start.result.channels[channel]], tokens[0:3], 'older than start')
    only_end = (await pubnub.fetch_messages(channels=[channel], end=tokens[2]).future()).result.channels[channel]
    a.eq([int(i.timetoken) for i in only_end][:3], tokens[2:5], 'end only: newer than or equal to end')
    a.eq(int(only_end[-1].timetoken), tokens[4], 'end only: includes the newest message')


@pytest.mark.timeout(300)
async def test_fetch_history_multiple(aclients):
    """Snippet: fetch_history_multiple."""
    pubnub = aclients.asyncio('open', 'capper')
    channel = 'my_channel'
    first = 'ch1'
    second = 'ch2'
    single = await seed_parallel(pubnub, channel, 101)
    on_first = await seed_parallel(pubnub, first, 26)
    on_second = await seed_parallel(pubnub, second, 26)

    async def single_stored():
        got = (await pubnub.fetch_messages(channels=[channel], count=150).future()).result.channels[channel]
        a.eq([int(i.timetoken) for i in got], single[1:], 'newest 100 of 101')

    await asettled(single_stored, timeout=30, what='seeded messages stored')

    async def newest_stored():
        got = (await pubnub.fetch_messages(channels=[first, second], count=30).future()).result.channels
        a.eq([int(i.timetoken) for i in got[first]], on_first[1:], 'newest 25 of ch1')
        a.eq([int(i.timetoken) for i in got[second]], on_second[1:], 'newest 25 of ch2')

    await asettled(newest_stored, timeout=30, what='seeded messages on both channels stored')

    # snippet.fetch_history_multiple
    envelope = await pubnub.fetch_messages() \
        .channels(["ch1", "ch2"]) \
        .maximum_per_channel(30) \
        .future()
    if envelope.is_error():
        print(f"Error: {envelope.status.error_data}")
    else:
        for channel_name, items in envelope.result.channels.items():
            print(channel_name, len(items))
    # snippet.end

    for name in (first, second):
        a.eq(len(envelope.result.channels[name]), 25, 'several channels: at most 25 per channel')
    one = (await pubnub.fetch_messages(channels=[channel], count=150).future()).result.channels[channel]
    a.eq(len(one), 100, 'one channel: at most 100 messages')
    a.eq([int(i.timetoken) for i in one], single[1:], 'the newest 100, oldest first')


async def test_message_counts_builder(aclients):
    """Snippets: message_counts_builder, message_counts_named, message_counts_multiple_builder,
    message_counts_multiple_named."""
    pubnub = aclients.asyncio('open', 'counter')
    channel = 'my_channel'
    other = 'my_channel_2'
    seeded = await seed(pubnub, channel, 4)
    tokens = [tt for _, tt in seeded]
    on_other = [tt for _, tt in await seed(pubnub, other, 2)]
    await wait_stored(pubnub, channel, tokens)
    await wait_stored(pubnub, other, on_other)
    timetoken = tokens[0]
    other_timetoken = on_other[0]

    def counted(envelope, expected):
        a.eq(envelope.result.channels, expected)

    async def counted_eventually(build, expected):
        async def check():
            counted(await build(), expected)

        await aeventually(check, timeout=30, what='message counts')

    # The service counts messages newer than the timetoken, the message at the timetoken itself is not counted.
    await counted_eventually(
        lambda: pubnub.message_counts(channels=channel, channels_timetoken=[timetoken - 1]).future(), {channel: 4})
    await counted_eventually(
        lambda: pubnub.message_counts(channels=channel, channels_timetoken=[timetoken]).future(), {channel: 3})

    # snippet.message_counts_builder
    envelope = await pubnub.message_counts() \
        .channel("my_channel") \
        .channel_timetokens([timetoken]) \
        .future()
    if envelope.is_error():
        print(f"Error: {envelope.status.error_data}")
    else:
        print(envelope.result.channels["my_channel"])
    # snippet.end
    counted(envelope, {channel: 3})

    # snippet.message_counts_named
    envelope = await pubnub.message_counts(channels="my_channel", channels_timetoken=[tokens[2]]).future()
    if envelope.is_error():
        print(f"Error: {envelope.status.error_data}")
    # snippet.end
    counted(envelope, {channel: 1})
    await counted_eventually(
        lambda: pubnub.message_counts(channels=channel, channels_timetoken=[tokens[3]]).future(), {channel: 0})

    # snippet.message_counts_multiple_builder
    envelope = await pubnub.message_counts() \
        .channel(["my_channel", "my_channel_2"]) \
        .channel_timetokens([timetoken, other_timetoken]) \
        .future()
    if envelope.is_error():
        print(f"Error: {envelope.status.error_data}")
    else:
        print(envelope.result.channels)
    # snippet.end
    counted(envelope, {channel: 3, other: 1})

    # snippet.message_counts_multiple_named
    envelope = await pubnub.message_counts(channels=["my_channel", "my_channel_2"],
                                           channels_timetoken=[tokens[1], other_timetoken]).future()
    if envelope.is_error():
        print(f"Error: {envelope.status.error_data}")
    # snippet.end
    counted(envelope, {channel: 2, other: 1})


async def test_delete_messages_builder(aclients):
    """Snippets: delete_messages_builder, delete_messages_named."""
    pubnub = aclients.asyncio('open', 'deleter')
    channel = 'my_channel'
    seeded = await seed(pubnub, channel, 4)
    tokens = [tt for _, tt in seeded]
    await wait_stored(pubnub, channel, tokens)
    newer_timetoken, older_timetoken = tokens[2], tokens[1]

    # snippet.delete_messages_builder
    envelope = await pubnub.delete_messages() \
        .channel("my_channel") \
        .start(newer_timetoken) \
        .end(older_timetoken) \
        .future()
    if envelope.is_error():
        print(f"Error: {envelope.status.error_data}")
    # snippet.end
    detail = getattr(envelope.status.error_data, 'information', None)
    a.eq(envelope.status.is_error(), False, 'delete failed: %s' % detail)

    async def left(expected):
        got = [int(i.timetoken) for i in await window(pubnub, channel, tokens[3], tokens[0])]
        a.eq(got, expected)

    await aeventually(lambda: left([tokens[0], tokens[2], tokens[3]]), timeout=30,
                      what='only the message at end is deleted')

    # snippet.delete_messages_named
    envelope = await pubnub.delete_messages(channel="my_channel", start=tokens[3], end=tokens[2]).future()
    if envelope.is_error():
        print(f"Error: {envelope.status.error_data}")
    # snippet.end
    detail = getattr(envelope.status.error_data, 'information', None)
    a.eq(envelope.status.is_error(), False, 'delete failed: %s' % detail)
    await aeventually(lambda: left([tokens[0], tokens[3]]), timeout=30, what='the second message is deleted')


async def test_delete_message_single_builder(aclients):
    """Snippets: delete_message_single_builder, delete_message_single_named."""
    pubnub = aclients.asyncio('open', 'single_deleter')
    channel = 'my_channel'
    seeded = await seed(pubnub, channel, 3)
    tokens = [tt for _, tt in seeded]
    await wait_stored(pubnub, channel, tokens)
    publish_timetoken = tokens[1]

    # snippet.delete_message_single_builder
    envelope = await pubnub.delete_messages() \
        .channel("my_channel") \
        .start(publish_timetoken - 1) \
        .end(publish_timetoken) \
        .future()
    if envelope.is_error():
        print(f"Error: {envelope.status.error_data}")
    # snippet.end
    detail = getattr(envelope.status.error_data, 'information', None)
    a.eq(envelope.status.is_error(), False, 'delete failed: %s' % detail)

    async def left(expected):
        got = [int(i.timetoken) for i in await window(pubnub, channel, tokens[2], tokens[0])]
        a.eq(got, expected)

    await aeventually(lambda: left([tokens[0], tokens[2]]), timeout=30,
                      what='exactly the published message is deleted')

    publish_timetoken = tokens[2]
    # snippet.delete_message_single_named
    envelope = await pubnub.delete_messages(channel="my_channel", start=publish_timetoken - 1,
                                            end=publish_timetoken).future()
    if envelope.is_error():
        print(f"Error: {envelope.status.error_data}")
    # snippet.end
    detail = getattr(envelope.status.error_data, 'information', None)
    a.eq(envelope.status.is_error(), False, 'delete failed: %s' % detail)
    await aeventually(lambda: left([tokens[0]]), timeout=30, what='the last message is deleted')
