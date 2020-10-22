from pubnub.endpoints.file_operations.file_based_endpoint import FileOperationEndpoint
from pubnub.enums import HttpMethod, PNOperationType
from pubnub import utils
from pubnub.models.consumer.file import PNDeleteFileResult


class DeleteFile(FileOperationEndpoint):
    DELETE_FILE_URL = "/v1/files/%s/channels/%s/files/%s/%s"

    def __init__(self, pubnub):
        FileOperationEndpoint.__init__(self, pubnub)
        self._file_id = None
        self._file_name = None

    def build_path(self):
        return DeleteFile.DELETE_FILE_URL % (
            self.pubnub.config.subscribe_key,
            utils.url_encode(self._channel),
            self._file_id,
            self._file_name
        )

    def file_id(self, file_id):
        self._file_id = file_id
        return self

    def file_name(self, file_name):
        self._file_name = file_name
        return self

    def http_method(self):
        return HttpMethod.DELETE

    def custom_params(self):
        return {}

    def is_auth_required(self):
        return True

    def validate_params(self):
        self.validate_subscribe_key()
        self.validate_channel()
        self.validate_file_name()
        self.validate_file_id()

    def create_response(self, envelope):
        return PNDeleteFileResult(envelope)

    def operation_type(self):
        return PNOperationType.PNDeleteFileOperation

    def name(self):
        return "Delete file"
