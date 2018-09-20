import unittest
import logging
import time
import pubnub
import threading

from pubnub.pubnub import PubNub, SubscribeListener, NonSubscribeListener
from tests import helper
from tests.helper import pnconf_sub_copy

pubnub.set_stream_logger('pubnub', logging.DEBUG)


class TestPubNubState(unittest.TestCase):
    def setUp(self):
        self.event = threading.Event()

    def callback(self, response, status):
        self.response = response
        self.status = status
        self.event.set()

    def test_single_channel(self):
        pubnub = PubNub(pnconf_sub_copy())
        ch = helper.gen_channel("wherenow-asyncio-channel")
        uuid = helper.gen_channel("wherenow-asyncio-uuid")
        pubnub.config.uuid = uuid

        subscribe_listener = SubscribeListener()
        where_now_listener = NonSubscribeListener()
        pubnub.add_listener(subscribe_listener)
        pubnub.subscribe().channels(ch).execute()

        subscribe_listener.wait_for_connect()

        time.sleep(2)

        pubnub.where_now() \
            .uuid(uuid) \
            .pn_async(where_now_listener.callback)

        if where_now_listener.pn_await() is False:
            self.fail("WhereNow operation timeout")

        result = where_now_listener.result
        channels = result.channels

        assert len(channels) == 1
        assert channels[0] == ch

        pubnub.unsubscribe().channels(ch).execute()
        subscribe_listener.wait_for_disconnect()

        pubnub.stop()

    @unittest.skip("Test fails for unknown reason")
    def test_multiple_channels(self):

        pubnub = PubNub(pnconf_sub_copy())
        ch1 = "state-native-sync-ch-1"
        ch2 = "state-native-sync-ch-2"
        pubnub.config.uuid = "state-native-sync-uuid"
        uuid = pubnub.config.uuid

        subscribe_listener = SubscribeListener()
        where_now_listener = NonSubscribeListener()
        pubnub.add_listener(subscribe_listener)
        pubnub.subscribe().channels([ch1, ch2]).execute()

        subscribe_listener.wait_for_connect()

        time.sleep(2)

        pubnub.where_now() \
            .uuid(uuid) \
            .pn_async(where_now_listener.callback)

        if where_now_listener.pn_await() is False:
            self.fail("WhereNow operation timeout")

        result = where_now_listener.result
        channels = result.channels

        assert len(channels) == 2
        assert ch1 in channels
        assert ch2 in channels

        pubnub.unsubscribe().channels([ch1, ch2]).execute()
        subscribe_listener.wait_for_disconnect()

        pubnub.stop()
