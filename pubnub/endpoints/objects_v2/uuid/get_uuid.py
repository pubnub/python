from pubnub.endpoints.objects_v2.objects_endpoint import ObjectsEndpoint, \
    IncludeCustomEndpoint, UuidEndpoint, IncludeStatusTypeEndpoint
from pubnub.enums import PNOperationType
from pubnub.enums import HttpMethod
from pubnub.models.consumer.common import PNStatus
from pubnub.models.consumer.objects_v2.uuid import PNGetUUIDMetadataResult
from pubnub.structures import Envelope


class PNGetUUIDMetadataResultEnvelope(Envelope):
    result: PNGetUUIDMetadataResult
    status: PNStatus


class GetUuid(ObjectsEndpoint, UuidEndpoint, IncludeCustomEndpoint, IncludeStatusTypeEndpoint):
    GET_UID_PATH = "/v2/objects/%s/uuids/%s"

    def __init__(self, pubnub, uuid: str = None, include_custom: bool = None, include_status: bool = True,
                 include_type: bool = True):
        ObjectsEndpoint.__init__(self, pubnub)
        UuidEndpoint.__init__(self, uuid=uuid)
        IncludeCustomEndpoint.__init__(self, include_custom=include_custom)
        IncludeStatusTypeEndpoint.__init__(self, include_status=include_status, include_type=include_type)

    def build_path(self):
        return GetUuid.GET_UID_PATH % (self.pubnub.config.subscribe_key, self._effective_uuid())

    def validate_specific_params(self):
        self._validate_uuid()

    def create_response(self, envelope) -> PNGetUUIDMetadataResult:
        return PNGetUUIDMetadataResult(envelope)

    def sync(self) -> PNGetUUIDMetadataResultEnvelope:
        return PNGetUUIDMetadataResultEnvelope(super().sync())

    def operation_type(self):
        return PNOperationType.PNGetUuidMetadataOperation

    def name(self):
        return "Get UUID"

    def http_method(self):
        return HttpMethod.GET
