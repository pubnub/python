import unittest
from unittest.mock import Mock, patch

from pubnub.pubnub import PubNub
from pubnub.enums import HttpMethod, PNOperationType
from pubnub.exceptions import PubNubException
from pubnub.errors import (
    PNERR_SUBSCRIBE_KEY_MISSING, PNERR_CHANNEL_MISSING,
    PNERR_FILE_ID_MISSING, PNERR_FILE_NAME_MISSING, PNERR_FILE_OBJECT_MISSING
)

# File operation endpoints
from pubnub.endpoints.file_operations.list_files import ListFiles
from pubnub.endpoints.file_operations.send_file import SendFileNative
from pubnub.endpoints.file_operations.download_file import DownloadFileNative
from pubnub.endpoints.file_operations.delete_file import DeleteFile
from pubnub.endpoints.file_operations.get_file_url import GetFileDownloadUrl
from pubnub.endpoints.file_operations.publish_file_message import PublishFileMessage
from pubnub.endpoints.file_operations.fetch_upload_details import FetchFileUploadS3Data

# Models
from pubnub.models.consumer.file import (
    PNGetFilesResult, PNSendFileResult, PNDownloadFileResult,
    PNDeleteFileResult, PNGetFileDownloadURLResult,
    PNPublishFileMessageResult, PNFetchFileUploadS3DataResult
)

from tests.helper import pnconf_file_copy


class TestFileEndpoints(unittest.TestCase):
    def setUp(self):
        self.config = pnconf_file_copy()
        self.config.subscribe_key = "test-sub-key"
        self.config.publish_key = "test-pub-key"
        self.config.uuid = "test-uuid"
        self.pubnub = PubNub(self.config)
        self.channel = "test-channel"
        self.file_id = "test-file-id"
        self.file_name = "test-file.txt"


class TestListFiles(TestFileEndpoints):
    def test_list_files_basic(self):
        endpoint = ListFiles(self.pubnub, self.channel)

        # Test basic properties
        self.assertEqual(endpoint._channel, self.channel)
        self.assertEqual(endpoint.http_method(), HttpMethod.GET)
        self.assertEqual(endpoint.operation_type(), PNOperationType.PNGetFilesAction)
        self.assertEqual(endpoint.name(), "List files")
        self.assertTrue(endpoint.is_auth_required())

    def test_list_files_path_building(self):
        endpoint = ListFiles(self.pubnub, self.channel)
        expected_path = (f"/v1/files/{self.config.subscribe_key}/channels/"
                         f"{self.channel}/files")
        self.assertEqual(endpoint.build_path(), expected_path)

    def test_list_files_with_limit(self):
        limit = 50
        endpoint = ListFiles(self.pubnub, self.channel, limit=limit)
        params = endpoint.custom_params()
        self.assertEqual(params["limit"], str(limit))

    def test_list_files_with_next(self):
        next_token = "next-token-123"
        endpoint = ListFiles(self.pubnub, self.channel, next=next_token)
        params = endpoint.custom_params()
        self.assertEqual(params["next"], next_token)

    def test_list_files_with_limit_and_next(self):
        limit = 25
        next_token = "next-token-456"
        endpoint = ListFiles(self.pubnub, self.channel, limit=limit, next=next_token)
        params = endpoint.custom_params()
        self.assertEqual(params["limit"], str(limit))
        self.assertEqual(params["next"], next_token)

    def test_list_files_fluent_interface(self):
        endpoint = ListFiles(self.pubnub)
        result = endpoint.channel(self.channel).limit(10).next("token")

        self.assertIsInstance(result, ListFiles)
        self.assertEqual(endpoint._channel, self.channel)
        self.assertEqual(endpoint._limit, 10)
        self.assertEqual(endpoint._next, "token")

    def test_list_files_custom_params_empty(self):
        endpoint = ListFiles(self.pubnub)
        params = endpoint.custom_params()
        self.assertEqual(params, {})

    def test_list_files_custom_params_limit_only(self):
        endpoint = ListFiles(self.pubnub)
        endpoint.limit(25)
        params = endpoint.custom_params()
        self.assertEqual(params, {"limit": "25"})

    def test_list_files_custom_params_next_only(self):
        endpoint = ListFiles(self.pubnub)
        endpoint.next("token123")
        params = endpoint.custom_params()
        self.assertEqual(params, {"next": "token123"})

    def test_list_files_validation_missing_subscribe_key(self):
        self.config.subscribe_key = None
        endpoint = ListFiles(self.pubnub, self.channel)

        with self.assertRaises(PubNubException) as context:
            endpoint.validate_params()
        self.assertEqual(context.exception._pn_error, PNERR_SUBSCRIBE_KEY_MISSING)

    def test_list_files_validation_missing_channel(self):
        endpoint = ListFiles(self.pubnub)

        with self.assertRaises(PubNubException) as context:
            endpoint.validate_params()
        self.assertEqual(context.exception._pn_error, PNERR_CHANNEL_MISSING)

    def test_list_files_create_response(self):
        mock_envelope = {"data": [{"id": "file1", "name": "test.txt"}], "count": 1}
        endpoint = ListFiles(self.pubnub, self.channel)
        result = endpoint.create_response(mock_envelope)

        self.assertIsInstance(result, PNGetFilesResult)
        self.assertEqual(result.data, mock_envelope["data"])
        self.assertEqual(result.count, mock_envelope["count"])

    def test_list_files_constructor_with_parameters(self):
        endpoint = ListFiles(self.pubnub, channel="test_channel", limit=50, next="token")
        self.assertEqual(endpoint._channel, "test_channel")
        self.assertEqual(endpoint._limit, 50)
        self.assertEqual(endpoint._next, "token")


