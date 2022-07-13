from pubnub.endpoints.entities.endpoint import EntitiesEndpoint, SpaceEndpoint
from pubnub.enums import PNOperationType
from pubnub.enums import HttpMethod
from pubnub.models.consumer.entities.space import PNRemoveSpaceResult


class RemoveSpace(EntitiesEndpoint, SpaceEndpoint):
    REMOVE_SPACE_PATH = "/v2/objects/%s/channels/%s"

    def __init__(self, pubnub):
        EntitiesEndpoint.__init__(self, pubnub)
        SpaceEndpoint.__init__(self)

    def build_path(self):
        return RemoveSpace.REMOVE_SPACE_PATH % (self.pubnub.config.subscribe_key, self._space_id)

    def validate_specific_params(self):
        self._validate_space_id()

    def create_response(self, envelope):
        return PNRemoveSpaceResult(envelope)

    def operation_type(self):
        return PNOperationType.PNRemoveSpaceOperation

    def name(self):
        return "Remove Space"

    def http_method(self):
        return HttpMethod.DELETE
