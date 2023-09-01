import os
import threading
import string
import random
import urllib

from copy import copy, deepcopy
from pubnub import utils
from pubnub.crypto import PubNubCryptodome
from pubnub.pnconfiguration import PNConfiguration


PAM_TOKEN_WITH_ALL_PERMS_GRANTED = (
    "qEF2AkF0GmEI03xDdHRsGDxDcmVzpURjaGFuoWljaGFubmVsLTEY70NncnChb2NoYW5uZWxfZ3JvdXAtMQVDdXNyoENzcGOgRHV1aWShZ"
    "nV1aWQtMRhoQ3BhdKVEY2hhbqFtXmNoYW5uZWwtXFMqJBjvQ2dycKF0XjpjaGFubmVsX2dyb3VwLVxTKiQFQ3VzcqBDc3BjoER1dWlkoW"
    "pedXVpZC1cUyokGGhEbWV0YaBEdXVpZHR0ZXN0LWF1dGhvcml6ZWQtdXVpZENzaWdYIPpU-vCe9rkpYs87YUrFNWkyNq8CVvmKwEjVinnDrJJc"
)

PAM_TOKEN_EXPIRED = (
    "qEF2AkF0GmEI03xDdHRsGDxDcmVzpURjaGFuoWljaGFubmVsLTEY70NncnChb2NoYW5uZWxfZ3JvdXAtMQ"
    "VDdXNyoENzcGOgRHV1aWShZnV1aWQtMRhoQ3BhdKVEY2hhbqFtXmNoYW5uZWwtXFMqJBjvQ2dycKF0XjpjaG"
    "FubmVsX2dyb3VwLVxTKiQFQ3VzcqBDc3BjoER1dWlkoWpedXVpZC1cUyokGGhEbWV0YaBEdXVpZHR0ZXN0LWF1"
    "dGhvcml6ZWQtdXVpZENzaWdYIPpU-vCe9rkpYs87YUrFNWkyNq8CVvmKwEjVinnDrJJc"
)

PAM_TOKEN_WITH_PUBLISH_ENABLED = (
    "qEF2AkF0GmEI03xDdHRsGDxDcmVzpURjaGFuoWljaGFubmVsLTEY70NncnChb2NoYW5uZWxfZ3JvdXAtMQ"
    "VDdXNyoENzcGOgRHV1aWShZnV1aWQtMRhoQ3BhdKVEY2hhbqFtXmNoYW5uZWwtXFMqJBjvQ2dycKF0XjpjaG"
    "FubmVsX2dyb3VwLVxTKiQFQ3VzcqBDc3BjoER1dWlkoWpedXVpZC1cUyokGGhEbWV0YaBEdXVpZHR0ZXN0LWF1"
    "dGhvcml6ZWQtdXVpZENzaWdYIPpU-vCe9rkpYs87YUrFNWkyNq8CVvmKwEjVinnDrJJc"
)


crypto_configuration = PNConfiguration()
crypto = PubNubCryptodome(crypto_configuration)
crypto.subscribe_request_timeout = 10

DEFAULT_TEST_CIPHER_KEY = "testKey"

pub_key = "pub-c-739aa0fc-3ed5-472b-af26-aca1b333ec52"
sub_key = "sub-c-33f55052-190b-11e6-bfbc-02ee2ddab7fe"

pub_key_mock = "pub-c-mock-key"
sub_key_mock = "sub-c-mock-key"
uuid_mock = "uuid-mock"

pub_key_pam = "pub-c-98863562-19a6-4760-bf0b-d537d1f5c582"
sub_key_pam = "sub-c-7ba2ac4c-4836-11e6-85a4-0619f8945a4f"
sec_key_pam = "sec-c-MGFkMjQxYjMtNTUxZC00YzE3LWFiZGYtNzUwMjdjNmM3NDhk"

pnconf = PNConfiguration()
pnconf.subscribe_request_timeout = 10
pnconf.publish_key = pub_key
pnconf.subscribe_key = sub_key
pnconf.enable_subscribe = False
pnconf.uuid = uuid_mock

pnconf_sub = PNConfiguration()
pnconf_sub.publish_key = pub_key
pnconf_sub.subscribe_request_timeout = 10
pnconf_sub.subscribe_key = sub_key
pnconf_sub.uuid = uuid_mock

pnconf_enc = PNConfiguration()
pnconf_enc.publish_key = pub_key
pnconf_enc.subscribe_request_timeout = 10
pnconf_enc.subscribe_key = sub_key
pnconf_enc.cipher_key = "testKey"
pnconf_enc.enable_subscribe = False
pnconf_enc.uuid = uuid_mock

pnconf_enc_sub = PNConfiguration()
pnconf_enc_sub.publish_key = pub_key
pnconf_enc_sub.subscribe_request_timeout = 10
pnconf_enc_sub.subscribe_key = sub_key
pnconf_enc_sub.cipher_key = "testKey"
pnconf_enc_sub.uuid = uuid_mock

pnconf_pam = PNConfiguration()
pnconf_pam.publish_key = pub_key_pam
pnconf_pam.subscribe_request_timeout = 10
pnconf_pam.subscribe_key = sub_key_pam
pnconf_pam.secret_key = sec_key_pam
pnconf_pam.enable_subscribe = False
pnconf_pam.uuid = uuid_mock


pnconf_pam_stub = PNConfiguration()
pnconf_pam_stub.publish_key = "pub-stub"
pnconf_pam_stub.subscribe_request_timeout = 10
pnconf_pam_stub.subscribe_key = "sub-c-stub"
pnconf_pam_stub.secret_key = "sec-c-stub"
pnconf_pam_stub.uuid = uuid_mock

