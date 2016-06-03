import threading

from pubnub import utils

from pubnub.pnconfiguration import PNConfiguration

pub_key = "pub-c-739aa0fc-3ed5-472b-af26-aca1b333ec52"
sub_key = "sub-c-33f55052-190b-11e6-bfbc-02ee2ddab7fe"

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

sdk_name = "Python-UnitTest"


def url_encode(data):
    return utils.url_encode(utils.write_value_as_string(data))


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
