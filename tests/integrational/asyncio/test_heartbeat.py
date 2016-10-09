import logging
import asyncio
import pytest

import pubnub as pn
from pubnub.pubnub_asyncio import PubNubAsyncio, SubscribeListener
from tests import helper
from tests.helper import pnconf_sub_copy

pn.set_stream_logger('pubnub', logging.DEBUG)


messenger_config = pnconf_sub_copy()
messenger_config.set_presence_timeout(8)
messenger_config.uuid = helper.gen_channel("messenger")

listener_config = pnconf_sub_copy()
listener_config.uuid = helper.gen_channel("listener")


@pytest.mark.asyncio
def test_timeout_event_on_broken_heartbeat(event_loop):
    ch = helper.gen_channel("heartbeat-test")

    pubnub = PubNubAsyncio(messenger_config, custom_event_loop=event_loop)
    pubnub_listener = PubNubAsyncio(listener_config, custom_event_loop=event_loop)

    pubnub.config.uuid = helper.gen_channel("messenger")
    pubnub_listener.config.uuid = helper.gen_channel("listener")

    # - connect to :ch-pnpres
    callback_presence = SubscribeListener()
    pubnub_listener.add_listener(callback_presence)
    pubnub_listener.subscribe().channels(ch).with_presence().execute()
    yield from callback_presence.wait_for_connect()

    envelope = yield from callback_presence.wait_for_presence_on(ch)
    assert ch == envelope.channel
    assert 'join' == envelope.event
    assert pubnub_listener.uuid == envelope.uuid

    # - connect to :ch
    callback_messages = SubscribeListener()
    pubnub.add_listener(callback_messages)
    pubnub.subscribe().channels(ch).execute()

    useless_connect_future = callback_messages.wait_for_connect()
    presence_future = asyncio.ensure_future(callback_presence.wait_for_presence_on(ch))

    # - assert join event
    yield from asyncio.wait([useless_connect_future, presence_future])

    prs_envelope = presence_future.result()

    assert ch == prs_envelope.channel
    assert 'join' == prs_envelope.event
    assert pubnub.uuid == prs_envelope.uuid

    # wait for one heartbeat call
    yield from asyncio.sleep(8)

    # - break messenger heartbeat loop
    pubnub._subscription_manager._stop_heartbeat_timer()

    # - assert for timeout
    envelope = yield from callback_presence.wait_for_presence_on(ch)
    assert ch == envelope.channel
    assert 'timeout' == envelope.event
    assert pubnub.uuid == envelope.uuid

    pubnub.unsubscribe().channels(ch).execute()
    yield from callback_messages.wait_for_disconnect()

    # - disconnect from :ch-pnpres
    pubnub_listener.unsubscribe().channels(ch).execute()
    yield from callback_presence.wait_for_disconnect()

    pubnub.stop()
    pubnub_listener.stop()
