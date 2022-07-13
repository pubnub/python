from pubnub.endpoints.entities.endpoint import EntitiesEndpoint, IncludeCustomEndpoint, UserEndpoint
from pubnub.enums import PNOperationType
from pubnub.enums import HttpMethod
from pubnub.models.consumer.entities.user import PNFetchUserResult


class FetchUser(EntitiesEndpoint, UserEndpoint, IncludeCustomEndpoint):
    FETCH_USER_PATH = "/v2/objects/%s/uuids/%s"

    def __init__(self, pubnub):
        EntitiesEndpoint.__init__(self, pubnub)
        UserEndpoint.__init__(self)
        IncludeCustomEndpoint.__init__(self)

    def build_path(self):
        return FetchUser.FETCH_USER_PATH % (self.pubnub.config.subscribe_key, self._effective_user_id())

    def validate_specific_params(self):
        self._validate_user_id()

    def create_response(self, envelope):
        return PNFetchUserResult(envelope)

    def operation_type(self):
        return PNOperationType.PNFetchUserOperation

    def name(self):
        return "Fetch User"

    def http_method(self):
        return HttpMethod.GET
