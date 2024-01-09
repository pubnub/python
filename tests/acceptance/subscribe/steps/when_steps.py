from behave import when
from behave.api.async_step import async_run_until_complete
from tests.acceptance.subscribe.environment import PNContext, AcceptanceCallback


@when('I subscribe')
def step_impl(context: PNContext):
    context.pubnub.subscribe().channels('foo').execute()


@when('I subscribe with timetoken {timetoken}')
def step_impl(context: PNContext, timetoken: str): # noqa F811
    callback = AcceptanceCallback()
    context.pubnub.add_listener(callback)
    context.pubnub.subscribe().channels('foo').with_timetoken(int(timetoken)).execute()


"""
Presence engine step definitions
"""


@when("I join '{channel1}', '{channel2}', '{channel3}' channels")
@async_run_until_complete
async def step_impl(context, channel1, channel2, channel3):
    context.pubnub.subscribe().channels([channel1, channel2, channel3]).execute()


@when("I join '{channel1}', '{channel2}', '{channel3}' channels with presence")
@async_run_until_complete
async def step_impl(context, channel1, channel2, channel3):
    context.pubnub.subscribe().channels([channel1, channel2, channel3]).with_presence().execute()
