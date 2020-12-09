from pubnub.endpoints.objects_v2.objects_endpoint import ObjectsEndpoint, ListEndpoint, \
    IncludeCustomEndpoint
from pubnub.enums import PNOperationType
from pubnub.enums import HttpMethod
from pubnub.models.consumer.objects_v2.uuid import PNGetAllUUIDMetadataResult


class GetAllUuid(ObjectsEndpoint, ListEndpoint, IncludeCustomEndpoint):
    GET_ALL_UID_PATH = "/v2/objects/%s/uuids"

    def __init__(self, pubnub):
        ObjectsEndpoint.__init__(self, pubnub)
        ListEndpoint.__init__(self)
        IncludeCustomEndpoint.__init__(self)

    def build_path(self):
        return GetAllUuid.GET_ALL_UID_PATH % self.pubnub.config.subscribe_key

    def create_response(self, envelope):
        return PNGetAllUUIDMetadataResult(envelope)

    def operation_type(self):
        return PNOperationType.PNGetAllUuidMetadataOperation

    def name(self):
        return "Get all UUIDs"

    def http_method(self):
        return HttpMethod.GET
