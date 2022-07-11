from pubnub import utils
from pubnub.endpoints.entities.endpoint import EntitiesEndpoint, SpaceEndpoint, SpacesEndpoint, UserEndpoint, \
    UsersEndpoint
from pubnub.enums import PNOperationType, HttpMethod
from pubnub.errors import PNERR_INVALID_SPACE, PNERR_INVALID_USER, PNERR_USER_ID_MISSING, PNERR_SPACE_MISSING
from pubnub.exceptions import PubNubException
from pubnub.models.consumer.entities.membership import PNMembershipsResult
from pubnub.models.consumer.entities.space import Space
from pubnub.models.consumer.entities.user import User


class RemoveSpaceMembers(EntitiesEndpoint, SpaceEndpoint, UsersEndpoint):
    MEMBERSHIP_PATH = "/v2/objects/%s/uuids/%s/channels"

    def __init__(self, pubnub):
        EntitiesEndpoint.__init__(self, pubnub)
        SpaceEndpoint.__init__(self)
        UsersEndpoint.__init__(self)

    def validate_specific_params(self):
        if self._space_id is None or len(self._space_id) == 0:
            raise PubNubException(pn_error=PNERR_SPACE_MISSING)

        self._users = list(self._users)

        if not all(isinstance(user, User) for user in self._users):
            raise PubNubException(pn_error=PNERR_INVALID_USER)

    def build_path(self):
        return RemoveSpaceMembers.MEMBERSHIP_PATH % (self.pubnub.config.subscribe_key, self.pubnub.uuid)

    def build_data(self):
        users = [user.to_payload_dict() for user in self._users]

        payload = {
            "set": [],
            "delete": users
        }
        return utils.write_value_as_string(payload)

    def create_response(self, envelope):
        return PNMembershipsResult(envelope)

    def operation_type(self):
        return PNOperationType.PNRemoveSpaceUsersOperation

    def name(self):
        return "Remove Space Users"

    def http_method(self):
        return HttpMethod.PATCH


class RemoveUserSpaces(EntitiesEndpoint, UserEndpoint, SpacesEndpoint):
    MEMBERSHIP_PATH = "/v2/objects/%s/uuids/%s/channels"

    def __init__(self, pubnub):
        EntitiesEndpoint.__init__(self, pubnub)
        UserEndpoint.__init__(self)
        SpacesEndpoint.__init__(self)

    def validate_specific_params(self):
        if self._user_id is None or len(self._user_id) == 0:
            raise PubNubException(pn_error=PNERR_USER_ID_MISSING)

        self._spaces = list(self._spaces)

        if not all(isinstance(space, Space) for space in self._spaces):
            raise PubNubException(pn_error=PNERR_INVALID_SPACE)

    def build_path(self):
        return RemoveUserSpaces.MEMBERSHIP_PATH % (self.pubnub.config.subscribe_key, self._user_id)

    def build_data(self):
        spaces = [space.to_payload_dict() for space in self._spaces]

        payload = {
            "set": [],
            "delete": spaces
        }
        return utils.write_value_as_string(payload)

    def create_response(self, envelope):
        return PNMembershipsResult(envelope)

    def operation_type(self):
        return PNOperationType.PNRemoveUserSpacesOperation

    def name(self):
        return "Remove User Spaces"

    def http_method(self):
        return HttpMethod.PATCH
