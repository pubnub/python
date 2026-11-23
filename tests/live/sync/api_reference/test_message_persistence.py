"""Docs page: message persistence (sync). Fetch history, delete messages, message counts and the deprecated history().

Each step seeds its own messages and reads them back through bounds made of the seeded timetokens, so leftovers on a
shared channel name from an earlier run of this page (for example the asyncio one) never change a result.
"""
import pytest

from support import assertions as a
from support.wait import eventually
from shared.message_persistence import seed, seed_parallel, wait_stored, window


def test_fetch_history_builder(clients):
    """Snippets: fetch_history_builder, fetch_history_named."""
    pubnub = clients.sync('open', 'fetcher')
    channel = 'my_channel'
    seeded = seed(pubnub, channel, 3, meta={'origin': 'docs'}, custom_message_type='text-message')
    wait_stored(pubnub, channel, [tt for _, tt in seeded])
    last_message, last_timetoken = seeded[-1]

    # snippet.fetch_history_builder
    envelope = pubnub.fetch_messages() \
        .channels(["my_channel"]) \
        .maximum_per_channel(1) \
        .include_message_actions(True) \
        .include_meta(True) \
        .include_message_type(True) \
        .include_uuid(True) \
        .sync()

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
    envelope = pubnub.fetch_messages(channels=["my_channel"], count=1, include_message_actions=True,
                                     include_meta=True, include_message_type=True, include_uuid=True).sync()

    for message in envelope.result.channels["my_channel"]:
        print(f"Message: {message.message}")
        print(f"Meta: {message.meta}")
        print(f"Timetoken: {message.timetoken}")
    # snippet.end
    check(envelope.result.channels[channel])
    a.eq(sorted(envelope.result.channels), [channel])


def test_fetch_history_range(clients):
    """Snippet: fetch_history_range."""
    pubnub = clients.sync('open', 'ranger')
    channel = 'my_channel'
    seeded = seed(pubnub, channel, 5)
    tokens = [tt for _, tt in seeded]
    messages = [m for m, _ in seeded]
    wait_stored(pubnub, channel, tokens)
    newer_timetoken, older_timetoken = tokens[3], tokens[1]

    # snippet.fetch_history_range
    envelope = pubnub.fetch_messages() \
        .channels(["my_channel"]) \
        .start(newer_timetoken) \
        .end(older_timetoken) \
        .sync()
    # snippet.end

    got = envelope.result.channels[channel]
    a.eq([int(i.timetoken) for i in got], [tokens[1], tokens[2]], 'start excluded, end included, oldest first')
    a.eq([i.message for i in got], messages[1:3])
    only_start = pubnub.fetch_messages(channels=[channel], start=tokens[3], end=tokens[0]).sync()
    a.eq([int(i.timetoken) for i in only_start.result.channels[channel]], tokens[0:3], 'older than start')
    only_end = pubnub.fetch_messages(channels=[channel], end=tokens[2]).sync().result.channels[channel]
    a.eq([int(i.timetoken) for i in only_end][:3], tokens[2:5], 'end only: newer than or equal to end')
    a.eq(int(only_end[-1].timetoken), tokens[4], 'end only: includes the newest message')


@pytest.mark.timeout(300)
def test_fetch_history_multiple(clients):
    """Snippet: fetch_history_multiple."""
    pubnub = clients.sync('open', 'capper')
    channel = 'my_channel'
    first = 'ch1'
    second = 'ch2'
    single = seed_parallel(pubnub, channel, 101)
    on_first = seed_parallel(pubnub, first, 26)
    on_second = seed_parallel(pubnub, second, 26)

    def single_stored():
        got = pubnub.fetch_messages(channels=[channel], count=150).sync().result.channels[channel]
        a.eq([int(i.timetoken) for i in got], single[1:], 'newest 100 of 101')

    eventually(single_stored, timeout=30, what='seeded messages stored')

    def newest_stored():
        got = pubnub.fetch_messages(channels=[first, second], count=30).sync().result.channels
        a.eq([int(i.timetoken) for i in got[first]], on_first[1:], 'newest 25 of ch1')
        a.eq([int(i.timetoken) for i in got[second]], on_second[1:], 'newest 25 of ch2')

    eventually(newest_stored, timeout=30, what='seeded messages on both channels stored')

    # snippet.fetch_history_multiple
    envelope = pubnub.fetch_messages() \
        .channels(["ch1", "ch2"]) \
        .maximum_per_channel(30) \
        .sync()

    for channel_name, items in envelope.result.channels.items():
        print(channel_name, len(items))
    # snippet.end

    for name in (first, second):
        a.eq(len(envelope.result.channels[name]), 25, 'several channels: at most 25 per channel')
    one = pubnub.fetch_messages(channels=[channel], count=150).sync().result.channels[channel]
    a.eq(len(one), 100, 'one channel: at most 100 messages')
    a.eq([int(i.timetoken) for i in one], single[1:], 'the newest 100, oldest first')


