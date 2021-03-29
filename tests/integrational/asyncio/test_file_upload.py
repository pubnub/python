import pytest

from unittest.mock import patch
from pubnub.pubnub_asyncio import PubNubAsyncio
from tests.integrational.vcr_helper import pn_vcr
from tests.helper import pnconf_file_copy
from pubnub.endpoints.file_operations.publish_file_message import PublishFileMessage
from pubnub.models.consumer.file import (
    PNSendFileResult, PNGetFilesResult, PNDownloadFileResult,
    PNGetFileDownloadURLResult, PNDeleteFileResult, PNFetchFileUploadS3DataResult, PNPublishFileMessageResult
)


CHANNEL = "files_asyncio_ch"


async def send_file(pubnub, file_for_upload, cipher_key=None):
    with open(file_for_upload.strpath, "rb") as fd:
        envelope = await pubnub.send_file().\
            channel(CHANNEL).\
            file_name(file_for_upload.basename).\
            message({"test_message": "test"}).\
            should_store(True).\
            ttl(222).\
            cipher_key(cipher_key).\
            file_object(fd.read()).future()

    assert isinstance(envelope.result, PNSendFileResult)
    assert envelope.result.name
    assert envelope.result.timestamp
    assert envelope.result.file_id
    return envelope


@pn_vcr.use_cassette(
    "tests/integrational/fixtures/asyncio/file_upload/delete_file.yaml",
    filter_query_parameters=['uuid', 'l_file', 'pnsdk']
)
@pytest.mark.asyncio
async def test_delete_file(event_loop, file_for_upload):
    pubnub = PubNubAsyncio(pnconf_file_copy(), custom_event_loop=event_loop)
    pubnub.config.uuid = "files_asyncio_uuid"

    envelope = await send_file(pubnub, file_for_upload)

    delete_envelope = await pubnub.delete_file().\
        channel(CHANNEL).\
        file_id(envelope.result.file_id).\
        file_name(envelope.result.name).future()

    assert isinstance(delete_envelope.result, PNDeleteFileResult)
    await pubnub.stop()


@pn_vcr.use_cassette(
    "tests/integrational/fixtures/asyncio/file_upload/list_files.yaml",
    filter_query_parameters=['uuid', 'l_file', 'pnsdk']


)
@pytest.mark.asyncio
async def test_list_files(event_loop):
    pubnub = PubNubAsyncio(pnconf_file_copy(), custom_event_loop=event_loop)
    envelope = await pubnub.list_files().channel(CHANNEL).future()

    assert isinstance(envelope.result, PNGetFilesResult)
    assert envelope.result.count == 23
    await pubnub.stop()


@pn_vcr.use_cassette(
    "tests/integrational/fixtures/asyncio/file_upload/send_and_download_file.yaml",
    filter_query_parameters=['uuid', 'l_file', 'pnsdk']
)
@pytest.mark.asyncio
async def test_send_and_download_file(event_loop, file_for_upload):
    pubnub = PubNubAsyncio(pnconf_file_copy(), custom_event_loop=event_loop)
    envelope = await send_file(pubnub, file_for_upload)
    download_envelope = await pubnub.download_file().\
        channel(CHANNEL).\
        file_id(envelope.result.file_id).\
        file_name(envelope.result.name).future()

    assert isinstance(download_envelope.result, PNDownloadFileResult)
    await pubnub.stop()


@pn_vcr.use_cassette(
    "tests/integrational/fixtures/asyncio/file_upload/send_and_download_encrypted_file.yaml",
    filter_query_parameters=['uuid', 'l_file', 'pnsdk']
)
@pytest.mark.asyncio
async def test_send_and_download_file_encrypted(event_loop, file_for_upload, file_upload_test_data):
    pubnub = PubNubAsyncio(pnconf_file_copy(), custom_event_loop=event_loop)

    with patch("pubnub.crypto.PubNubCryptodome.get_initialization_vector", return_value="knightsofni12345"):
        envelope = await send_file(pubnub, file_for_upload, cipher_key="test")
        download_envelope = await pubnub.download_file().\
            channel(CHANNEL).\
            file_id(envelope.result.file_id).\
            file_name(envelope.result.name).\
            cipher_key("test").\
            future()

        assert isinstance(download_envelope.result, PNDownloadFileResult)
        assert download_envelope.result.data == bytes(file_upload_test_data["FILE_CONTENT"], "utf-8")
        await pubnub.stop()


@pn_vcr.use_cassette(
    "tests/integrational/fixtures/asyncio/file_upload/get_file_url.yaml",
    filter_query_parameters=['uuid', 'l_file', 'pnsdk']
)
@pytest.mark.asyncio
async def test_get_file_url(event_loop, file_for_upload):
    pubnub = PubNubAsyncio(pnconf_file_copy(), custom_event_loop=event_loop)
    envelope = await send_file(pubnub, file_for_upload)
    file_url_envelope = await pubnub.get_file_url().\
        channel(CHANNEL).\
        file_id(envelope.result.file_id).\
        file_name(envelope.result.name).future()

    assert isinstance(file_url_envelope.result, PNGetFileDownloadURLResult)
    await pubnub.stop()


@pn_vcr.use_cassette(
    "tests/integrational/fixtures/asyncio/file_upload/fetch_s3_upload_data.yaml",
    filter_query_parameters=['uuid', 'l_file', 'pnsdk']
)
@pytest.mark.asyncio
async def test_fetch_file_upload_s3_data_with_result_invocation(event_loop, file_upload_test_data):
    pubnub = PubNubAsyncio(pnconf_file_copy(), custom_event_loop=event_loop)
    result = await pubnub._fetch_file_upload_s3_data().\
        channel(CHANNEL).\
        file_name(file_upload_test_data["UPLOADED_FILENAME"]).result()

    assert isinstance(result, PNFetchFileUploadS3DataResult)
    await pubnub.stop()


@pn_vcr.use_cassette(
    "tests/integrational/fixtures/asyncio/file_upload/publish_file_message_encrypted.yaml",
    filter_query_parameters=['uuid', 'seqn', 'pnsdk']
)
@pytest.mark.asyncio
async def test_publish_file_message_with_encryption(event_loop, file_upload_test_data):
    pubnub = PubNubAsyncio(pnconf_file_copy(), custom_event_loop=event_loop)
    envelope = await PublishFileMessage(pubnub).\
        channel(CHANNEL).\
        meta({}).\
        message({"test": "test"}).\
        file_id("2222").\
        file_name("test").\
        should_store(True).\
        ttl(222).future()

    assert isinstance(envelope.result, PNPublishFileMessageResult)
    await pubnub.stop()