class TestDeleteFile(TestFileEndpoints):
    def test_delete_file_basic(self):
        endpoint = DeleteFile(self.pubnub, self.channel, self.file_name, self.file_id)

        self.assertEqual(endpoint._channel, self.channel)
        self.assertEqual(endpoint._file_name, self.file_name)
        self.assertEqual(endpoint._file_id, self.file_id)
        self.assertEqual(endpoint.http_method(), HttpMethod.DELETE)
        self.assertEqual(endpoint.operation_type(), PNOperationType.PNDeleteFileOperation)
        self.assertEqual(endpoint.name(), "Delete file")
        self.assertTrue(endpoint.is_auth_required())

    def test_delete_file_path_building(self):
        endpoint = DeleteFile(self.pubnub, self.channel, self.file_name, self.file_id)
        expected_path = (f"/v1/files/{self.config.subscribe_key}/channels/"
                         f"{self.channel}/files/{self.file_id}/{self.file_name}")
        self.assertEqual(endpoint.build_path(), expected_path)

    def test_delete_file_fluent_interface(self):
        endpoint = DeleteFile(self.pubnub)
        result = endpoint.channel(self.channel).file_id(self.file_id).file_name(self.file_name)

        self.assertIsInstance(result, DeleteFile)
        self.assertEqual(endpoint._channel, self.channel)
        self.assertEqual(endpoint._file_id, self.file_id)
        self.assertEqual(endpoint._file_name, self.file_name)

    def test_delete_file_validation_missing_subscribe_key(self):
        self.config.subscribe_key = None
        endpoint = DeleteFile(self.pubnub, self.channel, self.file_name, self.file_id)

        with self.assertRaises(PubNubException) as context:
            endpoint.validate_params()
        self.assertEqual(context.exception._pn_error, PNERR_SUBSCRIBE_KEY_MISSING)

    def test_delete_file_validation_missing_channel(self):
        endpoint = DeleteFile(self.pubnub, None, self.file_name, self.file_id)

        with self.assertRaises(PubNubException) as context:
            endpoint.validate_params()
        self.assertEqual(context.exception._pn_error, PNERR_CHANNEL_MISSING)

    def test_delete_file_validation_missing_file_name(self):
        endpoint = DeleteFile(self.pubnub, self.channel, None, self.file_id)

        with self.assertRaises(PubNubException) as context:
            endpoint.validate_params()
        self.assertEqual(context.exception._pn_error, PNERR_FILE_NAME_MISSING)

    def test_delete_file_validation_missing_file_id(self):
        endpoint = DeleteFile(self.pubnub, self.channel, self.file_name, None)

        with self.assertRaises(PubNubException) as context:
            endpoint.validate_params()
        self.assertEqual(context.exception._pn_error, PNERR_FILE_ID_MISSING)

    def test_delete_file_create_response(self):
        mock_envelope = {"status": 200}
        endpoint = DeleteFile(self.pubnub, self.channel, self.file_name, self.file_id)
        result = endpoint.create_response(mock_envelope)

        self.assertIsInstance(result, PNDeleteFileResult)
        self.assertEqual(result.status, mock_envelope["status"])

    def test_delete_file_custom_params(self):
        endpoint = DeleteFile(self.pubnub, self.channel, self.file_name, self.file_id)
        params = endpoint.custom_params()
        self.assertEqual(params, {})


