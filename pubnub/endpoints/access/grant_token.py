from pubnub import utils
from pubnub.endpoints.endpoint import Endpoint
from pubnub.errors import PNERR_RESOURCES_MISSING, PNERR_TTL_MISSING, PNERR_INVALID_META
from pubnub.exceptions import PubNubException
from pubnub.enums import HttpMethod, PNOperationType
from pubnub.models.consumer.v3.access_manager import PNGrantTokenResult


class GrantToken(Endpoint):
    GRANT_TOKEN_PATH = "/v3/pam/%s/grant"

    READ = 1
    WRITE = 2
    MANAGE = 4
    DELETE = 8
    CREATE = 16

    def __init__(self, pubnub):
        Endpoint.__init__(self, pubnub)
        self._ttl = None
        self._meta = None
        self._channelList = []
        self._groupList = []
        self._userList = []
        self._spaceList = []

        self._sort_params = True

    def ttl(self, ttl):
        self._ttl = ttl
        return self

    def meta(self, meta):
        self._meta = meta
        return self

    def users(self, users):
        self._userList = users
        return self

    def spaces(self, spaces):
        self._spaceList = spaces
        return self

    def custom_params(self):
        return {}

    def build_data(self):
        params = {'ttl': str(int(self._ttl))}

        permissions = {}
        resources = {}
        patterns = {}

        utils.parse_resources(self._channelList, "channels", resources, patterns)
        utils.parse_resources(self._groupList, "groups", resources, patterns)
        utils.parse_resources(self._userList, "users", resources, patterns)
        utils.parse_resources(self._spaceList, "spaces", resources, patterns)

        permissions['resources'] = resources
        permissions['patterns'] = patterns

        if self._meta is not None:
            if isinstance(self._meta, dict):
                permissions['meta'] = self._meta
            else:
                raise PubNubException(pn_error=PNERR_INVALID_META)
        else:
            permissions['meta'] = {}

        params['permissions'] = permissions

        return utils.write_value_as_string(params)

    def build_path(self):
        return GrantToken.GRANT_TOKEN_PATH % self.pubnub.config.subscribe_key

    def http_method(self):
        return HttpMethod.POST

    def validate_params(self):
        self.validate_subscribe_key()
        self.validate_secret_key()
        self.validate_ttl()
        self.validate_resources()

    def create_response(self, envelope):
        return PNGrantTokenResult.from_json(envelope['data'])

    def is_auth_required(self):
        return False

    def affected_channels(self):
        # generate a list of channels when they become supported in PAMv3
        return None

    def affected_channels_groups(self):
        # generate a list of groups when they become supported in PAMv3
        return None

    def request_timeout(self):
        return self.pubnub.config.non_subscribe_request_timeout

    def connect_timeout(self):
        return self.pubnub.config.connect_timeout

    def operation_type(self):
        return PNOperationType.PNAccessManagerGrantToken

    def name(self):
        return "Grant Token"

    def validate_resources(self):
        if (self._userList is None or len(self._userList) == 0) and \
           (self._spaceList is None or len(self._spaceList) == 0):
            raise PubNubException(pn_error=PNERR_RESOURCES_MISSING)

    def validate_ttl(self):
        if self._ttl is None:
            raise PubNubException(pn_error=PNERR_TTL_MISSING)
