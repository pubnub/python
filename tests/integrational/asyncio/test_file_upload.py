import pytest

from unittest.mock import patch
from pubnub.pubnub_asyncio import PubNubAsyncio
from tests.integrational.vcr_helper import pn_vcr
from tests.helper import pnconf_env_copy, pnconf_enc_env_copy
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
    "tests/integrational/fixtures/asyncio/file_upload/delete_file.json", serializer="pn_json",
    filter_query_parameters=['uuid', 'l_file', 'pnsdk']
)
@pytest.mark.asyncio(loop_scope="module")
async def test_delete_file(file_for_upload):
    pubnub = PubNubAsyncio(pnconf_env_copy())
    pubnub.config.uuid = "files_asyncio_uuid"

    envelope = await send_file(pubnub, file_for_upload)

    delete_envelope = await pubnub.delete_file().\
        channel(CHANNEL).\
        file_id(envelope.result.file_id).\
        file_name(envelope.result.name).future()

    assert isinstance(delete_envelope.result, PNDeleteFileResult)
    await pubnub.stop()


@pn_vcr.use_cassette(
    "tests/integrational/fixtures/asyncio/file_upload/list_files.json", serializer="pn_json",
    filter_query_parameters=['uuid', 'l_file', 'pnsdk']
)
@pytest.mark.asyncio(loop_scope="module")
async def test_list_files(file_for_upload, file_upload_test_data):
    pubnub = PubNubAsyncio(pnconf_env_copy())
    pubnub.config.uuid = "files_asyncio_uuid"

    # Clear existing files first to ensure a clean state
    envelope = await pubnub.list_files().channel(CHANNEL).future()
    files = envelope.result.data
    for i in range(len(files)):
        file = files[i]
        await pubnub.delete_file().channel(CHANNEL).file_id(file["id"]).file_name(file["name"]).future()

    envelope = await send_file(pubnub, file_for_upload)

    envelope = await pubnub.list_files().channel(CHANNEL).future()

    assert isinstance(envelope.result, PNGetFilesResult)
    assert envelope.result.count == 1
    assert file_upload_test_data["UPLOADED_FILENAME"] == envelope.result.data[0]["name"]
    await pubnub.stop()


@pn_vcr.use_cassette(
    "tests/integrational/fixtures/asyncio/file_upload/list_files_with_limit.json", serializer="pn_json",
    filter_query_parameters=['uuid', 'l_file', 'pnsdk']
)
@pytest.mark.asyncio(loop_scope="module")
async def test_list_files_with_limit(file_for_upload, file_upload_test_data):
    pubnub = PubNubAsyncio(pnconf_env_copy())
    pubnub.config.uuid = "files_asyncio_uuid"
    await send_file(pubnub, file_for_upload)
    await send_file(pubnub, file_for_upload)
    envelope = await pubnub.list_files().channel(CHANNEL).limit(2).future()
    assert isinstance(envelope.result, PNGetFilesResult)
    assert envelope.result.count == 2
    assert file_upload_test_data["UPLOADED_FILENAME"] == envelope.result.data[0]["name"]
    await pubnub.stop()


@pn_vcr.use_cassette(
    "tests/integrational/fixtures/asyncio/file_upload/list_files_with_page.json", serializer="pn_json",
    filter_query_parameters=['uuid', 'l_file', 'pnsdk']
)
@pytest.mark.asyncio(loop_scope="module")
async def test_list_files_with_page(file_for_upload, file_upload_test_data):
    pubnub = PubNubAsyncio(pnconf_env_copy())
    pubnub.config.uuid = "files_asyncio_uuid"
    await send_file(pubnub, file_for_upload)
    await send_file(pubnub, file_for_upload)
    envelope = await pubnub.list_files().channel(CHANNEL).limit(2).future()
    assert isinstance(envelope.result, PNGetFilesResult)
    assert envelope.result.count == 2
    assert envelope.result.next is not None
    next_page = envelope.result.next
    file_ids = [envelope.result.data[0]['id'], envelope.result.data[1]['id']]
    envelope = await pubnub.list_files().channel(CHANNEL).limit(2).next(next_page).future()
    assert isinstance(envelope.result, PNGetFilesResult)
    assert envelope.result.count == 2
    assert envelope.result.next is not None
    assert envelope.result.data[0]['id'] not in file_ids
    assert envelope.result.data[1]['id'] not in file_ids
    assert file_upload_test_data["UPLOADED_FILENAME"] == envelope.result.data[0]["name"]
    await pubnub.stop()


