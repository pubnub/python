from .enums import PNHeartbeatNotificationOptions, PNReconnectionPolicy
from . import utils


class PNConfiguration(object):
    DEFAULT_PRESENCE_TIMEOUT = 300
    DEFAULT_HEARTBEAT_INTERVAL = 280

    def __init__(self):
        # TODO: add validation
        self.uuid = None
        self.origin = "ps.pndsn.com"
        self.ssl = True
        self.non_subscribe_request_timeout = 10
        self.subscribe_request_timeout = 310
        self.connect_timeout = 10
        self.subscribe_key = None
        self.publish_key = None
        self.secret_key = None
        self.cipher_key = None
        self.auth_key = None
        self.filter_expression = None
        self.enable_subscribe = True
        self.crypto_instance = None
        self.file_crypto_instance = None
        self.log_verbosity = False
        self.enable_presence_heartbeat = False
        self.heartbeat_notification_options = PNHeartbeatNotificationOptions.FAILURES
        self.reconnect_policy = PNReconnectionPolicy.NONE
        self.daemon = False
        self.disable_token_manager = False
        self.use_random_initialization_vector = False
        self.suppress_leave_events = False

        self.heartbeat_default_values = True
        self._presence_timeout = PNConfiguration.DEFAULT_PRESENCE_TIMEOUT
        self._heartbeat_interval = PNConfiguration.DEFAULT_HEARTBEAT_INTERVAL

    def validate(self):
        assert self.uuid is None or isinstance(self.uuid, str)

        if self.uuid is None:
            self.uuid = utils.uuid()

    def scheme(self):
        if self.ssl:
            return "https"
        else:
            return "http"

    def scheme_extended(self):
        return self.scheme() + "://"

    def scheme_and_host(self):
        return self.scheme_extended() + self.origin

    def set_presence_timeout_with_custom_interval(self, timeout, interval):
        self.heartbeat_default_values = False
        self._presence_timeout = timeout
        self._heartbeat_interval = interval

    def set_presence_timeout(self, timeout):
        self.set_presence_timeout_with_custom_interval(timeout, (timeout / 2) - 1)

    @property
    def crypto(self):
        if self.crypto_instance is None:
            self._init_cryptodome()

        return self.crypto_instance

    def _init_cryptodome(self):
        from .crypto import PubNubCryptodome
        self.crypto_instance = PubNubCryptodome(self)

    def _init_file_crypto(self):
        from .crypto import PubNubFileCrypto
        self.file_crypto_instance = PubNubFileCrypto(self)

    @property
    def file_crypto(self):
        if not self.file_crypto_instance:
            self._init_file_crypto()

        return self.file_crypto_instance

    @property
    def port(self):
        return 443 if self.ssl == "https" else 80

    @property
    def presence_timeout(self):
        return self._presence_timeout

    @property
    def heartbeat_interval(self):
        return self._heartbeat_interval

        # TODO: set log level
        # TODO: set log level
