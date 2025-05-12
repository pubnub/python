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
    _limit: int
    _next: str

    def __init__(self, pubnub, channel: str = None, *, limit: int = None, next: str = None):
        FileOperationEndpoint.__init__(self, pubnub)
        self._channel = channel
        self._limit = limit
        self._next = next

    def build_path(self):
        return ListFiles.LIST_FILES_URL % (
            self.pubnub.config.subscribe_key,
            utils.url_encode(self._channel)
        )

    def channel(self, channel: str) -> 'ListFiles':
        self._channel = channel
        return self

    def limit(self, limit: int) -> 'ListFiles':
        self._limit = limit
        return self

    def next(self, next: str) -> 'ListFiles':
        self._next = next
        return self

    def http_method(self):
        return HttpMethod.GET

    def custom_params(self):
        params = {}
        if self._limit:
            params["limit"] = str(self._limit)
        if self._next:
            params["next"] = str(self._next)
        return params

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
