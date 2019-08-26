from pubnub import utils
from pubnub.endpoints.endpoint import Endpoint
from pubnub.models.consumer.space import PNCreateSpaceResult
from pubnub.enums import HttpMethod, PNOperationType
from pubnub.exceptions import PubNubException


class CreateSpace(Endpoint):
    CREATE_SPACE_PATH = '/v1/objects/%s/spaces'

    def __init__(self, pubnub):
        Endpoint.__init__(self, pubnub)
        self._include = {}
        self._data = None

    def include(self, data):
        self._include = data
        return self

    def data(self, data):
        assert isinstance(data, dict)
        if 'id' not in data or 'name' not in data:
            raise PubNubException("Space's id or name missing.")
        self._data = data
        return self

    def custom_params(self):
        params = {}
        if self._include:
            params['include'] = self._include
        return params

    def build_data(self):
        return utils.write_value_as_string(self._data)

    def validate_params(self):
        self.validate_subscribe_key()
        if self._data is None:
            raise PubNubException('No data supplied.')

    def build_path(self):
        return CreateSpace.CREATE_SPACE_PATH % (self.pubnub.config.subscribe_key)

    def http_method(self):
        return HttpMethod.POST

    def is_auth_required(self):
        return True

    def create_response(self, envelope):  # pylint: disable=W0221
        return PNCreateSpaceResult(envelope)

    def request_timeout(self):
        return self.pubnub.config.non_subscribe_request_timeout

    def connect_timeout(self):
        return self.pubnub.config.connect_timeout

    def operation_type(self):
        return PNOperationType.PNCreateSpaceOperation

    def name(self):
        return 'Create space'
