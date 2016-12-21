import tornado
import logging
from tornado import gen
from tornado.testing import AsyncTestCase
import pubnub as pn

from pubnub.callbacks import SubscribeCallback
from pubnub.enums import PNReconnectionPolicy
from pubnub.pnconfiguration import PNConfiguration
from pubnub.pubnub_tornado import PubNubTornado


pn.set_stream_logger('pubnub', logging.DEBUG)


class MySubscribeCallback(SubscribeCallback):
    def status(self, pubnub, status):
        pass

    def message(self, pubnub, message):
        pass

    def presence(self, pubnub, presence):
        pass


class TestPubNubReconnection(AsyncTestCase):
    """
    Tornado Reconnection Manager test design to be invoked alongside with 'subscribe_stub.py'
    helper to start and drop a connection.
    """
    @tornado.testing.gen_test(timeout=300)
    def test_reconnection(self):
        pnconf = PNConfiguration()
        pnconf.publish_key = "demo"
        pnconf.subscribe_key = "demo"
        pnconf.origin = "localhost:8089"
        pnconf.subscribe_request_timeout = 10
        pnconf.reconnect_policy = PNReconnectionPolicy.LINEAR
        pubnub = PubNubTornado(pnconf, custom_ioloop=self.io_loop)
        time_until_open_again = 10

        @gen.coroutine
        def close_soon():
            yield gen.sleep(3)
            pubnub.http.close()
            pubnub.http = None
            print(">>> connection is broken")

        @gen.coroutine
        def open_again():
            yield gen.sleep(time_until_open_again)
            pubnub.http = tornado.httpclient.AsyncHTTPClient(max_clients=PubNubTornado.MAX_CLIENTS)
            print(">>> connection is open again")

        @gen.coroutine
        def countdown():
            yield gen.sleep(2)
            opened = False
            count = time_until_open_again

            while not opened:
                print(">>> %ds to open again" % count)
                count -= 1
                if count <= 0:
                    break
                yield gen.sleep(1)

        my_listener = MySubscribeCallback()
        pubnub.add_listener(my_listener)
        pubnub.subscribe().channels('my_channel').execute()

        yield gen.sleep(1000)
