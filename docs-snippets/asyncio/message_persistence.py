"""Docs page: message persistence (asyncio). Same steps as sync/message_persistence.py with await.

Each step seeds its own messages and reads them back through bounds made of the seeded timetokens, so leftovers on a
shared channel name from an earlier run of this page (for example the sync one) never change a result.
"""
import asyncio
import contextlib
import io

from harness import assertions as a
from harness import names
from harness.step import step
from harness.wait import aeventually

REGISTERED_NAMES = ['history_channel_2', 'history_paging_channel_2']


async def seed(client, channel, count, **extra):
    """Publish count messages one after the other and return [(message, timetoken)] oldest first."""
    seeded = []
    for index in range(count):
        message = {'n': index, 'channel': channel}
        builder = client.publish().channel(channel).message(message)
        if extra.get('meta'):
            builder = builder.meta(extra['meta'])
        if extra.get('custom_message_type'):
            builder = builder.custom_message_type(extra['custom_message_type'])
        seeded.append((message, int((await builder.future()).result.timetoken)))
    return seeded


async def seed_parallel(client, channel, count):
    """Publish count messages at the same time. Only the timetokens matter, they come back sorted."""
    async def one(index):
        # The asyncio SDK returns a failed request as an error object (result None), it does not raise. A publish that
        # failed in transit is repeated, any other outcome is reported with the status instead of an AttributeError.
        for attempt in range(3):
            envelope = await client.publish().channel(channel).message({'n': index}).future()
            if not envelope.is_error():
                return int(envelope.result.timetoken)
            last = envelope.status
        raise AssertionError(f'publish {index} failed 3 times: category={last.category} error={last.error_data}')

    return sorted(await asyncio.gather(*[one(i) for i in range(count)]))


async def window(client, channel, newest, oldest, **kwargs):
    """Fetch the seeded range: start is exclusive, so one above the newest. Returns the items oldest first."""
    envelope = await client.fetch_messages(channels=[channel], start=newest + 1, end=oldest, **kwargs).future()
    return envelope.result.channels.get(channel, [])


async def wait_stored(client, channel, timetokens):
    async def check():
        stored = [int(item.timetoken) for item in await window(client, channel, max(timetokens), min(timetokens))]
        a.eq(stored, sorted(timetokens), 'stored timetokens')

    await aeventually(check, timeout=30, what='seeded messages stored')


@step('fetch_history_builder', 'fetch_history_named', role='open')
async def test_fetch_history(aclients):
    pubnub = aclients.asyncio('open', 'fetcher')
    channel = names.with_suffix('my_channel')
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

    for message in envelope.result.channels["my_channel"]:
        print(f"Message: {message.message}")
        print(f"Meta: {message.meta}")
        print(f"Timetoken: {message.timetoken}")
    # snippet.end
    check(envelope.result.channels[channel])
    a.eq(sorted(envelope.result.channels), [channel])


@step('fetch_history_range', role='open')
async def test_fetch_history_range(aclients):
    pubnub = aclients.asyncio('open', 'ranger')
    channel = names.with_suffix('my_channel')
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
    # snippet.end

    got = envelope.result.channels[channel]
    a.eq([int(i.timetoken) for i in got], [tokens[1], tokens[2]], 'start excluded, end included, oldest first')
    a.eq([i.message for i in got], messages[1:3])
    only_start = await pubnub.fetch_messages(channels=[channel], start=tokens[3], end=tokens[0]).future()
    a.eq([int(i.timetoken) for i in only_start.result.channels[channel]], tokens[0:3], 'older than start')
    only_end = (await pubnub.fetch_messages(channels=[channel], end=tokens[2]).future()).result.channels[channel]
    a.eq([int(i.timetoken) for i in only_end][:3], tokens[2:5], 'end only: newer than or equal to end')
    a.eq(int(only_end[-1].timetoken), tokens[4], 'end only: includes the newest message')


