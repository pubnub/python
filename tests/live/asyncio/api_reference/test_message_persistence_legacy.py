"""Docs page: message-persistence-legacy (asyncio). The samples of the legacy page."""
import contextlib
import io

import pytest

from support import assertions as a
from support.wait import asettled
from shared.message_persistence import check_paging, seed_async as seed, seed_parallel_async as seed_parallel


async def test_history_basic(aclients):
    """Snippets: history_basic, history_reverse, history_start_reverse, history_end, history_include_timetoken."""
    pubnub = aclients.asyncio('open', 'historian')
    channel = 'history_channel_2'
    seeded = await seed(pubnub, channel, 5)
    tokens = [tt for _, tt in seeded]
    messages = [m for m, _ in seeded]

    async def stored():
        got = await pubnub.history().channel(channel).count(100).future()
        a.eq(len(got.result.messages), 5)

    await asettled(stored, timeout=30, what='seeded messages stored')

    # snippet.history_basic
    envelope = await pubnub.history() \
        .channel("history_channel_2") \
        .count(100) \
        .future()
    if envelope.is_error():
        print(f"Error: {envelope.status.error_data}")
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
    if envelope.is_error():
        print(f"Error: {envelope.status.error_data}")
    # snippet.end
    a.eq([m.entry for m in envelope.result.messages], messages[0:3], 'the three oldest')

    # snippet.history_start_reverse
    envelope = await pubnub.history() \
        .channel("history_channel_2") \
        .start(tokens[1]) \
        .reverse(True) \
        .future()
    if envelope.is_error():
        print(f"Error: {envelope.status.error_data}")
    # snippet.end
    a.eq([m.entry for m in envelope.result.messages], messages[2:], 'newer than start, start excluded')

    # snippet.history_end
    envelope = await pubnub.history() \
        .channel("history_channel_2") \
        .count(100) \
        .end(tokens[2]) \
        .future()
    if envelope.is_error():
        print(f"Error: {envelope.status.error_data}")
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
    if envelope.is_error():
        print(f"Error: {envelope.status.error_data}")
    # snippet.end
    a.eq([m.timetoken for m in envelope.result.messages], tokens)
    a.eq([m.entry for m in envelope.result.messages], messages)


@pytest.mark.timeout(300)
async def test_history_paging(aclients):
    """Snippet: history_paging."""
    pubnub = aclients.asyncio('open', 'pager')
    channel = 'history_paging_channel_2'
    tokens = await seed_parallel(pubnub, channel, 101)

    async def stored():
        got = await pubnub.history().channel(channel).count(100).future()
        a.eq(len(got.result.messages), 100)

    await asettled(stored, timeout=30, what='seeded messages stored')
    start_timetoken = tokens[-1] + 1

    # snippet.history_paging
    async def get_all_messages(start_tt):
        envelope = await pubnub.history() \
            .channel("history_paging_channel_2") \
            .count(100) \
            .start(start_tt) \
            .future()
        if envelope.is_error():
            print(f"Error: {envelope.status.error_data}")
            return
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
    # The pages as the service holds them, read without the sample (a repeated publish is stored twice).
    pages, cursor = [], start_timetoken
    while True:
        page = await pubnub.history().channel(channel).count(100).include_timetoken(True).start(cursor).future()
        listed = [int(m.timetoken) for m in page.result.messages]
        if not listed:
            break
        pages.append((len(listed), int(page.result.start_timetoken), int(page.result.end_timetoken), listed))
        if len(listed) < 100:
            break
        cursor = int(page.result.start_timetoken)
    check_paging(lines, pages, tokens)
