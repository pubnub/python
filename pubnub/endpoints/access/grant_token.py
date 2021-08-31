from pubnub import utils
from pubnub.endpoints.endpoint import Endpoint
from pubnub.errors import PNERR_TTL_MISSING, PNERR_INVALID_META, PNERR_RESOURCES_MISSING
from pubnub.exceptions import PubNubException
from pubnub.enums import HttpMethod, PNOperationType
from pubnub.models.consumer.v3.access_manager import PNGrantTokenResult


class GrantToken(Endpoint):
    GRANT_TOKEN_PATH = "/v3/pam/%s/grant"

    def __init__(self, pubnub):
        Endpoint.__init__(self, pubnub)
        self._ttl = None
        self._meta = None
        self._authorized_uuid = None
        self._channels = []
        self._groups = []
        self._uuids = []

        self._sort_params = True

    def ttl(self, ttl):
        self._ttl = ttl
        return self

    def meta(self, meta):
        self._meta = meta
        return self

    def authorized_uuid(self, uuid):
        self._authorized_uuid = uuid
        return self

    def channels(self, channels):
        self._channels = channels
        return self

    def groups(self, groups):
        self._groups = groups
        return self

    def uuids(self, uuids):
        self._uuids = uuids
        return self

    def custom_params(self):
        return {}

    def build_data(self):
        params = {'ttl': int(self._ttl)}

        permissions = {}
        resources = {}
        patterns = {}

        utils.parse_resources(self._channels, "channels", resources, patterns)
        utils.parse_resources(self._groups, "groups", resources, patterns)
        utils.parse_resources(self._uuids, "uuids", resources, patterns)
        utils.parse_resources(self._uuids, "users", resources, patterns)
        utils.parse_resources(self._uuids, "spaces", resources, patterns)

        permissions['resources'] = resources
        permissions['patterns'] = patterns

        if self._meta:
            if isinstance(self._meta, dict):
                permissions['meta'] = self._meta
            else:
                raise PubNubException(pn_error=PNERR_INVALID_META)
        else:
            permissions['meta'] = {}

        if self._authorized_uuid:
            permissions["uuid"] = self._authorized_uuid

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

    def request_timeout(self):
        return self.pubnub.config.non_subscribe_request_timeout

    def connect_timeout(self):
        return self.pubnub.config.connect_timeout

    def operation_type(self):
        return PNOperationType.PNAccessManagerGrantToken

    def name(self):
        return "Grant Token"

    def validate_resources(self):
        if not any((self._channels, self._groups, self._uuids)):
            raise PubNubException(pn_error=PNERR_RESOURCES_MISSING)

    def validate_ttl(self):
        if not self._ttl:
            raise PubNubException(pn_error=PNERR_TTL_MISSING)