# @pn_vcr.use_cassette( # Needs new recording for asyncio
#     "tests/integrational/fixtures/asyncio/file_upload/delete_all_files.json", serializer="pn_json",
#     filter_query_parameters=['uuid', 'l_file', 'pnsdk']
# )
@pytest.mark.asyncio(loop_scope="module")
async def test_delete_all_files():
    pubnub = PubNubAsyncio(pnconf_env_copy())
    pubnub.config.uuid = "files_asyncio_uuid"
    envelope = await pubnub.list_files().channel(CHANNEL).future()
    files = envelope.result.data
    for i in range(len(files)):
        file = files[i]
        await pubnub.delete_file().channel(CHANNEL).file_id(file["id"]).file_name(file["name"]).future()
    envelope = await pubnub.list_files().channel(CHANNEL).future()

    assert isinstance(envelope.result, PNGetFilesResult)
    assert envelope.result.count == 0
    await pubnub.stop()


# @pn_vcr.use_cassette(
#     "tests/integrational/fixtures/asyncio/file_upload/send_and_download_file.json", serializer="pn_json",
#     filter_query_parameters=['uuid', 'l_file', 'pnsdk']
# )
@pytest.mark.asyncio(loop_scope="module")
async def test_send_and_download_file(file_for_upload):
    pubnub = PubNubAsyncio(pnconf_env_copy())
    envelope = await send_file(pubnub, file_for_upload)
    download_envelope = await pubnub.download_file().\
        channel(CHANNEL).\
        file_id(envelope.result.file_id).\
        file_name(envelope.result.name).future()

    assert isinstance(download_envelope.result, PNDownloadFileResult)
    await pubnub.stop()


# @pn_vcr.use_cassette(
#     "tests/integrational/fixtures/asyncio/file_upload/send_and_download_encrypted_file_cipher_key.json",
#     filter_query_parameters=['uuid', 'l_file', 'pnsdk'], serializer='pn_json'
# )
@pytest.mark.asyncio(loop_scope="module")
@pytest.mark.filterwarnings("ignore:.*Usage of local cipher_keys is discouraged.*:DeprecationWarning")
async def test_send_and_download_file_encrypted_cipher_key(file_for_upload, file_upload_test_data):
    pubnub = PubNubAsyncio(pnconf_enc_env_copy())

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


# @pn_vcr.use_cassette(
#     "tests/integrational/fixtures/asyncio/file_upload/send_and_download_encrypted_file_crypto_module.json",
#     filter_query_parameters=['uuid', 'l_file', 'pnsdk'], serializer='pn_json'
# )
@pytest.mark.asyncio(loop_scope="module")
async def test_send_and_download_encrypted_file_crypto_module(file_for_upload, file_upload_test_data):
    pubnub = PubNubAsyncio(pnconf_enc_env_copy())

    with patch("pubnub.crypto_core.PubNubLegacyCryptor.get_initialization_vector", return_value=b"knightsofni12345"):
        envelope = await send_file(pubnub, file_for_upload)
        download_envelope = await pubnub.download_file().\
            channel(CHANNEL).\
            file_id(envelope.result.file_id).\
            file_name(envelope.result.name).\
            future()

        assert isinstance(download_envelope.result, PNDownloadFileResult)
        assert download_envelope.result.data == bytes(file_upload_test_data["FILE_CONTENT"], "utf-8")
        await pubnub.stop()


@pn_vcr.use_cassette(
    "tests/integrational/fixtures/asyncio/file_upload/get_file_url.json", serializer="pn_json",
    filter_query_parameters=['uuid', 'l_file', 'pnsdk']
)
@pytest.mark.asyncio(loop_scope="module")
async def test_get_file_url(file_for_upload):
    pubnub = PubNubAsyncio(pnconf_env_copy())
    envelope = await send_file(pubnub, file_for_upload)
    file_url_envelope = await pubnub.get_file_url().\
        channel(CHANNEL).\
        file_id(envelope.result.file_id).\
        file_name(envelope.result.name).future()

    assert isinstance(file_url_envelope.result, PNGetFileDownloadURLResult)
    await pubnub.stop()


@pn_vcr.use_cassette(
    "tests/integrational/fixtures/asyncio/file_upload/fetch_s3_upload_data.json", serializer="pn_json",
    filter_query_parameters=['uuid', 'l_file', 'pnsdk']
)
@pytest.mark.asyncio(loop_scope="module")
async def test_fetch_file_upload_s3_data_with_result_invocation(file_upload_test_data):
    pubnub = PubNubAsyncio(pnconf_env_copy())
    result = await pubnub._fetch_file_upload_s3_data().\
        channel(CHANNEL).\
        file_name(file_upload_test_data["UPLOADED_FILENAME"]).result()

    assert isinstance(result, PNFetchFileUploadS3DataResult)
    await pubnub.stop()


@pn_vcr.use_cassette(
    "tests/integrational/fixtures/asyncio/file_upload/publish_file_message_encrypted.json", serializer="pn_json",
    filter_query_parameters=['uuid', 'seqn', 'pnsdk']
)
@pytest.mark.asyncio(loop_scope="module")
async def test_publish_file_message_with_encryption(file_upload_test_data):
    pubnub = PubNubAsyncio(pnconf_env_copy())
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
