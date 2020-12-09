from pubnub import utils
from pubnub.endpoints.endpoint import Endpoint
from pubnub.errors import PNERR_PAM_NO_FLAGS, PNERR_PAM_INVALID_ARGUMENTS
from pubnub.exceptions import PubNubException
from pubnub.enums import HttpMethod, PNOperationType
from pubnub.models.consumer.access_manager import PNAccessManagerGrantResult


class Grant(Endpoint):
    GRANT_PATH = "/v2/auth/grant/sub-key/%s"

    def __init__(self, pubnub):
        Endpoint.__init__(self, pubnub)
        self._auth_keys = []
        self._channels = []
        self._groups = []
        self._uuids = []
        self._read = None
        self._write = None
        self._manage = None
        self._delete = None
        self._ttl = None
        self._get = None
        self._update = None
        self._join = None

        self._sort_params = True

    def get(self, flag):
        self._get = flag
        return self

    def update(self, flag):
        self._update = flag
        return self

    def join(self, flag):
        self._join = flag
        return self

    def uuids(self, uuids):
        utils.extend_list(self._uuids, uuids)
        return self

    def auth_keys(self, auth_keys):
        utils.extend_list(self._auth_keys, auth_keys)
        return self

    def channels(self, channels):
        utils.extend_list(self._channels, channels)
        return self

    def channel_groups(self, channel_groups):
        utils.extend_list(self._groups, channel_groups)
        return self

    def read(self, flag):
        self._read = flag
        return self

    def write(self, flag):
        self._write = flag
        return self

    def manage(self, flag):
        self._manage = flag
        return self

    def delete(self, flag):
        self._delete = flag
        return self

    def ttl(self, ttl):
        self._ttl = ttl
        return self

    def encoded_params(self):
        params = {}

        if self._auth_keys:
            params['auth'] = utils.join_items_and_encode(self._auth_keys)

        if self._channels:
            params['channel'] = utils.join_channels(self._channels)

        if self._groups:
            params['channel-group'] = utils.join_items_and_encode(self._groups)

        return params

    def custom_params(self):
        params = {}

        if self._read is not None:
            params['r'] = '1' if self._read is True else '0'
        if self._write is not None:
            params['w'] = '1' if self._write is True else '0'
        if self._manage is not None:
            params['m'] = '1' if self._manage is True else '0'
        if self._delete is not None:
            params['d'] = '1' if self._delete is True else '0'
        if self._get is not None:
            params['g'] = '1' if self._get is True else '0'
        if self._update is not None:
            params['u'] = '1' if self._update is True else '0'
        if self._join is not None:
            params['j'] = '1' if self._join is True else '0'

        if self._auth_keys:
            params['auth'] = utils.join_items(self._auth_keys)

        if self._channels:
            params['channel'] = utils.join_items(self._channels)

        if self._groups:
            params['channel-group'] = utils.join_items(self._groups)

        if self._uuids:
            params['target-uuid'] = utils.join_items(self._uuids)

        if self._ttl is not None:
            params['ttl'] = str(int(self._ttl))

        return params

    def build_path(self):
        return Grant.GRANT_PATH % self.pubnub.config.subscribe_key

    def http_method(self):
        return HttpMethod.GET

    def validate_params(self):
        self.validate_subscribe_key()
        self.validate_secret_key()
        self.validate_publish_key()
        # self.validate_channels_and_groups()

        if self._channels and self._groups and self._uuids:
            raise PubNubException(
                pn_error=PNERR_PAM_INVALID_ARGUMENTS,
                errormsg="Grants for channels or channelGroups can't be changed together with grants for UUIDs")

        if self._uuids and not self._auth_keys:
            raise PubNubException(pn_error=PNERR_PAM_INVALID_ARGUMENTS, errormsg="UUIDs grant management require "
                                                                                 "providing non empty authKeys"
                                  )

        if self._write is None and self._read is None and self._manage is None and self._get is None \
                and self._update is None and self._join is None:
            raise PubNubException(pn_error=PNERR_PAM_NO_FLAGS)

    def create_response(self, envelope):
        return PNAccessManagerGrantResult.from_json(envelope['payload'])

    def is_auth_required(self):
        return False

    def affected_channels(self):
        return self._channels

    def affected_channels_groups(self):
        return self._groups

    def request_timeout(self):
        return self.pubnub.config.non_subscribe_request_timeout

    def connect_timeout(self):
        return self.pubnub.config.connect_timeout

    def operation_type(self):
        return PNOperationType.PNAccessManagerGrant

    def name(self):
        return "Grant"
