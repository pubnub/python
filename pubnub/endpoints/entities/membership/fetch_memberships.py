from pubnub.endpoints.entities.endpoint import EntitiesEndpoint, IncludeCustomEndpoint, ListEndpoint, SpaceEndpoint, \
    UserEndpoint
from pubnub.enums import PNOperationType, HttpMethod
from pubnub.models.consumer.entities.membership import PNSpaceMembershipsResult, PNUserMembershipsResult


class FetchUserMemberships(EntitiesEndpoint, IncludeCustomEndpoint, UserEndpoint, ListEndpoint):
    MEMBERSHIP_PATH = "/v2/objects/%s/uuids/%s/channels"

    def __init__(self, pubnub):
        EntitiesEndpoint.__init__(self, pubnub)
        ListEndpoint.__init__(self)
        IncludeCustomEndpoint.__init__(self)
        UserEndpoint.__init__(self)

    def build_path(self):
        return FetchUserMemberships.MEMBERSHIP_PATH % (self.pubnub.config.subscribe_key, self._user_id)

    def validate_specific_params(self):
        self._validate_user_id()

    def create_response(self, envelope):
        return PNUserMembershipsResult(envelope)

    def operation_type(self):
        return PNOperationType.PNFetchUserMembershipsOperation

    def name(self):
        return "Fetch User Memberships"

    def http_method(self):
        return HttpMethod.GET


class FetchSpaceMemberships(EntitiesEndpoint, IncludeCustomEndpoint, SpaceEndpoint):
    MEMBERSHIP_PATH = "/v2/objects/%s/channels/%s/uuids"

    def __init__(self, pubnub):
        EntitiesEndpoint.__init__(self, pubnub)
        ListEndpoint.__init__(self)
        IncludeCustomEndpoint.__init__(self)
        UserEndpoint.__init__(self)

    def build_path(self):
        return FetchSpaceMemberships.MEMBERSHIP_PATH % (self.pubnub.config.subscribe_key, self._space_id)

    def validate_specific_params(self):
        self._validate_space_id()

    def create_response(self, envelope):
        return PNSpaceMembershipsResult(envelope)

    def operation_type(self):
        return PNOperationType.PNFetchSpaceMembershipsOperation

    def name(self):
        return "Fetch Space Memberships"

    def http_method(self):
        return HttpMethod.GET