class TestGetFileDownloadUrl(TestFileEndpoints):
    def test_get_file_url_basic(self):
        endpoint = GetFileDownloadUrl(self.pubnub, self.channel, self.file_name, self.file_id)

        self.assertEqual(endpoint._channel, self.channel)
        self.assertEqual(endpoint._file_name, self.file_name)
        self.assertEqual(endpoint._file_id, self.file_id)
        self.assertEqual(endpoint.http_method(), HttpMethod.GET)
        self.assertEqual(endpoint.operation_type(), PNOperationType.PNGetFileDownloadURLAction)
        self.assertEqual(endpoint.name(), "Get file download url")
        self.assertTrue(endpoint.is_auth_required())
        self.assertTrue(endpoint.non_json_response())
        self.assertFalse(endpoint.allow_redirects())

    def test_get_file_url_path_building(self):
        endpoint = GetFileDownloadUrl(self.pubnub, self.channel, self.file_name, self.file_id)
        expected_path = (f"/v1/files/{self.config.subscribe_key}/channels/"
                         f"{self.channel}/files/{self.file_id}/{self.file_name}")
        self.assertEqual(endpoint.build_path(), expected_path)

    def test_get_file_url_fluent_interface(self):
        endpoint = GetFileDownloadUrl(self.pubnub)
        result = endpoint.channel(self.channel).file_id(self.file_id).file_name(self.file_name)

        self.assertIsInstance(result, GetFileDownloadUrl)
        self.assertEqual(endpoint._channel, self.channel)
        self.assertEqual(endpoint._file_id, self.file_id)
        self.assertEqual(endpoint._file_name, self.file_name)

    def test_get_file_url_validation_missing_subscribe_key(self):
        self.config.subscribe_key = None
        endpoint = GetFileDownloadUrl(self.pubnub, self.channel, self.file_name, self.file_id)

        with self.assertRaises(PubNubException) as context:
            endpoint.validate_params()
        self.assertEqual(context.exception._pn_error, PNERR_SUBSCRIBE_KEY_MISSING)

    def test_get_file_url_validation_missing_channel(self):
        endpoint = GetFileDownloadUrl(self.pubnub, None, self.file_name, self.file_id)

        with self.assertRaises(PubNubException) as context:
            endpoint.validate_params()
        self.assertEqual(context.exception._pn_error, PNERR_CHANNEL_MISSING)

    def test_get_file_url_validation_missing_file_name(self):
        endpoint = GetFileDownloadUrl(self.pubnub, self.channel, None, self.file_id)

        with self.assertRaises(PubNubException) as context:
            endpoint.validate_params()
        self.assertEqual(context.exception._pn_error, PNERR_FILE_NAME_MISSING)

    def test_get_file_url_validation_missing_file_id(self):
        endpoint = GetFileDownloadUrl(self.pubnub, self.channel, self.file_name, None)

        with self.assertRaises(PubNubException) as context:
            endpoint.validate_params()
        self.assertEqual(context.exception._pn_error, PNERR_FILE_ID_MISSING)

    def test_get_file_url_create_response(self):
        mock_envelope = Mock()
        mock_envelope.headers = {"Location": "https://example.com/file.txt"}
        endpoint = GetFileDownloadUrl(self.pubnub, self.channel, self.file_name, self.file_id)
        result = endpoint.create_response(mock_envelope)

        self.assertIsInstance(result, PNGetFileDownloadURLResult)
        self.assertEqual(result.file_url, "https://example.com/file.txt")

    def test_get_file_url_custom_params(self):
        endpoint = GetFileDownloadUrl(self.pubnub, self.channel, self.file_name, self.file_id)
        params = endpoint.custom_params()
        self.assertEqual(params, {})

    @patch.object(GetFileDownloadUrl, 'options')
    def test_get_complete_url(self, mock_options):
        mock_options_obj = Mock()
        mock_options_obj.query_string = "auth=test&uuid=test-uuid"
        mock_options_obj.merge_params_in = Mock()
        mock_options.return_value = mock_options_obj

        self.pubnub.config.scheme_extended = Mock(return_value="https://")

        endpoint = GetFileDownloadUrl(self.pubnub, self.channel, self.file_name, self.file_id)
        complete_url = endpoint.get_complete_url()

        expected_base = (f"https://ps.pndsn.com/v1/files/{self.config.subscribe_key}/"
                         f"channels/{self.channel}/files/{self.file_id}/{self.file_name}")
        self.assertIn(expected_base, complete_url)
        self.assertIn("auth=test&uuid=test-uuid", complete_url)


