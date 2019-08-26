import threading
import string
import random
import six

from copy import copy
from pubnub import utils
from pubnub.crypto import PubNubCryptodome
from pubnub.pnconfiguration import PNConfiguration

try:
    from mock import patch
except ImportError:
    from unittest.mock import patch  # noqa: F401

crypto = PubNubCryptodome()


pub_key = "pub-c-739aa0fc-3ed5-472b-af26-aca1b333ec52"
sub_key = "sub-c-33f55052-190b-11e6-bfbc-02ee2ddab7fe"

pub_key_pam = "pub-c-98863562-19a6-4760-bf0b-d537d1f5c582"
sub_key_pam = "sub-c-7ba2ac4c-4836-11e6-85a4-0619f8945a4f"
sec_key_pam = "sec-c-MGFkMjQxYjMtNTUxZC00YzE3LWFiZGYtNzUwMjdjNmM3NDhk"

pnconf = PNConfiguration()
pnconf.publish_key = pub_key
pnconf.subscribe_key = sub_key
pnconf.enable_subscribe = False

pnconf_sub = PNConfiguration()
pnconf_sub.publish_key = pub_key
pnconf_sub.subscribe_key = sub_key

pnconf_enc = PNConfiguration()
pnconf_enc.publish_key = pub_key
pnconf_enc.subscribe_key = sub_key
pnconf_enc.cipher_key = "testKey"
pnconf_enc.enable_subscribe = False

pnconf_enc_sub = PNConfiguration()
pnconf_enc_sub.publish_key = pub_key
pnconf_enc_sub.subscribe_key = sub_key
pnconf_enc_sub.cipher_key = "testKey"

pnconf_pam = PNConfiguration()
pnconf_pam.publish_key = pub_key_pam
pnconf_pam.subscribe_key = sub_key_pam
pnconf_pam.secret_key = sec_key_pam
pnconf_pam.enable_subscribe = False

pnconf_ssl = PNConfiguration()
pnconf_ssl.publish_key = pub_key
pnconf_ssl.subscribe_key = sub_key
pnconf_ssl.ssl = True

message_count_config = PNConfiguration()
message_count_config.publish_key = 'demo-36'
message_count_config.subscribe_key = 'demo-36'
message_count_config.origin = 'balancer1g.bronze.aws-pdx-1.ps.pn'

objects_config = PNConfiguration()
objects_config.publish_key = 'demo'
objects_config.subscribe_key = 'demo'


def pnconf_copy():
    return copy(pnconf)


def pnconf_enc_copy():
    return copy(pnconf_enc)


def pnconf_sub_copy():
    return copy(pnconf_sub)


def pnconf_enc_sub_copy():
    return copy(pnconf_enc_sub)


def pnconf_pam_copy():
    return copy(pnconf_pam)


def pnconf_ssl_copy():
    return copy(pnconf_ssl)


def pnconf_mc_copy():
    return copy(message_count_config)


def pnconf_obj_copy():
    return copy(objects_config)


sdk_name = "Python-UnitTest"


def url_encode(data):
    return utils.url_encode(utils.write_value_as_string(data))


def url_decode(data):
    return six.moves.urllib.parse.unquote(data)


def gen_channel(prefix):
    return "%s-%s" % (prefix, gen_string(8))


def gen_string(l):
    return ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(l))


def gen_decrypt_func(cipher_key):
    def decrypter(entry):
        mr = crypto.decrypt(cipher_key, entry)
        return mr

    return decrypter


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
