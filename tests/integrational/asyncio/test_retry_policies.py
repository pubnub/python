import logging
import asyncio
import pytest
import pubnub as pn

from unittest.mock import patch
from pubnub.enums import PNReconnectionPolicy
from pubnub.managers import LinearDelay, ExponentialDelay
from pubnub.pubnub_asyncio import PubNubAsyncio, SubscribeListener

from tests.helper import pnconf_env_copy


pn.set_stream_logger('pubnub', logging.DEBUG)

CONF = dict(enable_subscribe=True, origin='127.0.0.1', ssl=False, connect_timeout=1,
            enable_presence_heartbeat=False)


@pytest.mark.asyncio
async def test_subscribe_retry_policy_none():
    ch = "test-subscribe-asyncio-retry-policy-none"
    pubnub = PubNubAsyncio(pnconf_env_copy(**CONF,
                                           reconnect_policy=PNReconnectionPolicy.NONE))
    listener = SubscribeListener()

    try:
        pubnub.add_listener(listener)
        pubnub.subscribe().channels(ch).execute()

        await asyncio.wait_for(listener.wait_for_disconnect(), timeout=10)
    finally:
        pubnub.unsubscribe_all()
        await pubnub.stop()


@pytest.mark.asyncio
async def test_subscribe_retry_policy_linear():
    def mock_calculate(*args, **kwargs):
        return 0.2

    with patch('pubnub.managers.LinearDelay.calculate', wraps=mock_calculate) as calculate_mock:
        ch = "test-subscribe-asyncio-retry-policy-linear"
        pubnub = PubNubAsyncio(pnconf_env_copy(**CONF,
                                               reconnect_policy=PNReconnectionPolicy.LINEAR))
        listener = SubscribeListener()

        try:
            pubnub.add_listener(listener)
            pubnub.subscribe().channels(ch).execute()

            await asyncio.wait_for(listener.wait_for_disconnect(), timeout=30)
        finally:
            pubnub.unsubscribe_all()
            await pubnub.stop()

        assert calculate_mock.call_count == LinearDelay.MAX_RETRIES


@pytest.mark.asyncio
async def test_subscribe_retry_policy_exponential():
    def mock_calculate(*args, **kwargs):
        return 0.2

    with patch('pubnub.managers.ExponentialDelay.calculate', wraps=mock_calculate) as calculate_mock:
        ch = "test-subscribe-asyncio-retry-policy-exponential"
        pubnub = PubNubAsyncio(pnconf_env_copy(**CONF,
                                               reconnect_policy=PNReconnectionPolicy.EXPONENTIAL))
        listener = SubscribeListener()

        try:
            pubnub.add_listener(listener)
            pubnub.subscribe().channels(ch).execute()

            await asyncio.wait_for(listener.wait_for_disconnect(), timeout=30)
        finally:
            pubnub.unsubscribe_all()
            await pubnub.stop()

        assert calculate_mock.call_count == ExponentialDelay.MAX_RETRIES


@pytest.mark.asyncio
async def test_subscribe_retry_policy_linear_with_max_retries():
    def mock_calculate(*args, **kwargs):
        return 0.2

    with patch('pubnub.managers.LinearDelay.calculate', wraps=mock_calculate) as calculate_mock:
        ch = "test-subscribe-asyncio-retry-policy-linear-max"
        pubnub = PubNubAsyncio(pnconf_env_copy(**CONF,
                                               maximum_reconnection_retries=3,
                                               reconnect_policy=PNReconnectionPolicy.LINEAR))
        listener = SubscribeListener()

        try:
            pubnub.add_listener(listener)
            pubnub.subscribe().channels(ch).execute()

            await asyncio.wait_for(listener.wait_for_disconnect(), timeout=30)
        finally:
            pubnub.unsubscribe_all()
            await pubnub.stop()

        assert calculate_mock.call_count == 3


@pytest.mark.asyncio
async def test_subscribe_retry_policy_exponential_with_max_retries():
    def mock_calculate(*args, **kwargs):
        return 0.2

    with patch('pubnub.managers.ExponentialDelay.calculate', wraps=mock_calculate) as calculate_mock:
        ch = "test-subscribe-asyncio-retry-policy-exponential-max"
        pubnub = PubNubAsyncio(pnconf_env_copy(**CONF,
                                               maximum_reconnection_retries=3,
                                               reconnect_policy=PNReconnectionPolicy.EXPONENTIAL))
        listener = SubscribeListener()

        try:
            pubnub.add_listener(listener)
            pubnub.subscribe().channels(ch).execute()

            await asyncio.wait_for(listener.wait_for_disconnect(), timeout=30)
        finally:
            pubnub.unsubscribe_all()
            await pubnub.stop()

        assert calculate_mock.call_count == 3


@pytest.mark.asyncio
async def test_subscribe_retry_policy_linear_with_custom_interval():
    def mock_calculate(*args, **kwargs):
        return 0.2

    with patch('pubnub.managers.LinearDelay.calculate', wraps=mock_calculate) as calculate_mock:
        ch = "test-subscribe-asyncio-retry-policy-linear-interval"
        pubnub = PubNubAsyncio(pnconf_env_copy(**CONF,
                                               maximum_reconnection_retries=3, reconnection_interval=0.2,
                                               reconnect_policy=PNReconnectionPolicy.LINEAR))
        listener = SubscribeListener()

        try:
            pubnub.add_listener(listener)
            pubnub.subscribe().channels(ch).execute()

            await asyncio.wait_for(listener.wait_for_disconnect(), timeout=30)
        finally:
            pubnub.unsubscribe_all()
            await pubnub.stop()

        assert calculate_mock.call_count == 3