class TestFetchFileUploadS3Data(TestFileEndpoints):
    def test_fetch_upload_details_basic(self):
        endpoint = FetchFileUploadS3Data(self.pubnub)
        endpoint.file_name(self.file_name).channel(self.channel)

        self.assertEqual(endpoint._file_name, self.file_name)
        self.assertEqual(endpoint._channel, self.channel)
        self.assertEqual(endpoint.http_method(), HttpMethod.POST)
        self.assertEqual(endpoint.operation_type(), PNOperationType.PNFetchFileUploadS3DataAction)
        self.assertEqual(endpoint.name(), "Fetch file upload S3 data")
        self.assertTrue(endpoint.is_auth_required())

    def test_fetch_upload_details_path_building(self):
        endpoint = FetchFileUploadS3Data(self.pubnub)
        endpoint.channel(self.channel)
        expected_path = (f"/v1/files/{self.config.subscribe_key}/channels/"
                         f"{self.channel}/generate-upload-url")
        self.assertEqual(endpoint.build_path(), expected_path)

    def test_fetch_upload_details_build_data(self):
        endpoint = FetchFileUploadS3Data(self.pubnub)
        endpoint.file_name(self.file_name)
        data = endpoint.build_data()

        # The data should be JSON string containing the file name
        import json
        parsed_data = json.loads(data)
        self.assertEqual(parsed_data["name"], self.file_name)

    def test_fetch_upload_details_fluent_interface(self):
        endpoint = FetchFileUploadS3Data(self.pubnub)
        result = endpoint.file_name(self.file_name)

        self.assertIsInstance(result, FetchFileUploadS3Data)
        self.assertEqual(endpoint._file_name, self.file_name)

    def test_fetch_upload_details_validation_missing_subscribe_key(self):
        self.config.subscribe_key = None
        endpoint = FetchFileUploadS3Data(self.pubnub)
        endpoint.channel(self.channel).file_name(self.file_name)

        with self.assertRaises(PubNubException) as context:
            endpoint.validate_params()
        self.assertEqual(context.exception._pn_error, PNERR_SUBSCRIBE_KEY_MISSING)

    def test_fetch_upload_details_validation_missing_channel(self):
        endpoint = FetchFileUploadS3Data(self.pubnub)
        endpoint.file_name(self.file_name)

        with self.assertRaises(PubNubException) as context:
            endpoint.validate_params()
        self.assertEqual(context.exception._pn_error, PNERR_CHANNEL_MISSING)

    def test_fetch_upload_details_validation_missing_file_name(self):
        endpoint = FetchFileUploadS3Data(self.pubnub)
        endpoint.channel(self.channel)

        with self.assertRaises(PubNubException) as context:
            endpoint.validate_params()
        self.assertEqual(context.exception._pn_error, PNERR_FILE_NAME_MISSING)

    def test_fetch_upload_details_create_response(self):
        mock_envelope = {
            "data": {"name": self.file_name, "id": self.file_id},
            "file_upload_request": {"url": "https://s3.amazonaws.com/upload"}
        }
        endpoint = FetchFileUploadS3Data(self.pubnub)
        result = endpoint.create_response(mock_envelope)

        self.assertIsInstance(result, PNFetchFileUploadS3DataResult)
        self.assertEqual(result.name, self.file_name)
        self.assertEqual(result.file_id, self.file_id)

    def test_fetch_upload_details_custom_params(self):
        endpoint = FetchFileUploadS3Data(self.pubnub)
        params = endpoint.custom_params()
        self.assertEqual(params, {})


