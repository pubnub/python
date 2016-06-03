import threading

from pubnub import utils

from pubnub.pnconfiguration import PNConfiguration

pnconf = PNConfiguration()
pnconf.publish_key = "pub-c-739aa0fc-3ed5-472b-af26-aca1b333ec52"
pnconf.subscribe_key = "sub-c-33f55052-190b-11e6-bfbc-02ee2ddab7fe"

pnconf_enc = PNConfiguration()
pnconf_enc.publish_key = "pub-c-739aa0fc-3ed5-472b-af26-aca1b333ec52"
pnconf_enc.subscribe_key = "sub-c-33f55052-190b-11e6-bfbc-02ee2ddab7fe"
pnconf_enc.cipher_key = "testKey"

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
