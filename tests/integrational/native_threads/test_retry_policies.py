import logging
import unittest
import time
import pubnub as pn

from unittest.mock import patch
from pubnub.enums import PNReconnectionPolicy, PNStatusCategory
from pubnub.exceptions import PubNubException
from pubnub.managers import LinearDelay, ExponentialDelay
from pubnub.pubnub import PubNub, SubscribeListener

from tests.helper import pnconf_env_copy


pn.set_stream_logger('pubnub', logging.DEBUG)


class DisconnectListener(SubscribeListener):
    status_result = None
    disconnected = False

    def status(self, pubnub, status):
        if status.category == PNStatusCategory.PNDisconnectedCategory:
            print('Could not connect. Exiting...')
            self.disconnected = True

    def message(self, pubnub, message):
        print(f'Message:\n{message.__dict__}')

    def presence(self, pubnub, presence):
        print(f'Presence:\n{presence.__dict__}')


class TestPubNubRetryPolicies(unittest.TestCase):
    def test_subscribe_retry_policy_none(self):
        ch = "test-subscribe-retry-policy-none"
        pubnub = PubNub(pnconf_env_copy(enable_subscribe=True, daemon=True, origin='127.0.0.1',
                                        reconnect_policy=PNReconnectionPolicy.NONE, enable_presence_heartbeat=True))
        listener = DisconnectListener()

        try:
            pubnub.add_listener(listener)
            pubnub.subscribe().channels(ch).execute()

            while not listener.disconnected:
                time.sleep(0.5)

        except PubNubException as e:
            self.fail(e)

    def test_subscribe_retry_policy_linear(self):
        # we don't test the actual delay calculation here, just everything around it
        def mock_calculate(*args, **kwargs):
            return 0.2

        with patch('pubnub.managers.LinearDelay.calculate', wraps=mock_calculate) as calculate_mock:
            ch = "test-subscribe-retry-policy-linear"
            pubnub = PubNub(pnconf_env_copy(enable_subscribe=True, daemon=True, origin='127.0.0.1',
                                            reconnect_policy=PNReconnectionPolicy.LINEAR,
                                            enable_presence_heartbeat=True))
            listener = DisconnectListener()

            try:
                pubnub.add_listener(listener)
                pubnub.subscribe().channels(ch).execute()

                while not listener.disconnected:
                    time.sleep(0.5)

            except PubNubException as e:
                self.fail(e)

            assert calculate_mock.call_count == LinearDelay.MAX_RETRIES + 1

    def test_subscribe_retry_policy_exponential(self):
        # we don't test the actual delay calculation here, just everything around it
        def mock_calculate(*args, **kwargs):
            return 0.2

        with patch('pubnub.managers.ExponentialDelay.calculate', wraps=mock_calculate) as calculate_mock:
            ch = "test-subscribe-retry-policy-exponential"
            pubnub = PubNub(pnconf_env_copy(enable_subscribe=True, daemon=True, origin='127.0.0.1',
                                            reconnect_policy=PNReconnectionPolicy.EXPONENTIAL,
                                            enable_presence_heartbeat=True))
            listener = DisconnectListener()

            try:
                pubnub.add_listener(listener)
                pubnub.subscribe().channels(ch).execute()

                while not listener.disconnected:
                    time.sleep(0.5)

            except PubNubException as e:
                self.fail(e)

            assert calculate_mock.call_count == ExponentialDelay.MAX_RETRIES + 1

    def test_subscribe_retry_policy_linear_with_max_retries(self):
        # we don't test the actual delay calculation here, just everything around it
        def mock_calculate(*args, **kwargs):
            return 0.2

        with patch('pubnub.managers.LinearDelay.calculate', wraps=mock_calculate) as calculate_mock:
            ch = "test-subscribe-retry-policy-linear"
            pubnub = PubNub(pnconf_env_copy(enable_subscribe=True, daemon=True, origin='127.0.0.1',
                                            maximum_reconnection_retries=3,
                                            reconnect_policy=PNReconnectionPolicy.LINEAR,
                                            enable_presence_heartbeat=True))
            listener = DisconnectListener()

            try:
                pubnub.add_listener(listener)
                pubnub.subscribe().channels(ch).execute()

                while not listener.disconnected:
                    time.sleep(0.5)

            except PubNubException as e:
                self.fail(e)

            assert calculate_mock.call_count == 3

    def test_subscribe_retry_policy_exponential_with_max_retries(self):
        # we don't test the actual delay calculation here, just everything around it
        def mock_calculate(*args, **kwargs):
            return 0.2

        with patch('pubnub.managers.ExponentialDelay.calculate', wraps=mock_calculate) as calculate_mock:
            ch = "test-subscribe-retry-policy-exponential"
            pubnub = PubNub(pnconf_env_copy(enable_subscribe=True, daemon=True, origin='127.0.0.1',
                                            maximum_reconnection_retries=3,
                                            reconnect_policy=PNReconnectionPolicy.EXPONENTIAL,
                                            enable_presence_heartbeat=True))
            listener = DisconnectListener()

            try:
                pubnub.add_listener(listener)
                pubnub.subscribe().channels(ch).execute()

                while not listener.disconnected:
                    time.sleep(0.5)

            except PubNubException as e:
                self.fail(e)

            assert calculate_mock.call_count == 3

    def test_subscribe_retry_policy_linear_with_custom_interval(self):
        # we don't test the actual delay calculation here, just everything around it
        def mock_calculate(*args, **kwargs):
            return 0.2

        with patch('pubnub.managers.LinearDelay.calculate', wraps=mock_calculate) as calculate_mock:
            ch = "test-subscribe-retry-policy-linear"
            pubnub = PubNub(pnconf_env_copy(enable_subscribe=True, daemon=True, origin='127.0.0.1',
                                            maximum_reconnection_retries=3, reconnection_interval=1,
                                            reconnect_policy=PNReconnectionPolicy.LINEAR,
                                            enable_presence_heartbeat=True))
            listener = DisconnectListener()

            try:
                pubnub.add_listener(listener)
                pubnub.subscribe().channels(ch).execute()

                while not listener.disconnected:
                    time.sleep(0.5)

            except PubNubException as e:
                self.fail(e)

            assert calculate_mock.call_count == 0
