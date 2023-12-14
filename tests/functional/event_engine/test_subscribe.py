import asyncio
import busypie
import logging
import pytest

from unittest.mock import patch
from tests.helper import pnconf_env_copy

from pubnub.pubnub_asyncio import PubNubAsyncio, EventEngineSubscriptionManager, SubscribeCallback
from pubnub.event_engine.models import states
from pubnub.models.consumer.common import PNStatus
from pubnub.enums import PNReconnectionPolicy


class TestCallback(SubscribeCallback):
    _status_called = False
    _message_called = False

    def status_called(self):
        return self._status_called

    def message_called(self):
        return self._message_called

    def status(self, pubnub, status: PNStatus):
        self._status_called = True
        assert isinstance(status, PNStatus)
        logging.debug('calling status_callback()')
        self.status_callback()

    def message(self, pubnub, message):
        self._message_called = True
        assert message.channel == 'foo'
        assert message.message == 'test'
        logging.debug('calling message_callback()')
        self.message_callback()

    def status_callback(self):
        pass

    def message_callback(self):
        pass


@pytest.mark.asyncio
async def test_subscribe():
    loop = asyncio.get_event_loop()
    config = pnconf_env_copy()
    config.enable_subscribe = True
    callback = TestCallback()
    with patch.object(TestCallback, 'status_callback') as status_callback, \
         patch.object(TestCallback, 'message_callback') as message_callback:
        pubnub = PubNubAsyncio(config, subscription_manager=EventEngineSubscriptionManager, custom_event_loop=loop)
        pubnub.add_listener(callback)
        pubnub.subscribe().channels('foo').execute()

        await delayed_publish('foo', 'test', 1)
        await busypie.wait().at_most(5).poll_delay(1).poll_interval(1).until_async(lambda: callback.message_called)
        assert pubnub._subscription_manager.event_engine.get_state_name() == states.ReceivingState.__name__

        status_callback.assert_called()
        message_callback.assert_called()
        pubnub.unsubscribe_all()
        pubnub._subscription_manager.stop()


async def delayed_publish(channel, message, delay):
    pn = PubNubAsyncio(pnconf_env_copy())
    await asyncio.sleep(delay)
    await pn.publish().channel(channel).message(message).future()


@pytest.mark.asyncio
async def test_handshaking():
    config = pnconf_env_copy()
    config.enable_subscribe = True
    config.subscribe_request_timeout = 3
    callback = TestCallback()
    with patch.object(TestCallback, 'status_callback') as status_callback:
        pubnub = PubNubAsyncio(config, subscription_manager=EventEngineSubscriptionManager)
        pubnub.add_listener(callback)
        pubnub.subscribe().channels('foo').execute()
        await busypie.wait().at_most(10).poll_delay(1).poll_interval(1).until_async(lambda: callback.status_called)
        assert pubnub._subscription_manager.event_engine.get_state_name() == states.ReceivingState.__name__
        status_callback.assert_called()
        pubnub._subscription_manager.stop()


@pytest.mark.asyncio
async def test_handshake_failed_no_reconnect():
    config = pnconf_env_copy()
    config.publish_key = 'totally-fake-key'
    config.subscribe_key = 'totally-fake-key'
    config.enable_subscribe = True
    config.reconnect_policy = PNReconnectionPolicy.NONE
    config.maximum_reconnection_retries = 1
    config.subscribe_request_timeout = 2

    callback = TestCallback()
    pubnub = PubNubAsyncio(config, subscription_manager=EventEngineSubscriptionManager)
    pubnub.add_listener(callback)
    pubnub.subscribe().channels('foo').execute()

    def is_state(state):
        return pubnub._subscription_manager.event_engine.get_state_name() == state

    await busypie.wait() \
        .at_most(10) \
        .poll_delay(1) \
        .poll_interval(1) \
        .until_async(lambda: is_state(states.HandshakeFailedState.__name__))

    assert pubnub._subscription_manager.event_engine.get_state_name() == states.HandshakeFailedState.__name__
    pubnub._subscription_manager.stop()
    await pubnub.close_session()


@pytest.mark.asyncio
async def test_handshake_failed_reconnect():
    config = pnconf_env_copy()
    config.publish_key = 'totally-fake-key'
    config.subscribe_key = 'totally-fake-key'
    config.enable_subscribe = True
    config.reconnect_policy = PNReconnectionPolicy.EXPONENTIAL
    config.maximum_reconnection_retries = 2
    config.subscribe_request_timeout = 1

    callback = TestCallback()

    pubnub = PubNubAsyncio(config, subscription_manager=EventEngineSubscriptionManager)
    pubnub.add_listener(callback)
    pubnub.subscribe().channels('foo').execute()

    def is_state(state):
        return pubnub._subscription_manager.event_engine.get_state_name() == state

    await busypie.wait() \
        .at_most(10) \
        .poll_delay(1) \
        .poll_interval(1) \
        .until_async(lambda: is_state(states.HandshakeReconnectingState.__name__))
    assert pubnub._subscription_manager.event_engine.get_state_name() == states.HandshakeReconnectingState.__name__
    pubnub._subscription_manager.stop()
