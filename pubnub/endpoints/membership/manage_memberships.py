import six

from pubnub import utils
from pubnub.endpoints.endpoint import Endpoint
from pubnub.models.consumer.membership import PNManageMembershipsResult
from pubnub.enums import HttpMethod, PNOperationType
from pubnub.exceptions import PubNubException


class ManageMemberships(Endpoint):
    MANAGE_MEMBERSHIPS_PATH = '/v1/objects/%s/users/%s/spaces'
    MAX_LIMIT = 100

    def __init__(self, pubnub):
        Endpoint.__init__(self, pubnub)
        self._start = None
        self._end = None
        self._limit = ManageMemberships.MAX_LIMIT
        self._count = False
        self._include = None
        self._user_id = None
        self._data = None

    def user_id(self, user_id):
        assert isinstance(user_id, six.string_types)
        self._user_id = user_id
        return self

    def start(self, start):
        assert isinstance(start, six.string_types)
        self._start = start
        return self

    def end(self, end):
        assert isinstance(end, six.string_types)
        self._end = end
        return self

    def limit(self, limit):
        assert isinstance(limit, six.integer_types)
        self._limit = limit
        return self

    def count(self, count):
        self._count = bool(count)
        return self

    def include(self, data):
        self._include = data
        return self

    def data(self, data):
        assert isinstance(data, dict)
        self._data = data
        return self

    def build_data(self):
        if self._data is not None:
            return utils.write_value_as_string(self._data)

    def custom_params(self):
        params = {}

        if self._start is not None:
            params['start'] = self._start

        if self._end is not None and self._start is None:
            params['end'] = self._end

        if self._count is True:
            params['count'] = True

        if self._limit != ManageMemberships.MAX_LIMIT:
            params['limit'] = self._limit

        if self._include:
            params['include'] = utils.join_items(self._include)

        return params

    def build_path(self):
        if self._user_id is None:
            raise PubNubException('Provide user_id.')
        return ManageMemberships.MANAGE_MEMBERSHIPS_PATH % (self.pubnub.config.subscribe_key, self._user_id)

    def http_method(self):
        return HttpMethod.PATCH

    def is_auth_required(self):
        return True

    def validate_params(self):
        self.validate_subscribe_key()
        if self._user_id is None:
            raise PubNubException('Provide user_id.')

    def create_response(self, envelope):   # pylint: disable=W0221
        return PNManageMembershipsResult(envelope)

    def request_timeout(self):
        return self.pubnub.config.non_subscribe_request_timeout

    def connect_timeout(self):
        return self.pubnub.config.connect_timeout

    def operation_type(self):
        return PNOperationType.PNManageMembershipsOperation

    def name(self):
        return 'Update space memberships'
