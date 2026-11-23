"""Docs page: file sharing (sync). Source: docs/sdks/python/api-reference/files.md.

Every step uploads its own fixture file and deletes it in a finally block. The fixture is 134 bytes, so a download can
be compared byte for byte.
"""
import os
import tempfile
import urllib.request

from support import assertions as a
from support.wait import eventually, settled
from shared.file_sharing import FIXTURE, FIXTURE_BYTES, channel_name, listed_ids, remove, stored_file_messages, upload


def test_send_file_builder(clients, monkeypatch):
    """Snippets: send_file_builder, send_file_custom_message_type."""
    pubnub = clients.sync('open', 'file_sender')
    monkeypatch.chdir(FIXTURE.parent)  # the samples open "sample.gif" from the working directory
    sent = []
    try:
        # snippet.send_file_builder
        with open("sample.gif", "rb") as sample_file:
            response = pubnub.send_file() \
                .channel("ch1") \
                .file_name("sample.gif") \
                .message({"test_message": "test"}) \
                .should_store(True) \
                .file_object(sample_file) \
                .sync()
        print("File sent successfully. File ID:", response.result.file_id)
        # snippet.end
        sent.append(response.result)
        a.ok(response.result.file_id, 'file id returned')
        a.eq(response.result.name, 'sample.gif')
        a.timetoken(response.result.timestamp)
        a.ok(not response.status.is_error(), 'status is not an error')

        # snippet.send_file_custom_message_type
        with open("sample.gif", "rb") as sample_file:
            response_2 = pubnub.send_file() \
                .channel("ch1") \
                .file_name("sample.gif") \
                .message("Hey, it's gif not jif") \
                .custom_message_type("file-message") \
                .should_store(True) \
                .file_object(sample_file) \
                .sync()
        print("File sent successfully. File ID:", response_2.result.file_id)
        # snippet.end
        sent.append(response_2.result)

        a.ok(response_2.result.file_id != response.result.file_id, 'every upload gets its own id')
        both = (response.result.file_id, response_2.result.file_id)
        eventually(lambda: a.eq(len(stored_file_messages(pubnub, *both)), 2, 'file events stored'))
        by_id = {m.message['file']['id']: m for m in stored_file_messages(pubnub, *both)}
        first_event = by_id[response.result.file_id]
        a.eq(first_event.message['message'], {'test_message': 'test'})
        a.eq(first_event.message['file']['name'], 'sample.gif')
        a.eq(str(first_event.timetoken), str(response.result.timestamp), 'the file message carries the timestamp')
        a.eq(by_id[response_2.result.file_id].message['message'], "Hey, it's gif not jif")
        eventually(lambda: a.contains(listed_ids(pubnub), response.result.file_id, 'listed after upload'))
        listing = pubnub.list_files().channel(channel_name()).sync().result.data
        entry = [item for item in listing if item['id'] == response.result.file_id][0]
        a.eq(entry['name'], 'sample.gif')
        a.eq(entry['size'], len(FIXTURE_BYTES), 'listed size is the fixture size')
    finally:
        remove(pubnub, *sent)


def test_list_files_builder(clients):
    """Snippets: list_files_builder, list_files_named."""
    pubnub = clients.sync('open', 'file_lister')
    first, second = upload(pubnub), upload(pubnub)
    try:
        settled(lambda: a.contains(listed_ids(pubnub), second.file_id, 'second upload listed'))

        # snippet.list_files_builder
        file_list_response = pubnub.list_files().channel("ch1").sync()
        print(f"Found {len(file_list_response.result.data)} files:")

        for file_data in file_list_response.result.data:
            print(f"  {file_data['name']} with id: {file_data['id']}")
        # snippet.end
        result = file_list_response.result
        a.contains([item['id'] for item in result.data], first.file_id)
        a.contains([item['id'] for item in result.data], second.file_id)
        a.eq(result.count, len(result.data), 'count matches the page')
        a.ok({'id', 'name', 'size', 'created'} <= set(result.data[0]), 'file entry keys')

        # snippet.list_files_named
        page_1 = pubnub.list_files(channel="ch1", limit=1).sync()
        page_2 = pubnub.list_files(channel="ch1", limit=1, next=page_1.result.next).sync()
        # snippet.end
        a.eq(len(page_1.result.data), 1, 'first page has the limit')
        a.eq(len(page_2.result.data), 1, 'second page has the limit')
        a.ok(page_1.result.data[0]['id'] != page_2.result.data[0]['id'], 'the next token moves forward')
        a.eq({page_1.result.data[0]['id'], page_2.result.data[0]['id']}, {first.file_id, second.file_id})
    finally:
        remove(pubnub, first, second)


def test_get_file_url_builder(clients):
    """Snippets: get_file_url_builder, get_file_url_named."""
    pubnub = clients.sync('open', 'file_url_reader')
    uploaded = upload(pubnub)
    file_data = {'id': uploaded.file_id, 'name': uploaded.name}
    try:
        # snippet.get_file_url_builder
        download_url = pubnub.get_file_url() \
            .channel("ch1") \
            .file_id(file_data['id']) \
            .file_name(file_data['name']) \
            .sync()

        print(f'  Download url: {download_url.result.file_url}')
        # snippet.end
        url_builder = download_url.result.file_url

        # snippet.get_file_url_named
        download_url = pubnub.get_file_url(channel="ch1",
                                           file_id=file_data['id'],
                                           file_name=file_data['name']) \
            .sync()

        print(f'  Download url: {download_url.result.file_url}')
        # snippet.end
        url_named = download_url.result.file_url

        for url in (url_builder, url_named):
            a.ok(url.startswith('https://'), 'url scheme')
            a.contains(url, uploaded.file_id)
            with urllib.request.urlopen(url, timeout=30) as served:
                a.eq(served.status, 200, 'the url serves the file')
                a.eq(served.read(), FIXTURE_BYTES, 'the url serves the same bytes')
    finally:
        remove(pubnub, uploaded)


