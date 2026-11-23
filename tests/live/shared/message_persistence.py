"""Shared scenario data of the message-persistence page for both docsets: literal resource names (NAMES,
read by the janitor through support/resources.py) and the helpers the sync and asyncio tests call outside
the snippet markers. Moved from the old docs-snippets/<docset>/ modules. Coroutine twins of a sync helper
carry an "_async" suffix, and the asyncio tests import them under the sync name.
"""
from concurrent.futures import ThreadPoolExecutor
import asyncio

from support import assertions as a
from support.wait import eventually
from support.wait import aeventually

NAMES = ['history_channel', 'history_channel_2', 'history_paging_channel', 'history_paging_channel_2']


def seed(client, channel, count, **extra):
    """Publish count messages one after the other and return [(message, timetoken)] oldest first."""
    seeded = []
    for index in range(count):
        message = {'n': index, 'channel': channel}
        builder = client.publish().channel(channel).message(message)
        if extra.get('meta'):
            builder = builder.meta(extra['meta'])
        if extra.get('custom_message_type'):
            builder = builder.custom_message_type(extra['custom_message_type'])
        seeded.append((message, int(builder.sync().result.timetoken)))
    return seeded


def seed_parallel(client, channel, count):
    """Publish count messages from several threads. Only the timetokens matter, they come back sorted."""
    def one(index):
        return int(client.publish().channel(channel).message({'n': index}).sync().result.timetoken)

    with ThreadPoolExecutor(8) as pool:
        return sorted(pool.map(one, range(count)))


def window(client, channel, newest, oldest, **kwargs):
    """Fetch the seeded range: start is exclusive, so one above the newest. Returns the items oldest first."""
    envelope = client.fetch_messages(channels=[channel], start=newest + 1, end=oldest, **kwargs).sync()
    return envelope.result.channels.get(channel, [])


def wait_stored(client, channel, timetokens):
    def check():
        stored = [int(item.timetoken) for item in window(client, channel, max(timetokens), min(timetokens))]
        a.eq(stored, sorted(timetokens), 'stored timetokens')

    eventually(check, timeout=30, what='seeded messages stored')


async def seed_async(client, channel, count, **extra):
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


async def seed_parallel_async(client, channel, count, concurrency=20):
    """Publish count messages, at most `concurrency` at a time. Only the timetokens matter, they come back sorted.

    No repeat after an error: a publish whose response was lost can already be stored, and a repeat would store it
    twice. The cap keeps the number of requests in flight on one HTTP/2 connection low instead."""
    limit = asyncio.Semaphore(concurrency)

    async def one(index):
        async with limit:
            envelope = await client.publish().channel(channel).message({'n': index}).future()
        if envelope.is_error():
            raise AssertionError(f'publish {index} failed: category={envelope.status.category} '
                                 f'error={envelope.status.error_data}')
        return int(envelope.result.timetoken)

    return sorted(await asyncio.gather(*[one(i) for i in range(count)]))


async def window_async(client, channel, newest, oldest, **kwargs):
    """Fetch the seeded range: start is exclusive, so one above the newest. Returns the items oldest first."""
    envelope = await client.fetch_messages(channels=[channel], start=newest + 1, end=oldest, **kwargs).future()
    return envelope.result.channels.get(channel, [])


async def wait_stored_async(client, channel, timetokens):
    async def check():
        stored = [int(item.timetoken) for item in await window_async(client, channel, max(timetokens), min(timetokens))]
        a.eq(stored, sorted(timetokens), 'stored timetokens')

    await aeventually(check, timeout=30, what='seeded messages stored')


def paging_lines(pages):
    """The text the history paging sample prints for these reference pages: (count, start, end, timetokens) per page."""
    lines = []
    for count, start, end, _ in pages:
        lines += ['%d' % count, 'start %d' % start, 'end %d' % end]
    return lines


def check_paging(lines, pages, tokens):
    """The sample printed what the API holds, and every published message is on a page.
    A publish that the SDK repeated after a transient error is stored twice, so the pages (read independently) are the
    reference, not the list of publish timetokens."""
    a.eq(lines[:len(pages) * 3], paging_lines(pages), 'the pages the sample printed')
    a.eq(lines[len(pages) * 3:], [''], 'nothing printed after the last page')
    on_pages = {t for _, _, _, listed in pages for t in listed}
    a.eq(sorted(set(tokens) - on_pages), [], 'published timetokens that are on no page')
    a.eq(pages[0][0], 100, 'the first page holds the newest 100')
    a.eq(pages[0][2], tokens[-1], 'the first page ends at the newest published message')
