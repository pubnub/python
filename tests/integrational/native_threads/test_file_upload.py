import unittest
import threading
import pytest
from pubnub.pubnub import PubNub
from tests.integrational.vcr_helper import pn_vcr
from tests.helper import pnconf_file_copy
from pubnub.endpoints.file_operations.publish_file_message import PublishFileMessage
from pubnub.models.consumer.file import (
    PNSendFileResult, PNGetFilesResult, PNDownloadFileResult,
    PNGetFileDownloadURLResult, PNDeleteFileResult, PNFetchFileUploadS3DataResult,
    PNPublishFileMessageResult
)


CHANNEL = "files_native_threads_ch"

pubnub = PubNub(pnconf_file_copy())
pubnub.config.uuid = "files_threads_uuid"


class TestFileUploadThreads(unittest.TestCase):
    @pytest.fixture(autouse=True)
    def init_with_file_upload_fixtures(self, file_for_upload, file_upload_test_data):
        self.file_for_upload = file_for_upload
        self.file_upload_test_data = file_upload_test_data

    def setUp(self):
        self.event = threading.Event()

    def callback(self, response, status):
        self.response = response
        self.status = status
        self.event.set()

    @pn_vcr.use_cassette(
        "tests/integrational/fixtures/native_threads/file_upload/send_file.yaml",
        filter_query_parameters=('pnsdk',)
    )
    def test_send_file(self):
        fd = open(self.file_for_upload.strpath, "rb")
        pubnub.send_file().\
            channel(CHANNEL).\
            file_name(self.file_for_upload.basename).\
            message({"test_message": "test"}).\
            should_store(True).\
            ttl(222).\
            file_object(fd).pn_async(self.callback)

        self.event.wait()
        assert not self.status.is_error()
        assert isinstance(self.response, PNSendFileResult)

        fd.close()
        self.event.clear()
        return self.response

    @pn_vcr.use_cassette(
        "tests/integrational/fixtures/native_threads/file_upload/list_files.yaml",
        filter_query_parameters=('pnsdk',)
    )
    def test_list_files(self):
        pubnub.list_files().channel(CHANNEL).pn_async(self.callback)

        self.event.wait()
        assert not self.status.is_error()
        assert isinstance(self.response, PNGetFilesResult)
        assert self.response.count == 1
        assert self.file_upload_test_data["UPLOADED_FILENAME"] == self.response.data[0]["name"]

    @pn_vcr.use_cassette(
        "tests/integrational/fixtures/native_threads/file_upload/test_send_and_download_files.yaml",
        filter_query_parameters=('pnsdk',)
    )
    def test_send_and_download_file(self):
        result = self.test_send_file()

        pubnub.download_file().\
            channel(CHANNEL).\
            file_id(result.file_id).\
            file_name(result.name).pn_async(self.callback)

        self.event.wait()
        assert not self.status.is_error()
        assert isinstance(self.response, PNDownloadFileResult)
        assert self.response.data.decode("utf-8") == self.file_upload_test_data["FILE_CONTENT"]

    @pn_vcr.use_cassette(
        "tests/integrational/fixtures/native_threads/file_upload/test_delete_file.yaml",
        filter_query_parameters=('pnsdk',)
    )
    def test_delete_file(self):
        result = self.test_send_file()

        pubnub.delete_file().\
            channel(CHANNEL).\
            file_id(result.file_id).\
            file_name(result.name).pn_async(self.callback)

        self.event.wait()
        assert not self.status.is_error()
        assert isinstance(self.response, PNDeleteFileResult)

    @pn_vcr.use_cassette(
        "tests/integrational/fixtures/native_threads/file_upload/test_get_file_url.yaml",
        filter_query_parameters=('pnsdk',)
    )
    def test_get_file_url(self):
        result = self.test_send_file()

        pubnub.get_file_url().\
            channel(CHANNEL).\
            file_id(result.file_id).\
            file_name(result.name).pn_async(self.callback)

        self.event.wait()
        assert not self.status.is_error()
        assert isinstance(self.response, PNGetFileDownloadURLResult)

    @pn_vcr.use_cassette(
        "tests/integrational/fixtures/native_threads/file_upload/fetch_file_upload_s3_data.yaml",
        filter_query_parameters=('pnsdk',)
    )
    def test_fetch_file_upload_s3_data(self):
        pubnub._fetch_file_upload_s3_data().\
            channel(CHANNEL).\
            file_name(self.file_upload_test_data["UPLOADED_FILENAME"]).pn_async(self.callback)

        self.event.wait()
        assert not self.status.is_error()
        assert isinstance(self.response, PNFetchFileUploadS3DataResult)

    @pn_vcr.use_cassette(
        "tests/integrational/fixtures/native_threads/file_upload/test_publish_file_message.yaml",
        filter_query_parameters=('pnsdk',)
    )
    def test_publish_file_message(self):
        PublishFileMessage(pubnub).\
            channel(CHANNEL).\
            meta({}).\
            message({"test": "test"}).\
            file_id("2222").\
            file_name("test").\
            should_store(True).\
            ttl(222).pn_async(self.callback)

        self.event.wait()
        assert not self.status.is_error()
        assert isinstance(self.response, PNPublishFileMessageResult)
