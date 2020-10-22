from pubnub.endpoints.file_operations.file_based_endpoint import FileOperationEndpoint
from pubnub.enums import HttpMethod, PNOperationType
from pubnub import utils
from pubnub.models.consumer.file import PNFetchFileUploadS3DataResult


class FetchFileUploadS3Data(FileOperationEndpoint):
    GENERATE_FILE_UPLOAD_DATA = "/v1/files/%s/channels/%s/generate-upload-url"

    def __init__(self, pubnub):
        FileOperationEndpoint.__init__(self, pubnub)
        self._file_name = None

    def build_path(self):
        return FetchFileUploadS3Data.GENERATE_FILE_UPLOAD_DATA % (
            self.pubnub.config.subscribe_key,
            utils.url_encode(self._channel)
        )

    def build_data(self):
        params = {
            "name": self._file_name
        }

        return utils.write_value_as_string(params)

    def http_method(self):
        return HttpMethod.POST

    def custom_params(self):
        return {}

    def is_auth_required(self):
        return True

    def file_name(self, file_name):
        self._file_name = file_name
        return self

    def validate_params(self):
        self.validate_subscribe_key()
        self.validate_channel()
        self.validate_file_name()

    def create_response(self, envelope):
        return PNFetchFileUploadS3DataResult(envelope)

    def operation_type(self):
        return PNOperationType.PNFetchFileUploadS3DataAction

    def name(self):
        return "Fetch file upload S3 data"
