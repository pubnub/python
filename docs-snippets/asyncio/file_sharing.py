"""Docs page: file sharing (asyncio). Source: docs/sdks/asyncio/api-reference/files.md. Same contract as sync."""
import asyncio
import os
import tempfile
import urllib.request
from pathlib import Path

from harness import assertions as a
from harness import names
from harness.step import step
from harness.wait import aeventually

FIXTURE = Path(__file__).resolve().parent.parent / 'fixtures' / 'sample.gif'
FIXTURE_BYTES = FIXTURE.read_bytes()


def channel_name():
    return names.with_suffix('test_channel')


REGISTERED_NAMES = ['test_channel']


async def upload(pubnub, store=True):
    """Seed a file outside the snippet markers. Returns the PNSendFileResult."""
    with open(FIXTURE, 'rb') as sample_file:
        envelope = await pubnub.send_file().channel(channel_name()).file_name('sample.gif') \
            .file_object(sample_file).should_store(store).future()
    return envelope.result


async def remove(pubnub, *uploaded):
    for item in uploaded:
        try:
            await pubnub.delete_file().channel(channel_name()).file_id(item.file_id).file_name(item.name).future()
        except Exception as e:  # cleanup must never hide the real failure
            print('cleanup: could not delete a file (' + type(e).__name__ + ')')


async def stored_file_messages(pubnub, *file_ids):
    """File events read back from Message Persistence, because the SDK cannot deliver file events to listeners."""
    envelope = await pubnub.fetch_messages().channels(channel_name()).include_meta(True).future()
    items = envelope.result.channels.get(channel_name(), [])
    files = [item for item in items if isinstance(item.message, dict) and 'file' in item.message]
    return [item for item in files if not file_ids or item.message['file']['id'] in file_ids]


async def listed_ids(pubnub):
    envelope = await pubnub.list_files().channel(channel_name()).future()
    return [item['id'] for item in envelope.result.data]


def fetch(url):
    with urllib.request.urlopen(url, timeout=30) as served:
        return served.status, served.read()


@step('send_file_builder', 'send_file_options', role='open')
async def test_send_file(aclients):
    pubnub = aclients.asyncio('open', 'file_sender')
    sent = []
    try:
        # snippet.send_file_builder
        with open(str(FIXTURE), "rb") as fd:
            envelope = await pubnub.send_file() \
                .channel("test_channel") \
                .file_name("knights_of_ni.jpg") \
                .message({"test_message": "test"}) \
                .should_store(True) \
                .file_object(fd) \
                .future()

        if envelope.status.is_error():
            print("Error sending file")
        else:
            print(f"File sent successfully: {envelope.result.name}")
        # snippet.end
        sent.append(envelope.result)
        a.ok(not envelope.status.is_error(), 'status is not an error')
        a.eq(envelope.result.name, 'knights_of_ni.jpg')
        a.ok(envelope.result.file_id, 'file id returned')
        a.timetoken(envelope.result.timestamp)

        # snippet.send_file_options
        with open(str(FIXTURE), "rb") as fd:
            envelope_2 = await pubnub.send_file() \
                .channel("test_channel") \
                .file_name("knights_of_ni.jpg") \
                .message({"test_message": "test"}) \
                .should_store(True) \
                .ttl(222) \
                .file_object(fd) \
                .future()
        # snippet.end
        sent.append(envelope_2.result)
        both = (envelope.result.file_id, envelope_2.result.file_id)
        a.ok(both[0] != both[1], 'every upload gets its own id')

        async def two_stored():
            a.eq(len(await stored_file_messages(pubnub, *both)), 2, 'file events stored')
        await aeventually(two_stored)
        stored = {m.message['file']['id']: m for m in await stored_file_messages(pubnub, *both)}
        a.eq(stored[both[0]].message['message'], {'test_message': 'test'})
        a.eq(stored[both[0]].message['file']['name'], 'knights_of_ni.jpg')
        a.eq(str(stored[both[0]].timetoken), str(envelope.result.timestamp), 'the message carries the timestamp')

        async def listed():
            a.contains(await listed_ids(pubnub), both[0], 'listed after upload')
        await aeventually(listed)
        listing = (await pubnub.list_files().channel(channel_name()).future()).result.data
        entry = [item for item in listing if item['id'] == both[0]][0]
        a.eq(entry['size'], len(FIXTURE_BYTES), 'listed size is the fixture size')
    finally:
        await remove(pubnub, *sent)