class TestPublishFileMessage(TestFileEndpoints):
    def test_publish_file_message_basic(self):
        endpoint = PublishFileMessage(self.pubnub)
        endpoint.channel(self.channel).file_id(self.file_id).file_name(self.file_name)

        self.assertEqual(endpoint._channel, self.channel)
        self.assertEqual(endpoint._file_id, self.file_id)
        self.assertEqual(endpoint._file_name, self.file_name)
        self.assertEqual(endpoint.http_method(), HttpMethod.GET)
        self.assertEqual(endpoint.operation_type(), PNOperationType.PNSendFileAction)
        self.assertEqual(endpoint.name(), "Sending file upload notification")
        self.assertTrue(endpoint.is_auth_required())

    def test_publish_file_message_path_building(self):
        message = {"text": "Hello"}
        endpoint = PublishFileMessage(self.pubnub)
        endpoint.channel(self.channel).file_id(self.file_id).file_name(self.file_name).message(message)

        path = endpoint.build_path()
        expected_base = (f"/v1/files/publish-file/{self.config.publish_key}/"
                         f"{self.config.subscribe_key}/0/{self.channel}/0/")
        self.assertIn(expected_base, path)
        self.assertIn(self.file_id, path)
        self.assertIn(self.file_name, path)

    def test_publish_file_message_fluent_interface(self):
        message = {"text": "Hello"}
        meta = {"info": "test"}
        endpoint = PublishFileMessage(self.pubnub)
        result = (endpoint.channel(self.channel)
                  .file_id(self.file_id)
                  .file_name(self.file_name)
                  .message(message)
                  .meta(meta)
                  .should_store(True)
                  .ttl(3600))

        self.assertIsInstance(result, PublishFileMessage)
        self.assertEqual(endpoint._channel, self.channel)
        self.assertEqual(endpoint._file_id, self.file_id)
        self.assertEqual(endpoint._file_name, self.file_name)
        self.assertEqual(endpoint._message, message)
        self.assertEqual(endpoint._meta, meta)
        self.assertTrue(endpoint._should_store)
        self.assertEqual(endpoint._ttl, 3600)

    def test_publish_file_message_replicate_and_ptto(self):
        endpoint = PublishFileMessage(self.pubnub)
        timetoken = 16057799474000000

        result = endpoint.replicate(False).ptto(timetoken)

        self.assertIsInstance(result, PublishFileMessage)
        self.assertEqual(endpoint._replicate, False)
        self.assertEqual(endpoint._ptto, timetoken)

    def test_publish_file_message_custom_params(self):
        meta = {"info": "test"}
        endpoint = PublishFileMessage(self.pubnub)
        endpoint.meta(meta).should_store(True).ttl(3600)

        params = endpoint.custom_params()
        self.assertEqual(params["ttl"], 3600)
        self.assertEqual(params["store"], 1)
        self.assertIn("meta", params)

    def test_publish_file_message_custom_params_with_timetoken_override(self):
        endpoint = PublishFileMessage(self.pubnub)
        endpoint.meta({"sender": "test"}) \
                .ttl(120) \
                .should_store(True) \
                .custom_message_type("file_notification") \
                .replicate(False) \
                .ptto(16057799474000000)

        params = endpoint.custom_params()

        self.assertIn("meta", params)
        self.assertEqual(params["ttl"], 120)
        self.assertEqual(params["store"], 1)
        self.assertIn("custom_message_type", params)
        self.assertEqual(params["norep"], "true")
        self.assertEqual(params["ptto"], 16057799474000000)

    def test_publish_file_message_custom_params_store_false(self):
        endpoint = PublishFileMessage(self.pubnub)
        endpoint.should_store(False)

        params = endpoint.custom_params()
        self.assertEqual(params["store"], 0)

    def test_publish_file_message_custom_params_replicate_true(self):
        endpoint = PublishFileMessage(self.pubnub)
        endpoint.replicate(True)
        params = endpoint.custom_params()
        self.assertEqual(params["norep"], "false")

    def test_publish_file_message_custom_params_no_ptto(self):
        endpoint = PublishFileMessage(self.pubnub)
        endpoint.replicate(True)
        params = endpoint.custom_params()
        self.assertNotIn("ptto", params)

    def test_publish_file_message_custom_message_type(self):
        custom_type = "custom-file-type"
        endpoint = PublishFileMessage(self.pubnub)
        result = endpoint.custom_message_type(custom_type)

        self.assertIsInstance(result, PublishFileMessage)
        self.assertEqual(endpoint._custom_message_type, custom_type)

        params = endpoint.custom_params()
        self.assertIn("custom_message_type", params)

    def test_publish_file_message_validation_missing_subscribe_key(self):
        self.config.subscribe_key = None
        endpoint = PublishFileMessage(self.pubnub)
        endpoint.channel(self.channel).file_id(self.file_id).file_name(self.file_name)

        with self.assertRaises(PubNubException) as context:
            endpoint.validate_params()
        self.assertEqual(context.exception._pn_error, PNERR_SUBSCRIBE_KEY_MISSING)

    def test_publish_file_message_validation_missing_channel(self):
        endpoint = PublishFileMessage(self.pubnub)
        endpoint.file_id(self.file_id).file_name(self.file_name)

        with self.assertRaises(PubNubException) as context:
            endpoint.validate_params()
        self.assertEqual(context.exception._pn_error, PNERR_CHANNEL_MISSING)

    def test_publish_file_message_validation_missing_file_name(self):
        endpoint = PublishFileMessage(self.pubnub)
        endpoint.channel(self.channel).file_id(self.file_id)

        with self.assertRaises(PubNubException) as context:
            endpoint.validate_params()
        self.assertEqual(context.exception._pn_error, PNERR_FILE_NAME_MISSING)

    def test_publish_file_message_validation_missing_file_id(self):
        endpoint = PublishFileMessage(self.pubnub)
        endpoint.channel(self.channel).file_name(self.file_name)

        with self.assertRaises(PubNubException) as context:
            endpoint.validate_params()
        self.assertEqual(context.exception._pn_error, PNERR_FILE_ID_MISSING)

    def test_publish_file_message_create_response(self):
        mock_envelope = [1, "Sent", 15566718169184000]
        endpoint = PublishFileMessage(self.pubnub)
        result = endpoint.create_response(mock_envelope)

        self.assertIsInstance(result, PNPublishFileMessageResult)
        self.assertEqual(result.timestamp, 15566718169184000)

    @patch.object(PubNub, 'crypto')
    def test_publish_file_message_with_encryption(self, mock_crypto):
        mock_crypto.encrypt.return_value = "encrypted_message"
        self.config.cipher_key = "test_cipher_key"

        message = {"text": "Hello"}
        endpoint = PublishFileMessage(self.pubnub)
        endpoint.channel(self.channel).file_id(self.file_id).file_name(self.file_name).message(message)

        # Build message should encrypt the content
        built_message = endpoint._build_message()
        self.assertEqual(built_message, "encrypted_message")
        mock_crypto.encrypt.assert_called_once()