def test_message_counts_builder(clients):
    """Snippets: message_counts_builder, message_counts_named, message_counts_multiple_builder,
    message_counts_multiple_named."""
    pubnub = clients.sync('open', 'counter')
    channel = 'my_channel'
    other = 'my_channel_2'
    seeded = seed(pubnub, channel, 4)
    tokens = [tt for _, tt in seeded]
    on_other = [tt for _, tt in seed(pubnub, other, 2)]
    wait_stored(pubnub, channel, tokens)
    wait_stored(pubnub, other, on_other)
    timetoken = tokens[0]
    other_timetoken = on_other[0]

    def counted(envelope, expected):
        a.eq(envelope.result.channels, expected)

    def counted_eventually(build, expected):
        eventually(lambda: counted(build(), expected), timeout=30, what='message counts')

    # The service counts messages newer than the timetoken, the message at the timetoken itself is not counted.
    counted_eventually(lambda: pubnub.message_counts(channels=channel, channels_timetoken=[timetoken - 1]).sync(),
                       {channel: 4})
    counted_eventually(lambda: pubnub.message_counts(channels=channel, channels_timetoken=[timetoken]).sync(),
                       {channel: 3})

    # snippet.message_counts_builder
    envelope = pubnub.message_counts() \
        .channel("my_channel") \
        .channel_timetokens([timetoken]) \
        .sync()
    print(envelope.result.channels["my_channel"])
    # snippet.end
    counted(envelope, {channel: 3})

    # snippet.message_counts_named
    envelope = pubnub.message_counts(channels="my_channel", channels_timetoken=[tokens[2]]).sync()
    # snippet.end
    counted(envelope, {channel: 1})
    counted_eventually(lambda: pubnub.message_counts(channels=channel, channels_timetoken=[tokens[3]]).sync(),
                       {channel: 0})

    # snippet.message_counts_multiple_builder
    envelope = pubnub.message_counts() \
        .channel(["my_channel", "my_channel_2"]) \
        .channel_timetokens([timetoken, other_timetoken]) \
        .sync()
    print(envelope.result.channels)
    # snippet.end
    counted(envelope, {channel: 3, other: 1})

    # snippet.message_counts_multiple_named
    envelope = pubnub.message_counts(channels=["my_channel", "my_channel_2"],
                                     channels_timetoken=[tokens[1], other_timetoken]).sync()
    # snippet.end
    counted(envelope, {channel: 2, other: 1})


def test_delete_messages_builder(clients):
    """Snippets: delete_messages_builder, delete_messages_named."""
    pubnub = clients.sync('open', 'deleter')
    channel = 'my_channel'
    seeded = seed(pubnub, channel, 4)
    tokens = [tt for _, tt in seeded]
    wait_stored(pubnub, channel, tokens)
    newer_timetoken, older_timetoken = tokens[2], tokens[1]

    # snippet.delete_messages_builder
    envelope = pubnub.delete_messages() \
        .channel("my_channel") \
        .start(newer_timetoken) \
        .end(older_timetoken) \
        .sync()
    # snippet.end
    a.eq(envelope.status.is_error(), False)

    def left(expected):
        got = [int(i.timetoken) for i in window(pubnub, channel, tokens[3], tokens[0])]
        a.eq(got, expected)

    eventually(lambda: left([tokens[0], tokens[2], tokens[3]]), timeout=30, what='only the message at end is deleted')

    # snippet.delete_messages_named
    envelope = pubnub.delete_messages(channel="my_channel", start=tokens[3], end=tokens[2]).sync()
    # snippet.end
    a.eq(envelope.status.is_error(), False)
    eventually(lambda: left([tokens[0], tokens[3]]), timeout=30, what='the second message is deleted')


def test_delete_message_single_builder(clients):
    """Snippets: delete_message_single_builder, delete_message_single_named."""
    pubnub = clients.sync('open', 'single_deleter')
    channel = 'my_channel'
    seeded = seed(pubnub, channel, 3)
    tokens = [tt for _, tt in seeded]
    wait_stored(pubnub, channel, tokens)
    publish_timetoken = tokens[1]

    # snippet.delete_message_single_builder
    envelope = pubnub.delete_messages() \
        .channel("my_channel") \
        .start(publish_timetoken - 1) \
        .end(publish_timetoken) \
        .sync()
    # snippet.end
    a.eq(envelope.status.is_error(), False)

    def left(expected):
        got = [int(i.timetoken) for i in window(pubnub, channel, tokens[2], tokens[0])]
        a.eq(got, expected)

    eventually(lambda: left([tokens[0], tokens[2]]), timeout=30, what='exactly the published message is deleted')

    publish_timetoken = tokens[2]
    # snippet.delete_message_single_named
    envelope = pubnub.delete_messages(channel="my_channel", start=publish_timetoken - 1, end=publish_timetoken).sync()
    # snippet.end
    a.eq(envelope.status.is_error(), False)
    eventually(lambda: left([tokens[0]]), timeout=30, what='the last message is deleted')
