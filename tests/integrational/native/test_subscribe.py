import logging
import unittest

# import pydevd as pydevd

import pubnub
from pubnub.callbacks import SubscribeCallback
from pubnub.exceptions import PubNubException
from pubnub.pubnub import PubNub
from tests.helper import CountDownLatch, pnconf_sub

pubnub.set_stream_logger('pubnub', logging.DEBUG)


class TestPubNubSubscribe(unittest.TestCase):
    # @vcr.use_cassette('integrational/fixtures/publish/publish_string_get.yaml',
    #                   filter_query_parameters=['uuid'])
    def test_subscribe_latched(self):
        pubnub = PubNub(pnconf_sub)
        latch = CountDownLatch()

        class MyCallback(SubscribeCallback):
            def __init__(self, l):
                super(MyCallback, self).__init__()

                assert isinstance(l, CountDownLatch)
                self._latch = l
                self.done = False
                self.msg = None

            def status(self, p, status):
                p.publish().channel('ch1').message('hey').sync()

            def presence(self, p, presence):
                pass

            def message(self, p, message):
                self.done = True
                self.msg = message
                self._latch.count_down()

        try:
            callback = MyCallback(latch)
            pubnub.add_listener(callback)
            pubnub.subscribe() \
                .channels(["ch1", "ch2"]) \
                .execute()

            latch.await(10)

            assert callback.done
            assert callback.msg.actual_channel == 'ch1'
            assert callback.msg.subscribed_channel == 'ch1'
            assert callback.msg.message == 'hey'
            assert callback.msg.timetoken > 0

            pubnub.stop()
        except PubNubException as e:
            self.fail(e)