@step('list_files_builder', role='open')
async def test_list_files(aclients):
    pubnub = aclients.asyncio('open', 'file_lister')
    first, second = await upload(pubnub), await upload(pubnub)
    try:
        async def both_listed():
            a.contains(await listed_ids(pubnub), second.file_id, 'second upload listed')
        await aeventually(both_listed)

        # snippet.list_files_builder
        envelope = await pubnub.list_files().channel("test_channel").limit(1).future()
        next_page = await pubnub.list_files().channel("test_channel").limit(1).next(envelope.result.next).future()
        # snippet.end
        a.eq(len(envelope.result.data), 1, 'first page has the limit')
        a.eq(len(next_page.result.data), 1, 'second page has the limit')
        a.eq({envelope.result.data[0]['id'], next_page.result.data[0]['id']}, {first.file_id, second.file_id})
        a.ok({'id', 'name', 'size', 'created'} <= set(envelope.result.data[0]), 'file entry keys')
        everything = await pubnub.list_files().channel(channel_name()).future()
        a.eq(everything.result.count, len(everything.result.data), 'count matches the page')
    finally:
        await remove(pubnub, first, second)


@step('get_file_url_builder', role='open')
async def test_get_file_url(aclients):
    pubnub = aclients.asyncio('open', 'file_url_reader')
    uploaded = await upload(pubnub)
    try:
        # snippet.get_file_url_builder
        envelope = await pubnub.get_file_url(). \
            channel("test_channel"). \
            file_id(uploaded.file_id). \
            file_name(uploaded.name).future()
        # snippet.end
        url = envelope.result.file_url
        a.ok(url.startswith('https://'), 'url scheme')
        a.contains(url, uploaded.file_id)
        status, body = await asyncio.get_running_loop().run_in_executor(None, fetch, url)
        a.eq(status, 200, 'the url serves the file')
        a.eq(body, FIXTURE_BYTES, 'the url serves the same bytes')
    finally:
        await remove(pubnub, uploaded)


@step('download_file_builder', role='open')
async def test_download_file(aclients):
    pubnub = aclients.asyncio('open', 'file_downloader')
    uploaded = await upload(pubnub)
    target = tempfile.mkdtemp(prefix='docs-snippets-')
    save_path = os.path.join(target, uploaded.name)
    try:
        # snippet.download_file_builder
        download_envelope = await pubnub.download_file(). \
            channel("test_channel"). \
            file_id(uploaded.file_id). \
            file_name(uploaded.name).future()

        with open(save_path, "wb") as fw:
            fw.write(download_envelope.result.data)
        # snippet.end
        a.eq(download_envelope.result.data, FIXTURE_BYTES, 'downloaded bytes equal the upload')
        with open(save_path, 'rb') as saved:
            a.eq(saved.read(), FIXTURE_BYTES, 'saved bytes equal the upload')
    finally:
        await remove(pubnub, uploaded)
        if os.path.exists(save_path):
            os.remove(save_path)
        os.rmdir(target)


@step('delete_file_builder', role='open')
async def test_delete_file(aclients):
    pubnub = aclients.asyncio('open', 'file_deleter')
    one, two = await upload(pubnub), await upload(pubnub)
    remaining = [one, two]
    try:
        async def both_listed():
            a.contains(await listed_ids(pubnub), two.file_id, 'uploads listed')
        await aeventually(both_listed)

        # snippet.delete_file_builder
        envelope = await pubnub.delete_file(). \
            channel("test_channel"). \
            file_id(one.file_id). \
            file_name(one.name).future()
        # snippet.end
        remaining.remove(one)
        a.eq(envelope.result.status, 200, 'delete status')

        async def gone():
            a.not_contains(await listed_ids(pubnub), one.file_id, 'deleted file still listed')
        await aeventually(gone)
        a.contains(await listed_ids(pubnub), two.file_id, 'the other file is untouched')
        missing = await pubnub.download_file().channel(channel_name()).file_id(one.file_id) \
            .file_name(one.name).future()
        a.ok(missing.is_error(), 'a deleted file cannot be downloaded')
        a.eq(missing.status.status_code, 404, 'the service answers not found')
    finally:
        await remove(pubnub, *remaining)


@step('publish_file_message_builder', role='open')
async def test_publish_file_message(aclients):
    pubnub = aclients.asyncio('open', 'file_publisher')
    uploaded = await upload(pubnub)
    try:
        async def uploaded_stored():
            a.eq(len(await stored_file_messages(pubnub, uploaded.file_id)), 1, 'upload stored a message')
        await aeventually(uploaded_stored)

        # snippet.publish_file_message_builder
        envelope = await pubnub.publish_file_message(). \
            channel("test_channel"). \
            meta({"test": "test"}). \
            message({"test_message": "test"}). \
            file_id(uploaded.file_id). \
            file_name(uploaded.name). \
            should_store(True). \
            ttl(22).future()
        # snippet.end
        a.timetoken(envelope.result.timestamp)

        async def message_stored():
            a.eq(len(await stored_file_messages(pubnub, uploaded.file_id)), 2, 'file message stored')
        await aeventually(message_stored)
        stored = await stored_file_messages(pubnub, uploaded.file_id)
        event = [m for m in stored if str(m.timetoken) == str(envelope.result.timestamp)][0]
        a.eq(event.message['file'], {'id': uploaded.file_id, 'name': uploaded.name})
        a.eq(event.message['message'], {'test_message': 'test'})
        a.eq(event.meta, {'test': 'test'})
    finally:
        await remove(pubnub, uploaded)