@step('fetch_history_multiple', role='open', timeout=300)
async def test_fetch_history_caps(aclients):
    pubnub = aclients.asyncio('open', 'capper')
    channel = names.with_suffix('my_channel')
    first = names.with_suffix('ch1')
    second = names.with_suffix('ch2')
    single = await seed_parallel(pubnub, channel, 101)
    on_first = await seed_parallel(pubnub, first, 26)
    on_second = await seed_parallel(pubnub, second, 26)

    async def single_stored():
        got = (await pubnub.fetch_messages(channels=[channel], count=150).future()).result.channels[channel]
        a.eq([int(i.timetoken) for i in got], single[1:], 'newest 100 of 101')

    await aeventually(single_stored, timeout=30, what='seeded messages stored')

    async def newest_stored():
        got = (await pubnub.fetch_messages(channels=[first, second], count=30).future()).result.channels
        a.eq([int(i.timetoken) for i in got[first]], on_first[1:], 'newest 25 of ch1')
        a.eq([int(i.timetoken) for i in got[second]], on_second[1:], 'newest 25 of ch2')

    await aeventually(newest_stored, timeout=30, what='seeded messages on both channels stored')

    # snippet.fetch_history_multiple
    envelope = await pubnub.fetch_messages() \
        .channels(["ch1", "ch2"]) \
        .maximum_per_channel(30) \
        .future()

    for channel_name, items in envelope.result.channels.items():
        print(channel_name, len(items))
    # snippet.end

    for name in (first, second):
        a.eq(len(envelope.result.channels[name]), 25, 'several channels: at most 25 per channel')
    one = (await pubnub.fetch_messages(channels=[channel], count=150).future()).result.channels[channel]
    a.eq(len(one), 100, 'one channel: at most 100 messages')
    a.eq([int(i.timetoken) for i in one], single[1:], 'the newest 100, oldest first')


@step('message_counts_builder', 'message_counts_named', 'message_counts_multiple_builder',
      'message_counts_multiple_named', role='open')
async def test_message_counts(aclients):
    pubnub = aclients.asyncio('open', 'counter')
    channel = names.with_suffix('my_channel')
    other = names.with_suffix('my_channel_2')
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
    print(envelope.result.channels["my_channel"])
    # snippet.end
    counted(envelope, {channel: 3})

    # snippet.message_counts_named
    envelope = await pubnub.message_counts(channels="my_channel", channels_timetoken=[tokens[2]]).future()
    # snippet.end
    counted(envelope, {channel: 1})
    await counted_eventually(
        lambda: pubnub.message_counts(channels=channel, channels_timetoken=[tokens[3]]).future(), {channel: 0})

    # snippet.message_counts_multiple_builder
    envelope = await pubnub.message_counts() \
        .channel(["my_channel", "my_channel_2"]) \
        .channel_timetokens([timetoken, other_timetoken]) \
        .future()
    print(envelope.result.channels)
    # snippet.end
    counted(envelope, {channel: 3, other: 1})

    # snippet.message_counts_multiple_named
    envelope = await pubnub.message_counts(channels=["my_channel", "my_channel_2"],
                                           channels_timetoken=[tokens[1], other_timetoken]).future()
    # snippet.end
    counted(envelope, {channel: 2, other: 1})


@step('delete_messages_builder', 'delete_messages_named', role='open')
async def test_delete_messages(aclients):
    pubnub = aclients.asyncio('open', 'deleter')
    channel = names.with_suffix('my_channel')
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
    # snippet.end
    detail = getattr(envelope.status.error_data, 'information', None)
    a.eq(envelope.status.is_error(), False, 'delete failed: %s' % detail)
    await aeventually(lambda: left([tokens[0], tokens[3]]), timeout=30, what='the second message is deleted')


@step('delete_message_single_builder', 'delete_message_single_named', role='open')
async def test_delete_single_message(aclients):
    pubnub = aclients.asyncio('open', 'single_deleter')
    channel = names.with_suffix('my_channel')
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
    # snippet.end
    detail = getattr(envelope.status.error_data, 'information', None)
    a.eq(envelope.status.is_error(), False, 'delete failed: %s' % detail)
    await aeventually(lambda: left([tokens[0]]), timeout=30, what='the last message is deleted')


@step('history_basic', 'history_reverse', 'history_start_reverse', 'history_end', 'history_include_timetoken',
      role='open')