def test_download_file_builder(clients, monkeypatch):
    """Snippet: download_file_builder."""
    pubnub = clients.sync('open', 'file_downloader')
    uploaded = upload(pubnub)
    file_data = {'id': uploaded.file_id, 'name': uploaded.name}
    target = tempfile.mkdtemp(prefix='docs-snippets-')
    saved_file = os.path.join(target, file_data['name'])
    monkeypatch.chdir(target)  # the sample saves the file in the working directory
    try:
        # snippet.download_file_builder
        download_file = pubnub.download_file() \
            .channel("ch1") \
            .file_id(file_data['id']) \
            .file_name(file_data['name']) \
            .sync()

        save_path = file_data['name']
        with open(save_path, 'wb') as fw:
            fw.write(download_file.result.data)

        print(f"File saved as {save_path}")
        # snippet.end
        a.eq(download_file.result.data, FIXTURE_BYTES, 'downloaded bytes equal the upload')
        a.eq(os.path.realpath(save_path), os.path.realpath(saved_file), 'saved in the working directory')
        with open(saved_file, 'rb') as saved:
            a.eq(saved.read(), FIXTURE_BYTES, 'saved bytes equal the upload')
    finally:
        remove(pubnub, uploaded)
        if os.path.exists(saved_file):
            os.remove(saved_file)
        os.rmdir(target)


def test_delete_file_builder(clients):
    """Snippets: delete_file_builder, delete_file_named."""
    pubnub = clients.sync('open', 'file_deleter')
    one, two = upload(pubnub), upload(pubnub)
    remaining = [one, two]
    try:
        settled(lambda: a.contains(listed_ids(pubnub), two.file_id, 'uploads listed'))
        file_data = {'id': one.file_id, 'name': one.name}

        # snippet.delete_file_builder
        envelope = pubnub.delete_file() \
            .channel("ch1") \
            .file_id(file_data['id']) \
            .file_name(file_data['name']) \
            .sync()

        print("File deleted")
        # snippet.end
        remaining.remove(one)
        a.eq(envelope.result.status, 200, 'delete status')
        eventually(lambda: a.not_contains(listed_ids(pubnub), one.file_id, 'deleted file still listed'))
        a.contains(listed_ids(pubnub), two.file_id, 'the other file is untouched')

        file_data = {'id': two.file_id, 'name': two.name}

        # snippet.delete_file_named
        envelope = pubnub.delete_file(channel="ch1",
                                      file_id=file_data['id'],
                                      file_name=file_data['name']) \
            .sync()

        print("File deleted")
        # snippet.end
        remaining.remove(two)
        a.eq(envelope.result.status, 200, 'delete status')
        eventually(lambda: a.not_contains(listed_ids(pubnub), two.file_id, 'deleted file still listed'))
        a.raises(Exception, lambda: pubnub.download_file().channel(channel_name()).file_id(one.file_id)
                 .file_name(one.name).sync())
    finally:
        remove(pubnub, *remaining)


def test_publish_file_message_builder(clients):
    """Snippets: publish_file_message_builder, publish_file_message_callback."""
    pubnub = clients.sync('open', 'file_publisher')
    uploaded = upload(pubnub)
    results = []
    try:
        eventually(lambda: a.eq(len(stored_file_messages(pubnub, uploaded.file_id)), 1, 'upload stored a message'))
        file_id, file_name = uploaded.file_id, uploaded.name

        # snippet.publish_file_message_builder
        envelope = pubnub.publish_file_message() \
            .channel("ch1") \
            .meta({"test": "test"}) \
            .message({"test_message": "test"}) \
            .custom_message_type("file-message") \
            .file_id(file_id) \
            .file_name(file_name) \
            .should_store(True) \
            .ttl(22) \
            .sync()
        # snippet.end
        a.timetoken(envelope.result.timestamp)
        eventually(lambda: a.eq(len(stored_file_messages(pubnub, file_id)), 2, 'file message stored'))
        stored = stored_file_messages(pubnub, file_id)
        event = [m for m in stored if str(m.timetoken) == str(envelope.result.timestamp)][0]
        a.eq(event.message['file'], {'id': file_id, 'name': file_name})
        a.eq(event.message['message'], {'test_message': 'test'})
        a.eq(event.meta, {'test': 'test'})

        # snippet.publish_file_message_callback
        def callback(response, status):
            results.append((response, status))

        pubnub.publish_file_message() \
            .channel("ch1") \
            .message("Bring me a shrubbery") \
            .file_id(file_id) \
            .file_name(file_name) \
            .should_store(True) \
            .pn_async(callback)
        # snippet.end
        eventually(lambda: a.eq(len(results), 1, 'callback called'))
        response, status = results[0]
        a.ok(not status.is_error(), 'callback status is not an error')
        a.timetoken(response.timestamp)
        eventually(lambda: a.contains([m.message['message'] for m in stored_file_messages(pubnub, file_id)],
                                      'Bring me a shrubbery', 'callback file message stored'))
    finally:
        remove(pubnub, uploaded)
