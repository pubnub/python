from pubnub.endpoints.entities.endpoint import EntitiesEndpoint, SpaceEndpoint, IncludeCustomEndpoint
from pubnub.enums import PNOperationType
from pubnub.enums import HttpMethod
from pubnub.models.consumer.entities.space import PNFetchSpaceResult


class FetchSpace(EntitiesEndpoint, SpaceEndpoint, IncludeCustomEndpoint):
    FETCH_SPACE_PATH = "/v2/objects/%s/channels/%s"

    def __init__(self, pubnub):
        EntitiesEndpoint.__init__(self, pubnub)
        SpaceEndpoint.__init__(self)
        IncludeCustomEndpoint.__init__(self)

    def build_path(self):
        return FetchSpace.FETCH_SPACE_PATH % (self.pubnub.config.subscribe_key, self._space_id)

    def validate_specific_params(self):
        self._validate_space_id()

    def create_response(self, envelope):
        return PNFetchSpaceResult(envelope)

    def operation_type(self):
        return PNOperationType.PNFetchSpaceOperation

    def name(self):
        return "Fetch Space"

    def http_method(self):
        return HttpMethod.GET
