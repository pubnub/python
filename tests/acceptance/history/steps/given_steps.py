from behave import given
from tests.helper import pnconf_demo_copy
from pubnub.pubnub import PubNub


@given('the demo keyset with enabled storage')
def step_impl(context):
    config = pnconf_demo_copy()
    config.origin = "localhost:8090"
    config.ssl = False
    pubnub_instance = PubNub(config)
    context.peer = pubnub_instance
