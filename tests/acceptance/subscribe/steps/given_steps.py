import logging

from behave import given
from io import StringIO
from pubnub.enums import PNReconnectionPolicy
from pubnub.pubnub_asyncio import PubNubAsyncio, EventEngineSubscriptionManager
from tests.helper import pnconf_env_acceptance_copy
from tests.acceptance.subscribe.environment import AcceptanceCallback, PNContext


@given("the demo keyset with event engine enabled")
def step_impl(context: PNContext):
    context.log_stream = StringIO()
    logger = logging.getLogger('pubnub').getChild('subscribe')
    logger.setLevel(logging.DEBUG)
    logger.handlers = []
    logger.addHandler(logging.StreamHandler(context.log_stream))

    context.pn_config = pnconf_env_acceptance_copy()
    context.pn_config.enable_subscribe = True
    context.pn_config.reconnect_policy = PNReconnectionPolicy.NONE
    context.pubnub = PubNubAsyncio(context.pn_config, subscription_manager=EventEngineSubscriptionManager)

    context.callback = AcceptanceCallback()
    context.pubnub.add_listener(context.callback)


@given("a linear reconnection policy with {max_retries} retries")
def step_impl(context: PNContext, max_retries: str):
    context.pubnub.config.reconnect_policy = PNReconnectionPolicy.LINEAR
    context.pubnub.config.maximum_reconnection_retries = int(max_retries)


"""
Presence engine step definitions
"""


@given("the demo keyset with Presence EE enabled")
def step_impl(context: PNContext):
    context.log_stream_pubnub = StringIO()
    logger = logging.getLogger('pubnub')
    logger.setLevel(logging.DEBUG)
    logger.handlers = []
    logger.addHandler(logging.StreamHandler(context.log_stream_pubnub))

    context.log_stream = StringIO()
    logger = logging.getLogger('pubnub').getChild('presence')
    logger.setLevel(logging.DEBUG)
    logger.handlers = []
    logger.addHandler(logging.StreamHandler(context.log_stream))

    context.pn_config = pnconf_env_acceptance_copy()
    context.pn_config.enable_subscribe = True
    context.pn_config.enable_presence_heartbeat = True
    context.pn_config.reconnect_policy = PNReconnectionPolicy.LINEAR
    context.pn_config.subscribe_request_timeout = 10
    context.pn_config.set_presence_timeout(3)
    context.pubnub = PubNubAsyncio(context.pn_config, subscription_manager=EventEngineSubscriptionManager)

    context.callback = AcceptanceCallback()
    context.pubnub.add_listener(context.callback)


@given("heartbeatInterval set to '{interval}', timeout set to '{timeout}'"
       " and suppressLeaveEvents set to '{suppress_leave}'")
def step_impl(context: PNContext, interval: str, timeout: str, suppress_leave: str):
    context.pn_config.set_presence_timeout_with_custom_interval(int(timeout), int(interval))
    context.pn_config.suppress_leave_events = True if suppress_leave == 'true' else False
