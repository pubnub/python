"""Shared scenario data of the file-sharing page for both docsets: literal resource names (NAMES,
read by the janitor through support/resources.py) and the helpers the sync and asyncio tests call outside
the snippet markers. Moved from the old docs-snippets/<docset>/ modules. Coroutine twins of a sync helper
carry an "_async" suffix, and the asyncio tests import them under the sync name.
"""
import urllib.request
from pathlib import Path


NAMES = ['test_channel']


FIXTURE = Path(__file__).resolve().parent.parent / 'fixtures' / 'sample.gif'


FIXTURE_BYTES = FIXTURE.read_bytes()


def channel_name():
    return 'ch1'


def upload(pubnub, channel=None, store=True):
    """Seed a file outside the snippet markers. Returns the PNSendFileResult."""
    with open(FIXTURE, 'rb') as sample_file:
        return pubnub.send_file().channel(channel or channel_name()).file_name('sample.gif') \
            .file_object(sample_file).should_store(store).sync().result


def remove(pubnub, *uploaded):
    for item in uploaded:
        try:
            pubnub.delete_file().channel(channel_name()).file_id(item.file_id).file_name(item.name).sync()
        except Exception as e:  # cleanup must never hide the real failure
            print('cleanup: could not delete a file (' + type(e).__name__ + ')')


def stored_file_messages(pubnub, *file_ids):
    """File events read back from Message Persistence. A subscriber callback cannot be used, see the report: the SDK
    raises AttributeError in models/subscription.py for every file event and the worker thread dies."""
    envelope = pubnub.fetch_messages().channels(channel_name()).include_meta(True).sync()
    items = envelope.result.channels.get(channel_name(), [])
    files = [item for item in items if isinstance(item.message, dict) and 'file' in item.message]
    return [item for item in files if not file_ids or item.message['file']['id'] in file_ids]


def listed_ids(pubnub):
    envelope = pubnub.list_files().channel(channel_name()).sync()
    return [item['id'] for item in envelope.result.data]


def channel_name_async():
    return 'test_channel'


async def upload_async(pubnub, store=True):
    """Seed a file outside the snippet markers. Returns the PNSendFileResult."""
    with open(FIXTURE, 'rb') as sample_file:
        envelope = await pubnub.send_file().channel(channel_name_async()).file_name('sample.gif') \
            .file_object(sample_file).should_store(store).future()
    return envelope.result


async def remove_async(pubnub, *uploaded):
    for item in uploaded:
        try:
            await pubnub.delete_file().channel(channel_name_async()).file_id(item.file_id).file_name(item.name).future()
        except Exception as e:  # cleanup must never hide the real failure
            print('cleanup: could not delete a file (' + type(e).__name__ + ')')


async def stored_file_messages_async(pubnub, *file_ids):
    """File events read back from Message Persistence, because the SDK cannot deliver file events to listeners."""
    envelope = await pubnub.fetch_messages().channels(channel_name_async()).include_meta(True).future()
    items = envelope.result.channels.get(channel_name_async(), [])
    files = [item for item in items if isinstance(item.message, dict) and 'file' in item.message]
    return [item for item in files if not file_ids or item.message['file']['id'] in file_ids]


async def listed_ids_async(pubnub):
    envelope = await pubnub.list_files().channel(channel_name_async()).future()
    return [item['id'] for item in envelope.result.data]


def fetch(url):
    with urllib.request.urlopen(url, timeout=30) as served:
        return served.status, served.read()
