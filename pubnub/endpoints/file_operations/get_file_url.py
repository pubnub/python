from pubnub.endpoints.file_operations.file_based_endpoint import FileOperationEndpoint
from pubnub.enums import HttpMethod, PNOperationType
from pubnub import utils
from pubnub.models.consumer.file import PNGetFileDownloadURLResult


class GetFileDownloadUrl(FileOperationEndpoint):
    GET_FILE_DOWNLOAD_URL = "/v1/files/%s/channels/%s/files/%s/%s"

    def __init__(self, pubnub, file_name=None, file_id=None):
        FileOperationEndpoint.__init__(self, pubnub)
        self._file_id = file_id
        self._file_name = file_name

    def build_path(self):
        return GetFileDownloadUrl.GET_FILE_DOWNLOAD_URL % (
            self.pubnub.config.subscribe_key,
            utils.url_encode(self._channel),
            self._file_id,
            self._file_name
        )

    def get_complete_url(self):
        endpoint_options = self.options()
        endpoint_options.merge_params_in(self.custom_params())
        query_params = '?' + endpoint_options.query_string

        return self.pubnub.config.scheme_extended() + self.pubnub.base_origin + self.build_path() + query_params

    def file_id(self, file_id):
        self._file_id = file_id
        return self

    def file_name(self, file_name):
        self._file_name = file_name
        return self

    def http_method(self):
        return HttpMethod.GET

    def custom_params(self):
        return {}

    def is_auth_required(self):
        return True

    def non_json_response(self):
        return True

    def validate_params(self):
        self.validate_subscribe_key()
        self.validate_channel()
        self.validate_file_id()
        self.validate_file_name()

    def create_response(self, envelope, data=None):
        return PNGetFileDownloadURLResult(envelope)

    def operation_type(self):
        return PNOperationType.PNGetFileDownloadURLAction

    def allow_redirects(self):
        return False

    def name(self):
        return "Get file download url"
