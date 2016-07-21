import json
import os
import threading
import string
import random
import six
import vcr

from copy import copy
from pubnub import utils
from pubnub.pnconfiguration import PNConfiguration

try:
    from mock import patch
except ImportError:
    from unittest.mock import patch

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


def pnconf_copy():
    return copy(pnconf)


def pnconf_sub_copy():
    return copy(pnconf_sub)


def pnconf_enc_copy():
    return copy(pnconf_enc)


def pnconf_pam_copy():
    return copy(pnconf_pam)

sdk_name = "Python-UnitTest"


def url_encode(data):
    return utils.url_encode(utils.write_value_as_string(data))


def url_decode(data):
    return six.moves.urllib.parse.unquote(data)


def gen_channel(prefix):
    return "%s-%s" % (prefix, gen_string(8))


def gen_string(l):
    return ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(l))


pn_vcr = vcr.VCR(
    cassette_library_dir=os.path.dirname((os.path.dirname(os.path.abspath(__file__))))
)


def meta_object_in_query_matcher(r1, r2):
    return assert_request_equal_with_object_in_query(r1, r2, 'meta')


def assert_request_equal_with_object_in_query(r1, r2, query_field_name):
    try:
        assert r1.body == r2.body
        assert r1.headers == r2.headers
        assert r1.host == r2.host
        assert r1.method == r2.method
        assert r1.path == r2.path
        assert r1.port == r2.port
        assert r1.protocol == r2.protocol
        assert r1.scheme == r2.scheme

        for v in r1.query:
            if v[0] == query_field_name:
                for w in r2.query:
                    if w[0] == query_field_name:
                        assert json.loads(v[1]) == json.loads(w[1])
            else:
                for w in r2.query:
                    if w[0] == v[0]:
                        assert w[1] == v[1]

    except AssertionError:
        return False

    return True

pn_vcr.register_matcher('meta_object_in_query', meta_object_in_query_matcher)


def use_cassette_and_stub_time_sleep(cassette_name, filter_query_parameters):
    context = pn_vcr.use_cassette(cassette_name, filter_query_parameters=filter_query_parameters)
    cs = context.cls(path=cassette_name).load(path=cassette_name)

    def _inner(f):
        @patch('time.sleep', return_value=None)
        @six.wraps(f)
        def stubbed(*args):
            with context as cassette:
                largs = list(args)
                largs.pop(1)
                return f(*largs)

        @six.wraps(f)
        def original(*args):
            with context as cassette:
                return f(*args)

        return stubbed if len(cs) > 0 else original
    return _inner


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

    def await(self, timeout=5):
        self.lock.acquire()

        self.t = threading.Timer(timeout, self._release)
        self.t.start()

        while self.count > 0:
            self.lock.wait()

        self.t.cancel()
        self.lock.release()