class TestSendFileNative(TestFileEndpoints):
    def setUp(self):
        super().setUp()
        self.file_content = b"test file content"
        self.file_object = Mock()
        self.file_object.read.return_value = self.file_content

    def test_send_file_basic(self):
        endpoint = SendFileNative(self.pubnub)
        endpoint.channel(self.channel).file_name(self.file_name).file_object(self.file_object)

        self.assertEqual(endpoint._channel, self.channel)
        self.assertEqual(endpoint._file_name, self.file_name)
        self.assertEqual(endpoint._file_object, self.file_object)
        self.assertEqual(endpoint.http_method(), HttpMethod.POST)
        self.assertEqual(endpoint.operation_type(), PNOperationType.PNSendFileAction)
        self.assertEqual(endpoint.name(), "Send file to S3")
        self.assertFalse(endpoint.is_auth_required())
        self.assertFalse(endpoint.use_base_path())
        self.assertTrue(endpoint.non_json_response())

    def test_send_file_fluent_interface(self):
        message = {"text": "Hello"}
        meta = {"info": "test"}
        endpoint = SendFileNative(self.pubnub)
        result = (endpoint.channel(self.channel)
                  .file_name(self.file_name)
                  .file_object(self.file_object)
                  .message(message)
                  .meta(meta)
                  .should_store(True)
                  .ttl(3600))

        self.assertIsInstance(result, SendFileNative)
        self.assertEqual(endpoint._channel, self.channel)
        self.assertEqual(endpoint._file_name, self.file_name)
        self.assertEqual(endpoint._file_object, self.file_object)
        self.assertEqual(endpoint._message, message)
        self.assertEqual(endpoint._meta, meta)
        self.assertTrue(endpoint._should_store)
        self.assertEqual(endpoint._ttl, 3600)

    def test_send_file_replicate_and_ptto(self):
        endpoint = SendFileNative(self.pubnub)
        timetoken = 16057799474000000

        result = endpoint.replicate(False).ptto(timetoken)

        self.assertIsInstance(result, SendFileNative)
        self.assertEqual(endpoint._replicate, False)
        self.assertEqual(endpoint._ptto, timetoken)

    def test_send_file_ttl_parameter(self):
        endpoint = SendFileNative(self.pubnub)
        result = endpoint.ttl(300)

        self.assertIsInstance(result, SendFileNative)
        self.assertEqual(endpoint._ttl, 300)

    def test_send_file_meta_parameter(self):
        meta_data = {"sender": "test_user", "type": "document"}
        endpoint = SendFileNative(self.pubnub)
        result = endpoint.meta(meta_data)

        self.assertIsInstance(result, SendFileNative)
        self.assertEqual(endpoint._meta, meta_data)

    def test_send_file_message_parameter(self):
        message_data = {"text": "File uploaded", "timestamp": 1234567890}
        endpoint = SendFileNative(self.pubnub)
        result = endpoint.message(message_data)

        self.assertIsInstance(result, SendFileNative)
        self.assertEqual(endpoint._message, message_data)

    def test_send_file_should_store_true(self):
        endpoint = SendFileNative(self.pubnub)
        result = endpoint.should_store(True)

        self.assertIsInstance(result, SendFileNative)
        self.assertEqual(endpoint._should_store, True)

    def test_send_file_should_store_false(self):
        endpoint = SendFileNative(self.pubnub)
        result = endpoint.should_store(False)

        self.assertIsInstance(result, SendFileNative)
        self.assertEqual(endpoint._should_store, False)

    def test_send_file_custom_message_type(self):
        custom_type = "custom-file-type"
        endpoint = SendFileNative(self.pubnub)
        result = endpoint.custom_message_type(custom_type)

        self.assertIsInstance(result, SendFileNative)
        self.assertEqual(endpoint._custom_message_type, custom_type)

    def test_send_file_validation_missing_subscribe_key(self):
        self.config.subscribe_key = None
        endpoint = SendFileNative(self.pubnub)
        endpoint.channel(self.channel).file_name(self.file_name).file_object(self.file_object)

        with self.assertRaises(PubNubException) as context:
            endpoint.validate_params()
        self.assertEqual(context.exception._pn_error, PNERR_SUBSCRIBE_KEY_MISSING)

    def test_send_file_validation_missing_channel(self):
        endpoint = SendFileNative(self.pubnub)
        endpoint.file_name(self.file_name).file_object(self.file_object)

        with self.assertRaises(PubNubException) as context:
            endpoint.validate_params()
        self.assertEqual(context.exception._pn_error, PNERR_CHANNEL_MISSING)

    def test_send_file_validation_missing_file_name(self):
        endpoint = SendFileNative(self.pubnub)
        endpoint.channel(self.channel).file_object(self.file_object)

        with self.assertRaises(PubNubException) as context:
            endpoint.validate_params()
        self.assertEqual(context.exception._pn_error, PNERR_FILE_NAME_MISSING)

    def test_send_file_validation_missing_file_object(self):
        endpoint = SendFileNative(self.pubnub)
        endpoint.channel(self.channel).file_name(self.file_name)

        with self.assertRaises(PubNubException) as context:
            endpoint.validate_params()
        self.assertEqual(context.exception._pn_error, PNERR_FILE_OBJECT_MISSING)

    def test_send_file_request_headers(self):
        endpoint = SendFileNative(self.pubnub)
        headers = endpoint.request_headers()
        self.assertEqual(headers, {})

    def test_send_file_custom_params(self):
        endpoint = SendFileNative(self.pubnub)
        params = endpoint.custom_params()
        self.assertEqual(params, {})

    def test_send_file_build_params_callback(self):
        endpoint = SendFileNative(self.pubnub)
        callback = endpoint.build_params_callback()
        result = callback("test")
        self.assertEqual(result, {})

    def test_send_file_use_compression(self):
        endpoint = SendFileNative(self.pubnub)
        result = endpoint.use_compression(True)

        self.assertIsInstance(result, SendFileNative)
        self.assertTrue(endpoint._use_compression)
        self.assertTrue(endpoint.is_compressable())

    def test_send_file_use_compression_false(self):
        endpoint = SendFileNative(self.pubnub)
        result = endpoint.use_compression(False)

        self.assertIsInstance(result, SendFileNative)
        self.assertFalse(endpoint._use_compression)

    @patch('pubnub.crypto.PubNubFileCrypto.encrypt')
    def test_send_file_encrypt_payload_with_cipher_key(self, mock_encrypt):
        mock_encrypt.return_value = b"encrypted_content"
        endpoint = SendFileNative(self.pubnub)
        endpoint.cipher_key("test_cipher_key")
        endpoint.file_object(self.file_object)

        encrypted = endpoint.encrypt_payload()
        self.assertEqual(encrypted, b"encrypted_content")
        mock_encrypt.assert_called_once()

    @patch.object(SendFileNative, 'encrypt_payload')
    def test_send_file_build_file_upload_request(self, mock_encrypt):
        mock_encrypt.return_value = self.file_content

        # Mock file upload envelope
        mock_envelope = Mock()
        mock_envelope.result.data = {
            "form_fields": [
                {"key": "key", "value": "test_key"},
                {"key": "policy", "value": "test_policy"}
            ]
        }
        endpoint = SendFileNative(self.pubnub)
        endpoint._file_upload_envelope = mock_envelope
        endpoint._file_name = self.file_name

        multipart_body = endpoint.build_file_upload_request()

        self.assertEqual(multipart_body["key"], (None, "test_key"))
        self.assertEqual(multipart_body["policy"], (None, "test_policy"))
        self.assertEqual(multipart_body["file"], (self.file_name, self.file_content, None))

    def test_send_file_create_response(self):
        mock_envelope = Mock()
        mock_file_upload_envelope = Mock()
        mock_file_upload_envelope.result.name = self.file_name
        mock_file_upload_envelope.result.file_id = self.file_id

        endpoint = SendFileNative(self.pubnub)
        endpoint._file_upload_envelope = mock_file_upload_envelope
        result = endpoint.create_response(mock_envelope)

        self.assertIsInstance(result, PNSendFileResult)


