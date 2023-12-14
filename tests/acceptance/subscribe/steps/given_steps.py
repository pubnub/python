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
    logger = logging.getLogger('pubnub')
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
