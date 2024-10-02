from pubnub.endpoints.file_operations.file_based_endpoint import FileOperationEndpoint
from pubnub.enums import HttpMethod, PNOperationType
from pubnub import utils
from pubnub.models.consumer.common import PNStatus
from pubnub.models.consumer.file import PNGetFilesResult
from pubnub.structures import Envelope


class PNGetFilesResultEnvelope(Envelope):
    result: PNGetFilesResult
    status: PNStatus


class ListFiles(FileOperationEndpoint):
    LIST_FILES_URL = "/v1/files/%s/channels/%s/files"
    _channel: str

    def __init__(self, pubnub, channel: str = None):
        FileOperationEndpoint.__init__(self, pubnub)
        self._channel = channel

    def build_path(self):
        return ListFiles.LIST_FILES_URL % (
            self.pubnub.config.subscribe_key,
            utils.url_encode(self._channel)
        )

    def channel(self, channel) -> 'ListFiles':
        self._channel = channel
        return self

    def http_method(self):
        return HttpMethod.GET

    def custom_params(self):
        return {}

    def is_auth_required(self):
        return True

    def validate_params(self):
        self.validate_subscribe_key()
        self.validate_channel()

    def create_response(self, envelope) -> PNGetFilesResult:
        return PNGetFilesResult(envelope)

    def sync(self) -> PNGetFilesResultEnvelope:
        return PNGetFilesResultEnvelope(super().sync())

    def operation_type(self):
        return PNOperationType.PNGetFilesAction

    def name(self):
        return "List files"
