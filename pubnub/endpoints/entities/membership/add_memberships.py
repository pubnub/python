from pubnub import utils
from pubnub.endpoints.entities.endpoint import EntitiesEndpoint, SpaceEndpoint, SpacesEndpoint, UserEndpoint, \
    UsersEndpoint
from pubnub.enums import PNOperationType, HttpMethod
from pubnub.errors import PNERR_INVALID_SPACE, PNERR_INVALID_USER, PNERR_USER_ID_MISSING, PNERR_SPACE_MISSING
from pubnub.exceptions import PubNubException

from pubnub.models.consumer.entities.membership import PNMembershipsResult
from pubnub.models.consumer.entities.space import Space
from pubnub.models.consumer.entities.user import User


class AddSpaceMembers(EntitiesEndpoint, SpaceEndpoint, UsersEndpoint):
    MEMBERSHIP_PATH = "/v2/objects/%s/uuids/%s/channels"

    def __init__(self, pubnub):
        EntitiesEndpoint.__init__(self, pubnub)
        SpaceEndpoint.__init__(self)
        UsersEndpoint.__init__(self)

    def validate_specific_params(self):
        if self._space_id is None or len(self._space_id) == 0:
            raise PubNubException(pn_error=PNERR_SPACE_MISSING)
        if type(self._users) is list:
            for user in self._users:
                if type(user) is not User:
                    raise PubNubException(pn_error=PNERR_INVALID_USER)
        elif type(self._users) is User:
            self._users = [self._users]
        else:
            raise PubNubException(pn_error=PNERR_INVALID_USER)

    def build_path(self):
        return AddSpaceMembers.MEMBERSHIP_PATH % (self.pubnub.config.subscribe_key, self.pubnub.uuid)

    def build_data(self):
        users = []
        for user in self._users:
            users.append(user.to_payload_dict())

        payload = {
            "set": users,
            "delete": []
        }
        return utils.write_value_as_string(payload)

    def create_response(self, envelope):
        return PNMembershipsResult(envelope)

    def operation_type(self):
        return PNOperationType.PNAddSpaceUsersOperation

    def name(self):
        return "Add Space Users"

    def http_method(self):
        return HttpMethod.PATCH


class AddUserSpaces(EntitiesEndpoint, UserEndpoint, SpacesEndpoint):
    MEMBERSHIP_PATH = "/v2/objects/%s/uuids/%s/channels"

    def __init__(self, pubnub):
        EntitiesEndpoint.__init__(self, pubnub)
        UserEndpoint.__init__(self)
        SpacesEndpoint.__init__(self)

    def validate_specific_params(self):
        if self._user_id is None or len(self._user_id) == 0:
            raise PubNubException(pn_error=PNERR_USER_ID_MISSING)

        if type(self._spaces) is list:
            for space in self._spaces:
                if type(space) is not Space:
                    raise PubNubException(pn_error=PNERR_INVALID_SPACE)
        elif type(self._spaces) is Space:
            self._spaces = [self._spaces]
        else:
            raise PubNubException(pn_error=PNERR_INVALID_SPACE)

    def build_path(self):
        return AddUserSpaces.MEMBERSHIP_PATH % (self.pubnub.config.subscribe_key, self._user_id)

    def build_data(self):
        spaces = []
        for space in self._spaces:
            spaces.append(space.to_payload_dict())

        payload = {
            "set": spaces,
            "delete": []
        }
        return utils.write_value_as_string(payload)

    def create_response(self, envelope):
        return PNMembershipsResult(envelope)

    def operation_type(self):
        return PNOperationType.PNAddUserSpacesOperation

    def name(self):
        return "Add User Spaces"

    def http_method(self):
        return HttpMethod.PATCH
