from pubnub.endpoints.objects_v2.objects_endpoint import ObjectsEndpoint, UuidEndpoint
from pubnub.enums import PNOperationType
from pubnub.enums import HttpMethod
from pubnub.models.consumer.common import PNStatus
from pubnub.models.consumer.objects_v2.uuid import PNRemoveUUIDMetadataResult
from pubnub.structures import Envelope


class PNRemoveUUIDMetadataResultEnvelope(Envelope):
    result: PNRemoveUUIDMetadataResult
    status: PNStatus


class RemoveUuid(ObjectsEndpoint, UuidEndpoint):
    REMOVE_UID_PATH = "/v2/objects/%s/uuids/%s"

    def __init__(self, pubnub, uuid: str = None):
        ObjectsEndpoint.__init__(self, pubnub)
        UuidEndpoint.__init__(self, uuid=uuid)

    def build_path(self):
        return RemoveUuid.REMOVE_UID_PATH % (self.pubnub.config.subscribe_key, self._effective_uuid())

    def validate_specific_params(self):
        self._validate_uuid()

    def create_response(self, envelope) -> PNRemoveUUIDMetadataResult:
        return PNRemoveUUIDMetadataResult(envelope)

    def sync(self) -> PNRemoveUUIDMetadataResultEnvelope:
        return PNRemoveUUIDMetadataResultEnvelope(super().sync())

    def operation_type(self):
        return PNOperationType.PNRemoveUuidMetadataOperation

    def name(self):
        return "Remove UUID"

    def http_method(self):
        return HttpMethod.DELETE
