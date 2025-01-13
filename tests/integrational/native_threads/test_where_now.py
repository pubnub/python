import unittest
import logging
import pubnub
import threading
import time

from pubnub.pubnub import PubNub, SubscribeListener, NonSubscribeListener
from tests.helper import pnconf_env_copy

pubnub.set_stream_logger('pubnub', logging.DEBUG)


class TestPubNubState(unittest.TestCase):
    def setUp(self):
        self.event = threading.Event()

    def callback(self, response, status):
        self.response = response
        self.status = status
        self.event.set()

    # for subscribe we don't use VCR due to it's limitations with longpolling
    def test_single_channel(self):
        print('test_single_channel')
        pubnub = PubNub(pnconf_env_copy(enable_subscribe=True))
        ch = "wherenow-asyncio-channel"
        uuid = "wherenow-asyncio-uuid"
        pubnub.config.uuid = uuid

        subscribe_listener = SubscribeListener()
        where_now_listener = NonSubscribeListener()
        pubnub.add_listener(subscribe_listener)
        pubnub.subscribe().channels(ch).execute()
        subscribe_listener.wait_for_connect()

        # the delay is needed for the server side to propagate presence
        time.sleep(1)
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

    # for subscribe we don't use VCR due to it's limitations with longpolling
    def test_multiple_channels(self):
        pubnub = PubNub(pnconf_env_copy(enable_subscribe=True))
        ch1 = "state-native-sync-ch-1"
        ch2 = "state-native-sync-ch-2"
        pubnub.config.uuid = "state-native-sync-uuid"
        uuid = pubnub.config.uuid

        subscribe_listener = SubscribeListener()
        where_now_listener = NonSubscribeListener()
        pubnub.add_listener(subscribe_listener)
        pubnub.subscribe().channels([ch1, ch2]).execute()

        subscribe_listener.wait_for_connect()

        # the delay is needed for the server side to propagate presence
        time.sleep(1)
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
