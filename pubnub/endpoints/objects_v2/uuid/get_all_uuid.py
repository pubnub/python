from pubnub.endpoints.objects_v2.objects_endpoint import ObjectsEndpoint, ListEndpoint, \
    IncludeCustomEndpoint, IncludeStatusTypeEndpoint
from pubnub.enums import PNOperationType
from pubnub.enums import HttpMethod
from pubnub.models.consumer.objects_v2.uuid import PNGetAllUUIDMetadataResult


class GetAllUuid(ObjectsEndpoint, ListEndpoint, IncludeCustomEndpoint, IncludeStatusTypeEndpoint):
    GET_ALL_UID_PATH = "/v2/objects/%s/uuids"

    def __init__(self, pubnub, include_custom: bool = None, include_status: bool = True, include_type: bool = True,
                 limit: int = None, filter: str = None, include_total_count: bool = None, sort_keys: list = None):
        ObjectsEndpoint.__init__(self, pubnub)
        ListEndpoint.__init__(self, limit=limit, filter=filter, include_total_count=include_total_count,
                              sort_keys=sort_keys)
        IncludeCustomEndpoint.__init__(self, include_custom=include_custom)
        IncludeStatusTypeEndpoint.__init__(self, include_status=include_status, include_type=include_type)

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
