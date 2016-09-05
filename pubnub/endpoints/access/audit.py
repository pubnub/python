import copy

from pubnub import utils
from pubnub.endpoints.endpoint import Endpoint
from pubnub.enums import HttpMethod, PNOperationType
from pubnub.models.consumer.access_manager import PNAccessManagerAuditResult


class Audit(Endpoint):
    AUDIT_PATH = "/v1/auth/audit/sub-key/%s"

    def __init__(self, pubnub):
        Endpoint.__init__(self, pubnub)
        self._auth_keys = []
        self._channels = []
        self._groups = []
        self._read = None
        self._write = None
        self._manage = None
        self._ttl = None

        self._sort_params = True

    def auth_keys(self, auth_keys):
        utils.extend_list(self._auth_keys, auth_keys)
        return self

    def channels(self, channels):
        utils.extend_list(self._channels, channels)
        return self

    def channel_groups(self, channel_groups):
        utils.extend_list(self._groups, channel_groups)
        return self

    def build_params(self):
        params = self.default_params()

        signed_input = (self.pubnub.config.subscribe_key + "\n" + self.pubnub.config.publish_key + "\naudit\n")

        if len(self._auth_keys) > 0:
            params['auth'] = utils.join_items_and_encode(self._auth_keys)

        if len(self._channels) > 0:
            params['channel'] = utils.join_items_and_encode(self._channels)

        if len(self._groups) > 0:
            params['channel-group'] = utils.join_items_and_encode(self._groups)

        params['timestamp'] = str(self.pubnub.timestamp())

        # The SDK version string should be signed unencoded
        params_to_sign = copy.copy(params)
        params_to_sign['pnsdk'] = self.pubnub.sdk_name

        signed_input += utils.prepare_pam_arguments(params_to_sign)
        signature = utils.sign_sha256(self.pubnub.config.secret_key, signed_input)

        params['signature'] = signature

        return params

    def build_path(self):
        return Audit.AUDIT_PATH % self.pubnub.config.subscribe_key

    def http_method(self):
        return HttpMethod.GET

    def validate_params(self):
        self.validate_subscribe_key()
        self.validate_secret_key()

    def create_response(self, envelope):
        return PNAccessManagerAuditResult.from_json(envelope['payload'])

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