async def test_history(aclients):
    pubnub = aclients.asyncio('open', 'historian')
    channel = names.with_suffix('history_channel_2')
    seeded = await seed(pubnub, channel, 5)
    tokens = [tt for _, tt in seeded]
    messages = [m for m, _ in seeded]

    async def stored():
        got = await pubnub.history().channel(channel).count(100).future()
        a.eq(len(got.result.messages), 5)

    await aeventually(stored, timeout=30, what='seeded messages stored')

    # snippet.history_basic
    envelope = await pubnub.history() \
        .channel("history_channel_2") \
        .count(100) \
        .future()
    # snippet.end
    a.eq([m.entry for m in envelope.result.messages], messages, 'oldest first, newest last')
    a.eq(envelope.result.start_timetoken, tokens[0])
    a.eq(envelope.result.end_timetoken, tokens[4])

    # snippet.history_reverse
    envelope = await pubnub.history() \
        .channel("history_channel_2") \
        .count(3) \
        .reverse(True) \
        .future()
    # snippet.end
    a.eq([m.entry for m in envelope.result.messages], messages[0:3], 'the three oldest')

    # snippet.history_start_reverse
    envelope = await pubnub.history() \
        .channel("history_channel_2") \
        .start(tokens[1]) \
        .reverse(True) \
        .future()
    # snippet.end
    a.eq([m.entry for m in envelope.result.messages], messages[2:], 'newer than start, start excluded')

    # snippet.history_end
    envelope = await pubnub.history() \
        .channel("history_channel_2") \
        .count(100) \
        .end(tokens[2]) \
        .future()
    # snippet.end
    a.eq([m.entry for m in envelope.result.messages], messages[2:], 'end included, newest last')
    # The docs sample adds start(-1) and reverse(True). The service refuses start(-1) and with reverse(True) the end
    # timetoken becomes the newer boundary, so the result is the other half of the timeline.
    refused = await pubnub.history().channel(channel).count(100).start(-1).end(tokens[2]).future()
    a.eq((refused.status.is_error(), refused.status.status_code), (True, 400), 'start(-1) is refused with HTTP 400')
    flipped = await pubnub.history().channel(channel).count(100).end(tokens[2]).reverse(True).future()
    a.eq([m.entry for m in flipped.result.messages], messages[:3], 'reverse with end returns the older half')

    # snippet.history_include_timetoken
    envelope = await pubnub.history() \
        .channel("history_channel_2") \
        .count(100) \
        .include_timetoken(True) \
        .future()
    # snippet.end
    a.eq([m.timetoken for m in envelope.result.messages], tokens)
    a.eq([m.entry for m in envelope.result.messages], messages)


@step('history_paging', role='open', timeout=300)
async def test_history_paging(aclients):
    pubnub = aclients.asyncio('open', 'pager')
    channel = names.with_suffix('history_paging_channel_2')
    tokens = await seed_parallel(pubnub, channel, 101)

    async def stored():
        got = await pubnub.history().channel(channel).count(100).future()
        a.eq(len(got.result.messages), 100)

    await aeventually(stored, timeout=30, what='seeded messages stored')
    start_timetoken = tokens[-1] + 1

    # snippet.history_paging
    async def get_all_messages(start_tt):
        envelope = await pubnub.history() \
            .channel("history_paging_channel_2") \
            .count(100) \
            .start(start_tt) \
            .future()
        msgs = envelope.result.messages
        start = envelope.result.start_timetoken
        end = envelope.result.end_timetoken
        count = len(msgs)

        if count > 0:
            print("%d" % count)
            print("start %d" % start)
            print("end %d" % end)

        if count == 100:
            await get_all_messages(start)
    # snippet.end

    output = io.StringIO()
    with contextlib.redirect_stdout(output):
        await get_all_messages(start_timetoken)
    lines = output.getvalue().split('\n')
    a.eq(lines[0:3], ['100', 'start %d' % tokens[1], 'end %d' % tokens[-1]], 'first page: the newest 100')
    a.eq(lines[3:6], ['1', 'start %d' % tokens[0], 'end %d' % tokens[0]], 'second page: the one older message')
