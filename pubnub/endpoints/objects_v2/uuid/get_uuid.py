from pubnub.endpoints.objects_v2.objects_endpoint import ObjectsEndpoint, \
    IncludeCustomEndpoint, UuidEndpoint
from pubnub.enums import PNOperationType
from pubnub.enums import HttpMethod
from pubnub.models.consumer.objects_v2.uuid import PNGetUUIDMetadataResult


class GetUuid(ObjectsEndpoint, UuidEndpoint, IncludeCustomEndpoint):
    GET_UID_PATH = "/v2/objects/%s/uuids/%s"

    def __init__(self, pubnub):
        ObjectsEndpoint.__init__(self, pubnub)
        UuidEndpoint.__init__(self)
        IncludeCustomEndpoint.__init__(self)

    def build_path(self):
        return GetUuid.GET_UID_PATH % (self.pubnub.config.subscribe_key, self._effective_uuid())

    def validate_specific_params(self):
        self._validate_uuid()

    def create_response(self, envelope):
        return PNGetUUIDMetadataResult(envelope)

    def operation_type(self):
        return PNOperationType.PNGetUuidMetadataOperation

    def name(self):
        return "Get UUID"

    def http_method(self):
        return HttpMethod.GET
