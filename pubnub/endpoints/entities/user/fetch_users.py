from pubnub.endpoints.entities.endpoint import EntitiesEndpoint, ListEndpoint, IncludeCustomEndpoint
from pubnub.enums import PNOperationType
from pubnub.enums import HttpMethod
from pubnub.models.consumer.entities.user import PNFetchUsersResult


class FetchUsers(EntitiesEndpoint, ListEndpoint, IncludeCustomEndpoint):
    FETCH_USERS_PATH = "/v2/objects/%s/uuids"

    def __init__(self, pubnub):
        EntitiesEndpoint.__init__(self, pubnub)
        ListEndpoint.__init__(self)
        IncludeCustomEndpoint.__init__(self)

    def build_path(self):
        return FetchUsers.FETCH_USERS_PATH % self.pubnub.config.subscribe_key

    def create_response(self, envelope):
        return PNFetchUsersResult(envelope)

    def operation_type(self):
        return PNOperationType.PNFetchUsersOperation

    def name(self):
        return "Fetch Users"

    def http_method(self):
        return HttpMethod.GET
