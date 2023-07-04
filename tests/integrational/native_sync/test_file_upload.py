import pytest

from Cryptodome.Cipher import AES
from unittest.mock import patch
from pubnub.exceptions import PubNubException
from pubnub.pubnub import PubNub
from tests.integrational.vcr_helper import pn_vcr, pn_vcr_with_empty_body_request
from tests.helper import pnconf_file_copy, pnconf_enc_env_copy
from pubnub.endpoints.file_operations.publish_file_message import PublishFileMessage
from pubnub.models.consumer.file import (
    PNSendFileResult, PNGetFilesResult, PNDownloadFileResult,
    PNGetFileDownloadURLResult, PNDeleteFileResult, PNFetchFileUploadS3DataResult,
    PNPublishFileMessageResult
)

CHANNEL = "files_native_sync_ch"

pubnub = PubNub(pnconf_file_copy())
pubnub.config.uuid = "files_native_sync_uuid"


def send_file(file_for_upload, cipher_key=None, pass_binary=False, timetoken_override=None, pubnub_instance=None):
    if not pubnub_instance:
        pubnub_instance = pubnub

    with open(file_for_upload.strpath, "rb") as fd:
        if pass_binary:
            fd = fd.read()

        send_file_endpoint = pubnub_instance.send_file().\
            channel(CHANNEL).\
            file_name(file_for_upload.basename).\
            message({"test_message": "test"}).\
            should_store(True).\
            ttl(222).\
            file_object(fd).\
            cipher_key(cipher_key)

        if timetoken_override:
            send_file_endpoint = send_file_endpoint.ptto(timetoken_override)

        envelope = send_file_endpoint.sync()

    assert isinstance(envelope.result, PNSendFileResult)
    assert envelope.result.name
    assert envelope.result.timestamp
    assert envelope.result.file_id
    return envelope


@pn_vcr.use_cassette(
    "tests/integrational/fixtures/native_sync/file_upload/list_files.yaml",
    filter_query_parameters=('pnsdk',)
)
def test_list_files(file_upload_test_data):
    envelope = pubnub.list_files().channel(CHANNEL).sync()

    assert isinstance(envelope.result, PNGetFilesResult)
    assert envelope.result.count == 9
    assert file_upload_test_data["UPLOADED_FILENAME"] == envelope.result.data[8]["name"]


@pn_vcr.use_cassette(
    "tests/integrational/fixtures/native_sync/file_upload/download_file.yaml",
    filter_query_parameters=('pnsdk',)
)
def test_send_and_download_file_using_bytes_object(file_for_upload, file_upload_test_data):
    envelope = send_file(file_for_upload, pass_binary=True)

    download_envelope = pubnub.download_file().\
        channel(CHANNEL).\
        file_id(envelope.result.file_id).\
        file_name(envelope.result.name).sync()

    assert isinstance(download_envelope.result, PNDownloadFileResult)
    data = download_envelope.result.data
    assert data == bytes(file_upload_test_data["FILE_CONTENT"], "utf-8")


@pn_vcr.use_cassette(
    "tests/integrational/fixtures/native_sync/file_upload/download_file_encrypted.yaml",
    filter_query_parameters=('pnsdk',)
)
def test_send_and_download_encrypted_file(file_for_upload, file_upload_test_data):
    cipher_key = "silly_walk"
    with patch("pubnub.crypto.PubNubCryptodome.get_initialization_vector", return_value="knightsofni12345"):
        envelope = send_file(file_for_upload, cipher_key=cipher_key)

        download_envelope = pubnub.download_file().\
            channel(CHANNEL).\
            file_id(envelope.result.file_id).\
            file_name(envelope.result.name).\
            cipher_key(cipher_key).sync()

        assert isinstance(download_envelope.result, PNDownloadFileResult)
        data = download_envelope.result.data
        assert data == bytes(file_upload_test_data["FILE_CONTENT"], "utf-8")


@pn_vcr_with_empty_body_request.use_cassette(
    "tests/integrational/fixtures/native_sync/file_upload/file_size_exceeded_maximum_size.yaml",
    filter_query_parameters=('pnsdk',)
)
def test_file_exceeded_maximum_size(file_for_upload_10mb_size):
    with pytest.raises(PubNubException) as exception:
        send_file(file_for_upload_10mb_size)

    assert "Your proposed upload exceeds the maximum allowed size" in str(exception.value)


@pn_vcr.use_cassette(
    "tests/integrational/fixtures/native_sync/file_upload/delete_file.yaml",
    filter_query_parameters=('pnsdk',)
)
def test_delete_file(file_for_upload):
    envelope = send_file(file_for_upload)

    delete_envelope = pubnub.delete_file().\
        channel(CHANNEL).\
        file_id(envelope.result.file_id).\
        file_name(envelope.result.name).sync()

    assert isinstance(delete_envelope.result, PNDeleteFileResult)


@pn_vcr.use_cassette(
    "tests/integrational/fixtures/native_sync/file_upload/download_url.yaml",
    filter_query_parameters=('pnsdk',)
)
def test_get_file_url(file_for_upload):
    envelope = send_file(file_for_upload)

    file_url_envelope = pubnub.get_file_url().\
        channel(CHANNEL).\
        file_id(envelope.result.file_id).\
        file_name(envelope.result.name).sync()

    assert isinstance(file_url_envelope.result, PNGetFileDownloadURLResult)