class TestDownloadFileNative(TestFileEndpoints):
    def test_download_file_basic(self):
        endpoint = DownloadFileNative(self.pubnub)
        endpoint.channel(self.channel).file_id(self.file_id).file_name(self.file_name)

        self.assertEqual(endpoint._channel, self.channel)
        self.assertEqual(endpoint._file_id, self.file_id)
        self.assertEqual(endpoint._file_name, self.file_name)
        self.assertEqual(endpoint.http_method(), HttpMethod.GET)
        self.assertEqual(endpoint.operation_type(), PNOperationType.PNDownloadFileAction)
        self.assertEqual(endpoint.name(), "Downloading file")
        self.assertFalse(endpoint.is_auth_required())
        self.assertFalse(endpoint.use_base_path())
        self.assertTrue(endpoint.non_json_response())

    def test_download_file_fluent_interface(self):
        endpoint = DownloadFileNative(self.pubnub)
        result = endpoint.channel(self.channel).file_id(self.file_id).file_name(self.file_name)

        self.assertIsInstance(result, DownloadFileNative)
        self.assertEqual(endpoint._channel, self.channel)
        self.assertEqual(endpoint._file_id, self.file_id)
        self.assertEqual(endpoint._file_name, self.file_name)

    def test_download_file_validation_missing_subscribe_key(self):
        self.config.subscribe_key = None
        endpoint = DownloadFileNative(self.pubnub)
        endpoint.channel(self.channel).file_id(self.file_id).file_name(self.file_name)

        with self.assertRaises(PubNubException) as context:
            endpoint.validate_params()
        self.assertEqual(context.exception._pn_error, PNERR_SUBSCRIBE_KEY_MISSING)

    def test_download_file_validation_missing_channel(self):
        endpoint = DownloadFileNative(self.pubnub)
        endpoint.file_id(self.file_id).file_name(self.file_name)

        with self.assertRaises(PubNubException) as context:
            endpoint.validate_params()
        self.assertEqual(context.exception._pn_error, PNERR_CHANNEL_MISSING)

    def test_download_file_validation_missing_file_name(self):
        endpoint = DownloadFileNative(self.pubnub)
        endpoint.channel(self.channel).file_id(self.file_id)

        with self.assertRaises(PubNubException) as context:
            endpoint.validate_params()
        self.assertEqual(context.exception._pn_error, PNERR_FILE_NAME_MISSING)

    def test_download_file_validation_missing_file_id(self):
        endpoint = DownloadFileNative(self.pubnub)
        endpoint.channel(self.channel).file_name(self.file_name)

        with self.assertRaises(PubNubException) as context:
            endpoint.validate_params()
        self.assertEqual(context.exception._pn_error, PNERR_FILE_ID_MISSING)

    def test_download_file_custom_params(self):
        endpoint = DownloadFileNative(self.pubnub)
        params = endpoint.custom_params()
        self.assertEqual(params, {})

    @patch('pubnub.crypto.PubNubFileCrypto.decrypt')
    def test_download_file_decrypt_payload_with_cipher_key(self, mock_decrypt):
        mock_decrypt.return_value = b"decrypted_content"
        endpoint = DownloadFileNative(self.pubnub)
        endpoint.cipher_key("test_cipher_key")

        decrypted = endpoint.decrypt_payload(b"encrypted_content")
        self.assertEqual(decrypted, b"decrypted_content")
        mock_decrypt.assert_called_once_with("test_cipher_key", b"encrypted_content")

    def test_download_file_create_response_without_encryption(self):
        mock_envelope = Mock()
        mock_envelope.content = b"file_content"

        endpoint = DownloadFileNative(self.pubnub)
        result = endpoint.create_response(mock_envelope)

        self.assertIsInstance(result, PNDownloadFileResult)
        self.assertEqual(result.data, b"file_content")

    @patch.object(DownloadFileNative, 'decrypt_payload')
    def test_download_file_create_response_with_encryption(self, mock_decrypt):
        mock_decrypt.return_value = b"decrypted_content"
        mock_envelope = Mock()
        mock_envelope.content = b"encrypted_content"

        self.config.cipher_key = "test_cipher_key"
        endpoint = DownloadFileNative(self.pubnub)
        result = endpoint.create_response(mock_envelope)

        self.assertIsInstance(result, PNDownloadFileResult)
        self.assertEqual(result.data, b"decrypted_content")
        mock_decrypt.assert_called_once_with(b"encrypted_content")
