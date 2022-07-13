from pubnub.endpoints.entities.endpoint import EntitiesEndpoint, SpaceEndpoint, IncludeCustomEndpoint, \
    CustomAwareEndpoint
from pubnub.enums import PNOperationType
from pubnub.enums import HttpMethod
from pubnub.models.consumer.entities.space import PNCreateSpaceResult
from pubnub.utils import write_value_as_string


class CreateSpace(EntitiesEndpoint, SpaceEndpoint, IncludeCustomEndpoint, CustomAwareEndpoint):
    CREATE_SPACE_PATH = "/v2/objects/%s/channels/%s"

    def __init__(self, pubnub):
        EntitiesEndpoint.__init__(self, pubnub)
        SpaceEndpoint.__init__(self)
        CustomAwareEndpoint.__init__(self)
        IncludeCustomEndpoint.__init__(self)

        self._name = None
        self._description = None
        self._status = None
        self._type = None

    def space_status(self, space_status):
        self._status = space_status
        self._include_status = True
        return self

    def space_type(self, space_type):
        self._type = space_type
        self._include_type = True
        return self

    def set_name(self, name):
        self._name = str(name)
        return self

    def description(self, description):
        self._description = str(description)
        return self

    def validate_specific_params(self):
        self._validate_space_id()

    def build_path(self):
        return CreateSpace.CREATE_SPACE_PATH % (self.pubnub.config.subscribe_key, self._space_id)

    def build_data(self):
        payload = {
            "name": self._name,
            "description": self._description,
            "custom": self._custom
        }
        if self._status:
            payload['status'] = self._status
        if self._type:
            payload['type'] = self._type

        return write_value_as_string(payload)

    def create_response(self, envelope):
        return PNCreateSpaceResult(envelope)

    def operation_type(self):
        return PNOperationType.PNCreateSpaceOperation

    def name(self):
        return "Create space"

    def http_method(self):
        return HttpMethod.PATCH