@pn_vcr.use_cassette(
    "tests/integrational/fixtures/native_sync/file_upload/download_url_check_auth_key_in_url.yaml",
    filter_query_parameters=('pnsdk',)
)
def test_get_file_url_has_auth_key_in_url_and_signature(file_upload_test_data):
    pubnub = PubNub(pnconf_file_copy())
    pubnub.config.uuid = "files_native_sync_uuid"
    pubnub.config.auth_key = "test_auth_key"

    file_url_envelope = pubnub.get_file_url().\
        channel(CHANNEL).\
        file_id("random_file_id").\
        file_name("random_file_name").sync()

    assert "auth=test_auth_key" in file_url_envelope.status.client_request.url


@pn_vcr.use_cassette(
    "tests/integrational/fixtures/native_sync/file_upload/fetch_file_upload_data.yaml",
    filter_query_parameters=('pnsdk',)
)
def test_fetch_file_upload_s3_data(file_upload_test_data):
    envelope = pubnub._fetch_file_upload_s3_data().\
        channel(CHANNEL).\
        file_name(file_upload_test_data["UPLOADED_FILENAME"]).sync()

    assert isinstance(envelope.result, PNFetchFileUploadS3DataResult)


@pn_vcr.use_cassette(
    "tests/integrational/fixtures/native_sync/file_upload/publish_file_message.yaml",
    filter_query_parameters=('pnsdk',)
)
def test_publish_file_message():
    envelope = PublishFileMessage(pubnub).\
        channel(CHANNEL).\
        meta({}).\
        message({"test": "test"}).\
        file_id("2222").\
        file_name("test").\
        should_store(True).\
        ttl(222).sync()

    assert isinstance(envelope.result, PNPublishFileMessageResult)


@pn_vcr.use_cassette(
    "tests/integrational/fixtures/native_sync/file_upload/publish_file_message_encrypted.yaml",
    filter_query_parameters=('pnsdk',)
)
def test_publish_file_message_with_encryption():
    envelope = PublishFileMessage(pubnub).\
        channel(CHANNEL).\
        meta({}).\
        message({"test": "test"}).\
        file_id("2222").\
        file_name("test").\
        should_store(True).\
        ttl(222).sync()

    assert isinstance(envelope.result, PNPublishFileMessageResult)


@pn_vcr.use_cassette(
    "tests/integrational/fixtures/native_sync/file_upload/publish_file_message_with_ptto.yaml",
    filter_query_parameters=('pnsdk',)
)
def test_publish_file_message_with_overriding_time_token():
    timetoken_to_override = 16057799474000000
    envelope = PublishFileMessage(pubnub).\
        channel(CHANNEL).\
        meta({}).\
        message({"test": "test"}).\
        file_id("2222").\
        file_name("test").\
        should_store(True).\
        replicate(True).\
        ptto(timetoken_to_override).\
        ttl(222).sync()

    assert isinstance(envelope.result, PNPublishFileMessageResult)
    assert "ptto" in envelope.status.client_request.url


@pn_vcr.use_cassette(
    "tests/integrational/fixtures/native_sync/file_upload/send_file_with_ptto.yaml",
    filter_query_parameters=('pnsdk',)
)
def test_send_file_with_timetoken_override(file_for_upload):
    send_file(file_for_upload, pass_binary=True, timetoken_override=16057799474000000)


@pn_vcr.use_cassette(
    "tests/integrational/fixtures/native_sync/file_upload/send_and_download_gcm_encrypted_file.json",
    filter_query_parameters=('pnsdk',), serializer='pn_json'
)
def test_send_and_download_gcm_encrypted_file(file_for_upload, file_upload_test_data):
    config = pnconf_enc_env_copy()
    config.cipher_mode = AES.MODE_GCM
    config.fallback_cipher_mode = AES.MODE_CBC
    pubnub = PubNub(config)

    cipher_key = "silly_walk"
    with patch("pubnub.crypto.PubNubCryptodome.get_initialization_vector", return_value="knightsofni12345"):
        envelope = send_file(file_for_upload, cipher_key=cipher_key, pubnub_instance=pubnub)

        download_envelope = pubnub.download_file().\
            channel(CHANNEL).\
            file_id(envelope.result.file_id).\
            file_name(envelope.result.name).\
            cipher_key(cipher_key).sync()

        assert isinstance(download_envelope.result, PNDownloadFileResult)
        data = download_envelope.result.data
        assert data == bytes(file_upload_test_data["FILE_CONTENT"], "utf-8")


@pn_vcr.use_cassette(
    "tests/integrational/fixtures/native_sync/file_upload/send_and_download_encrypted_file_fallback_decode.json",
    filter_query_parameters=('pnsdk',), serializer='pn_json'
)
def test_send_and_download_encrypted_file_fallback_decode(file_for_upload, file_upload_test_data):
    config_cbc = pnconf_enc_env_copy()
    pn_cbc = PubNub(config_cbc)
    config_gcm = pnconf_enc_env_copy()
    config_gcm.cipher_mode = AES.MODE_GCM
    config_gcm.fallback_cipher_mode = AES.MODE_CBC
    pn_gcm = PubNub(config_gcm)

    cipher_key = "silly_walk"
    with patch("pubnub.crypto.PubNubCryptodome.get_initialization_vector", return_value="knightsofni12345"):
        envelope = send_file(file_for_upload, cipher_key=cipher_key, pubnub_instance=pn_cbc)

        download_envelope = pn_gcm.download_file().\
            channel(CHANNEL).\
            file_id(envelope.result.file_id).\
            file_name(envelope.result.name).\
            cipher_key(cipher_key).sync()

        assert isinstance(download_envelope.result, PNDownloadFileResult)
        data = download_envelope.result.data
        assert data == bytes(file_upload_test_data["FILE_CONTENT"], "utf-8")
