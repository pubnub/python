"""Docs page: message-persistence-legacy (sync). The samples of the legacy page, moved from the old
docs-snippets/sync/message_persistence.py.
"""
import contextlib
import io

from pubnub.exceptions import PubNubException
import pytest

from support import assertions as a
from support.wait import eventually
from shared.message_persistence import check_paging, seed, seed_parallel


def test_history_basic(clients):
    """Snippets: history_basic, history_reverse, history_start_reverse, history_end, history_include_timetoken."""
    pubnub = clients.sync('open', 'historian')
    channel = 'history_channel'
    seeded = seed(pubnub, channel, 5)
    tokens = [tt for _, tt in seeded]
    messages = [m for m, _ in seeded]

    def stored():
        a.eq(len(pubnub.history().channel(channel).count(100).sync().result.messages), 5)

    eventually(stored, timeout=30, what='seeded messages stored')

    # snippet.history_basic
    envelope = pubnub.history() \
        .channel("history_channel") \
        .count(100) \
        .sync()
    # snippet.end
    a.eq([m.entry for m in envelope.result.messages], messages, 'oldest first, newest last')
    a.eq(envelope.result.start_timetoken, tokens[0])
    a.eq(envelope.result.end_timetoken, tokens[4])

    # snippet.history_reverse
    envelope = pubnub.history() \
        .channel("history_channel") \
        .count(3) \
        .reverse(True) \
        .sync()
    # snippet.end
    a.eq([m.entry for m in envelope.result.messages], messages[0:3], 'the three oldest')

    # snippet.history_start_reverse
    envelope = pubnub.history() \
        .channel("history_channel") \
        .start(tokens[1]) \
        .reverse(True) \
        .sync()
    # snippet.end
    a.eq([m.entry for m in envelope.result.messages], messages[2:], 'newer than start, start excluded')

    # snippet.history_end
    envelope = pubnub.history() \
        .channel("history_channel") \
        .count(100) \
        .end(tokens[2]) \
        .sync()
    # snippet.end
    a.eq([m.entry for m in envelope.result.messages], messages[2:], 'end included, newest last')
    # The docs sample adds start(-1) and reverse(True). The service refuses start(-1) and with reverse(True) the end
    # timetoken becomes the newer boundary, so the result is the other half of the timeline.
    a.raises(PubNubException, pubnub.history().channel(channel).count(100).start(-1).end(tokens[2]).sync,
             match='400')
    flipped = pubnub.history().channel(channel).count(100).end(tokens[2]).reverse(True).sync()
    a.eq([m.entry for m in flipped.result.messages], messages[:3], 'reverse with end returns the older half')

    # snippet.history_include_timetoken
    envelope = pubnub.history() \
        .channel("history_channel") \
        .count(100) \
        .include_timetoken(True) \
        .sync()
    # snippet.end
    a.eq([m.timetoken for m in envelope.result.messages], tokens)
    a.eq([m.entry for m in envelope.result.messages], messages)


@pytest.mark.timeout(300)
def test_history_paging(clients):
    """Snippet: history_paging."""
    pubnub = clients.sync('open', 'pager')
    channel = 'history_paging_channel'
    tokens = seed_parallel(pubnub, channel, 101)

    def stored():
        a.eq(len(pubnub.history().channel(channel).count(100).sync().result.messages), 100)

    eventually(stored, timeout=30, what='seeded messages stored')
    start_timetoken = tokens[-1] + 1

    # snippet.history_paging
    def get_all_messages(start_tt):
        envelope = pubnub.history() \
            .channel("history_paging_channel") \
            .count(100) \
            .start(start_tt) \
            .sync()
        msgs = envelope.result.messages
        start = envelope.result.start_timetoken
        end = envelope.result.end_timetoken
        count = len(msgs)

        if count > 0:
            print("%d" % count)
            print("start %d" % start)
            print("end %d" % end)

        if count == 100:
            get_all_messages(start)
    # snippet.end

    output = io.StringIO()
    with contextlib.redirect_stdout(output):
        get_all_messages(start_timetoken)
    lines = output.getvalue().split('\n')
    # The pages as the service holds them, read without the sample (a repeated publish is stored twice).
    pages, cursor = [], start_timetoken
    while True:
        page = pubnub.history().channel(channel).count(100).include_timetoken(True).start(cursor).sync()
        listed = [int(m.timetoken) for m in page.result.messages]
        if not listed:
            break
        pages.append((len(listed), int(page.result.start_timetoken), int(page.result.end_timetoken), listed))
        if len(listed) < 100:
            break
        cursor = int(page.result.start_timetoken)
    check_paging(lines, pages, tokens)
