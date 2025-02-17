from typing import Union, List, Optional
from pubnub import utils
from pubnub.endpoints.endpoint import Endpoint
from pubnub.errors import PNERR_TTL_MISSING, PNERR_INVALID_META, PNERR_RESOURCES_MISSING
from pubnub.exceptions import PubNubException
from pubnub.enums import HttpMethod, PNOperationType
from pubnub.models.consumer.common import PNStatus
from pubnub.models.consumer.v3.access_manager import PNGrantTokenResult
from pubnub.models.consumer.v3.channel import Channel
from pubnub.models.consumer.v3.group import Group
from pubnub.models.consumer.v3.space import Space
from pubnub.models.consumer.v3.user import User
from pubnub.models.consumer.v3.uuid import UUID
from pubnub.structures import Envelope


class PNGrantTokenResultEnvelope(Envelope):
    result: PNGrantTokenResult
    status: PNStatus


class GrantToken(Endpoint):
    GRANT_TOKEN_PATH = "/v3/pam/%s/grant"

    def __init__(self, pubnub, channels: Union[str, List[str]] = None, channel_groups: Union[str, List[str]] = None,
                 users: Union[str, List[str]] = None, spaces: Union[str, List[str]] = None,
                 authorized_user_id: str = None, ttl: Optional[int] = None, meta: Optional[any] = None):
        Endpoint.__init__(self, pubnub)
        self._ttl = ttl
        self._meta = meta
        self._authorized_uuid = authorized_user_id
        self._channels = []
        if channels:
            utils.extend_list(self._channels, channels)
        if spaces:
            utils.extend_list(self._channels, spaces)

        self._groups = []
        if channel_groups:
            utils.extend_list(self._groups, channel_groups)
        self._uuids = []
        if users:
            utils.extend_list(self._uuids, users)

        self._sort_params = True

    def ttl(self, ttl: int) -> 'GrantToken':
        self._ttl = ttl
        return self

    def meta(self, meta: any) -> 'GrantToken':
        self._meta = meta
        return self

    def authorized_uuid(self, uuid: str) -> 'GrantToken':
        self._authorized_uuid = uuid
        return self

    def authorized_user(self, user) -> 'GrantToken':
        self._authorized_uuid = user
        return self

    def spaces(self, spaces: List[Space]) -> 'GrantToken':
        self._channels = spaces
        return self

    def users(self, users: List[User]) -> 'GrantToken':
        self._uuids = users
        return self

    def channels(self, channels: List[Channel]) -> 'GrantToken':
        self._channels = channels
        return self

    def groups(self, groups: List[Group]) -> 'GrantToken':
        self._groups = groups
        return self

    def uuids(self, uuids: List[UUID]) -> 'GrantToken':
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
        utils.parse_resources(self._channels, "spaces", resources, patterns)

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

    def create_response(self, envelope) -> PNGrantTokenResult:
        return PNGrantTokenResult.from_json(envelope['data'])

    def sync(self) -> PNGrantTokenResultEnvelope:
        return PNGrantTokenResultEnvelope(super().sync())

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
