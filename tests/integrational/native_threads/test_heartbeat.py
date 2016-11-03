import logging
import unittest
import time
import pubnub as pn

from pubnub.pubnub import PubNub, SubscribeListener
from tests import helper
from tests.helper import pnconf_sub_copy

pn.set_stream_logger('pubnub', logging.DEBUG)


# TODO: add a success heartbeat test

messenger_config = pnconf_sub_copy()
messenger_config.set_presence_timeout(8)
messenger_config.uuid = helper.gen_channel("messenger")

listener_config = pnconf_sub_copy()
listener_config.uuid = helper.gen_channel("listener")


class TestPubNubHeartbeat(unittest.TestCase):
    def test_timeout_event_on_broken_heartbeat(self):
        ch = helper.gen_channel("heartbeat-test")

        pubnub = PubNub(messenger_config)
        pubnub_listener = PubNub(listener_config)

        pubnub.config.uuid = helper.gen_channel("messenger")
        pubnub_listener.config.uuid = helper.gen_channel("listener")

        callback_presence = SubscribeListener()
        callback_messages = SubscribeListener()

        # - connect to :ch-pnpres
        pubnub_listener.add_listener(callback_presence)
        pubnub_listener.subscribe().channels(ch).with_presence().execute()
        callback_presence.wait_for_connect()

        presence_message = callback_presence.wait_for_presence_on(ch)
        assert ch == presence_message.channel
        assert 'join' == presence_message.event
        assert pubnub_listener.uuid == presence_message.uuid

        # - connect to :ch
        pubnub.add_listener(callback_messages)
        pubnub.subscribe().channels(ch).execute()
        callback_messages.wait_for_connect()

        prs_envelope = callback_presence.wait_for_presence_on(ch)
        assert ch == prs_envelope.channel
        assert 'join' == prs_envelope.event
        assert pubnub.uuid == prs_envelope.uuid

        # wait for one heartbeat call
        time.sleep(6)

        # - break messenger heartbeat loop
        pubnub._subscription_manager._stop_heartbeat_timer()

        # - assert for timeout
        presence_message = callback_presence.wait_for_presence_on(ch)
        assert ch == presence_message.channel
        assert 'timeout' == presence_message.event
        assert pubnub.uuid == presence_message.uuid

        pubnub.unsubscribe().channels(ch).execute()
        callback_messages.wait_for_disconnect()

        # - disconnect from :ch-pnpres
        pubnub_listener.unsubscribe().channels(ch).execute()
        callback_presence.wait_for_disconnect()

        pubnub.stop()
        pubnub_listener.stop()
