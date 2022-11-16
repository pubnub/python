from pubnub.endpoints.entities.endpoint import EntitiesEndpoint, IncludeCustomEndpoint, ListEndpoint
from pubnub.enums import PNOperationType
from pubnub.enums import HttpMethod
from pubnub.models.consumer.entities.space import PNFetchSpacesResult


class FetchSpaces(EntitiesEndpoint, ListEndpoint, IncludeCustomEndpoint):
    FETCH_SPACES_PATH = "/v2/objects/%s/channels"
    inclusions = ['status', 'type']

    def __init__(self, pubnub):
        EntitiesEndpoint.__init__(self, pubnub)
        ListEndpoint.__init__(self)
        IncludeCustomEndpoint.__init__(self)

    def build_path(self):
        return FetchSpaces.FETCH_SPACES_PATH % self.pubnub.config.subscribe_key

    def create_response(self, envelope):
        return PNFetchSpacesResult(envelope)

    def operation_type(self):
        return PNOperationType.PNFetchSpacesOperation

    def name(self):
        return "Fetch Spaces"

    def http_method(self):
        return HttpMethod.GET