pnconf_ssl = PNConfiguration()
pnconf_ssl.publish_key = pub_key
pnconf_ssl.subscribe_request_timeout = 10
pnconf_ssl.subscribe_key = sub_key
pnconf_ssl.ssl = True
pnconf_ssl.uuid = uuid_mock

message_count_config = PNConfiguration()
message_count_config.publish_key = 'demo-36'
message_count_config.subscribe_request_timeout = 10
message_count_config.subscribe_key = 'demo-36'
message_count_config.origin = 'balancer1g.bronze.aws-pdx-1.ps.pn'
message_count_config.uuid = uuid_mock

pnconf_demo = PNConfiguration()
pnconf_demo.publish_key = 'demo'
pnconf_demo.subscribe_request_timeout = 10
pnconf_demo.subscribe_key = 'demo'
pnconf_demo.uuid = uuid_mock

file_upload_config = PNConfiguration()
file_upload_config.publish_key = pub_key_mock
file_upload_config.subscribe_request_timeout = 10
file_upload_config.subscribe_key = sub_key_mock
file_upload_config.uuid = uuid_mock

mocked_config = PNConfiguration()
mocked_config.publish_key = pub_key_mock
mocked_config.subscribe_request_timeout = 10
mocked_config.subscribe_key = sub_key_mock
mocked_config.uuid = uuid_mock

hardcoded_iv_config = PNConfiguration()
hardcoded_iv_config.use_random_initialization_vector = False
hardcoded_iv_config.subscribe_request_timeout = 10

# configuration with keys from PN_KEY_* (enabled all except PAM, PUSH and FUNCTIONS)
pnconf_env = PNConfiguration()
pnconf_env.publish_key = os.environ.get('PN_KEY_PUBLISH')
pnconf_env.subscribe_request_timeout = 10
pnconf_env.subscribe_key = os.environ.get('PN_KEY_SUBSCRIBE')
pnconf_env.enable_subscribe = False
pnconf_env.uuid = uuid_mock

# configuration with keys from PN_KEY_* (enabled all except PAM, PUSH and FUNCTIONS) and encryption enabled
pnconf_enc_env = PNConfiguration()
pnconf_enc_env.publish_key = os.environ.get('PN_KEY_PUBLISH')
pnconf_enc_env.subscribe_request_timeout = 10
pnconf_enc_env.subscribe_key = os.environ.get('PN_KEY_SUBSCRIBE')
pnconf_enc_env.cipher_key = "testKey"
pnconf_enc_env.enable_subscribe = False
pnconf_enc_env.uuid = uuid_mock

# configuration with keys from PN_KEY_PAM_* (enabled with all including PAM except PUSH and FUNCTIONS)
pnconf_pam_env = PNConfiguration()
pnconf_pam_env.publish_key = os.environ.get('PN_KEY_PAM_PUBLISH')
pnconf_pam_env.subscribe_request_timeout = 10
pnconf_pam_env.subscribe_key = os.environ.get('PN_KEY_PAM_SUBSCRIBE')
pnconf_pam_env.secret_key = os.environ.get('PN_KEY_PAM_SECRET')
pnconf_pam_env.enable_subscribe = False
pnconf_pam_env.uuid = uuid_mock


def hardcoded_iv_config_copy():
    return copy(hardcoded_iv_config)


def mocked_config_copy():
    return copy(mocked_config)


def pnconf_file_copy():
    return copy(file_upload_config)


def pnconf_copy():
    return copy(pnconf)


def pnconf_enc_copy():
    return copy(pnconf_enc)


def pnconf_sub_copy():
    return copy(pnconf_sub)


def pnconf_enc_sub_copy():
    return copy(pnconf_enc_sub)


def pnconf_pam_copy():
    return deepcopy(pnconf_pam)


def pnconf_pam_stub_copy():
    return deepcopy(pnconf_pam_stub)


def pnconf_pam_acceptance_copy():
    pam_config = copy(pnconf_pam)
    pam_config.origin = "localhost:8090"
    pam_config.ssl = False
    return pam_config


def pnconf_env_acceptance_copy():
    config = copy(pnconf_env)
    config.origin = "localhost:8090"
    config.ssl = False
    config.enable_subscribe = True
    return config


def pnconf_ssl_copy():
    return copy(pnconf_ssl)


def pnconf_mc_copy():
    return copy(message_count_config)


def pnconf_demo_copy():
    return copy(pnconf_demo)


def pnconf_env_copy():
    return copy(pnconf_env)


def pnconf_enc_env_copy():
    return copy(pnconf_enc_env)


def pnconf_pam_env_copy():
    return copy(pnconf_pam_env)


sdk_name = "Python-UnitTest"


def url_encode(data):
    return utils.url_encode(utils.write_value_as_string(data))


def url_decode(data):
    return urllib.parse.unquote(data)


def gen_channel(prefix):
    return "%s-%s" % (prefix, gen_string(8))


def gen_string(length):
    return ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(length))


class CountDownLatch(object):
    def __init__(self, count=1):
        self.count = count
        self.lock = threading.Condition()
        self.done = False
        self.t = None

    def count_down(self):
        self.lock.acquire()
        self.count -= 1

        if self.count <= 0:
            self.done = True
            self.lock.notifyAll()

        if self.t is not None:
            self.t.cancel()
        self.lock.release()

    def _release(self):
        self.lock.acquire()
        self.count = 0
        self.lock.notifyAll()
        self.lock.release()

    def pn_await(self, timeout=5):
        self.lock.acquire()

        self.t = threading.Timer(timeout, self._release)
        self.t.start()

        while self.count > 0:
            self.lock.wait()

        self.t.cancel()
        self.lock.release()
