import warnings
from typing import Any
from copy import deepcopy
from Cryptodome.Cipher import AES
from pubnub.enums import PNHeartbeatNotificationOptions, PNReconnectionPolicy
from pubnub.exceptions import PubNubException
from pubnub.crypto import PubNubCrypto, LegacyCryptoModule, PubNubCryptoModule


class PNConfiguration(object):
    DEFAULT_PRESENCE_TIMEOUT = 300
    DEFAULT_HEARTBEAT_INTERVAL = 280
    ALLOWED_AES_MODES = [AES.MODE_CBC, AES.MODE_GCM]
    DEFAULT_CRYPTO_MODULE = LegacyCryptoModule
    _locked = False

    def __init__(self):
        # TODO: add validation
        self._uuid = None
        self.origin = "ps.pndsn.com"
        self.ssl = True
        self.non_subscribe_request_timeout = 10
        self.subscribe_request_timeout = 310
        self.connect_timeout = 10
        self.subscribe_key = None
        self.publish_key = None
        self.secret_key = None
        self.cipher_key = None
        self._cipher_mode = AES.MODE_CBC
        self._fallback_cipher_mode = None
        self.auth_key = None
        self.filter_expression = None
        self.enable_subscribe = True
        self.crypto_instance = None
        self.file_crypto_instance = None
        self.log_verbosity = False
        self.enable_presence_heartbeat = False
        self.heartbeat_notification_options = PNHeartbeatNotificationOptions.FAILURES
        self.reconnect_policy = PNReconnectionPolicy.EXPONENTIAL
        self.maximum_reconnection_retries = None  # -1 means unlimited/ 0 means no retries
        self.reconnection_interval = None  # if None is left the default value from LinearDelay is used
        self.daemon = False
        self.use_random_initialization_vector = True
        self.suppress_leave_events = False
        self.should_compress = False

        self.heartbeat_default_values = True
        self._presence_timeout = PNConfiguration.DEFAULT_PRESENCE_TIMEOUT
        self._heartbeat_interval = PNConfiguration.DEFAULT_HEARTBEAT_INTERVAL
        self.cryptor = None
        self.file_cryptor = None
        self._crypto_module = None
        self.disable_config_locking = True
        self._locked = False

    def validate(self):
        PNConfiguration.validate_not_empty_string(self.uuid)
        if self.disable_config_locking:
            warnings.warn(DeprecationWarning('Mutable config will be deprecated in the future.'))

    def validate_not_empty_string(value: str):
        assert value and isinstance(value, str) and value.strip() != "", "UUID missing or invalid type"

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
    def cipher_mode(self):
        return self._cipher_mode

    @cipher_mode.setter
    def cipher_mode(self, cipher_mode):
        if cipher_mode not in self.ALLOWED_AES_MODES:
            raise PubNubException('Cipher mode not supported')
        if cipher_mode is not self._cipher_mode:
            self._cipher_mode = cipher_mode
            self.crypto_instance = None

    @property
    def fallback_cipher_mode(self):
        return self._fallback_cipher_mode

    @fallback_cipher_mode.setter
    def fallback_cipher_mode(self, fallback_cipher_mode):
        if fallback_cipher_mode and fallback_cipher_mode not in self.ALLOWED_AES_MODES:
            raise PubNubException('Cipher mode not supported')
        if fallback_cipher_mode is not self._fallback_cipher_mode:
            self._fallback_cipher_mode = fallback_cipher_mode
            self.crypto_instance = None

    @property
    def crypto(self):
        if self._crypto_module:
            return self._crypto_module
        if self.crypto_instance is None:
            self._init_cryptodome()

        return self.crypto_instance

    def _init_cryptodome(self):
        if not self.cryptor:
            from pubnub.crypto import PubNubCryptodome
            self.cryptor = PubNubCryptodome
        self.crypto_instance = self.cryptor(self)

    def _init_file_crypto(self):
        from .crypto import PubNubFileCrypto
        if not self.file_cryptor:
            from pubnub.crypto import PubNubFileCrypto
            self.file_cryptor = PubNubFileCrypto
        self.file_crypto_instance = self.file_cryptor(self)

    @property
    def file_crypto(self) -> PubNubCrypto:
        if not self.file_crypto_instance:
            self._init_file_crypto()

        return self.file_crypto_instance

    @property
    def crypto_module(self):
        return self._crypto_module

    @crypto_module.setter
    def crypto_module(self, crypto_module: PubNubCryptoModule):
        self._crypto_module = crypto_module

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

    @property
    def uuid(self):
        return self._uuid

    @uuid.setter
    def uuid(self, uuid):
        PNConfiguration.validate_not_empty_string(uuid)
        self._uuid = uuid

    @property
    def user_id(self):
        return self._uuid

    @user_id.setter
    def user_id(self, user_id):
        PNConfiguration.validate_not_empty_string(user_id)
        self._uuid = user_id

    def lock(self):
        self.__dict__['_locked'] = False if self.disable_config_locking else True

    def copy(self):
        config_copy = deepcopy(self)
        config_copy.__dict__['_locked'] = False
        return config_copy

    def __setattr__(self, name: str, value: Any) -> None:
        if self._locked:
            warnings.warn(UserWarning('Configuration is locked. Any changes made won\'t have any effect'))
            return
        if name in ['uuid', 'user_id']:
            PNConfiguration.validate_not_empty_string(value)
            self.__dict__['_uuid'] = value
        elif name in ['cipher_mode', 'fallback_cipher_mode', 'crypto_module']:
            self.__dict__[f'_{name}'] = value
        else:
            self.__dict__[name] = value
