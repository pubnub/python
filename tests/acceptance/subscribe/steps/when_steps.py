from behave import when
from tests.acceptance.subscribe.environment import PNContext, AcceptanceCallback


@when('I subscribe')
def step_impl(context: PNContext):
    print(f'WHEN I subscribe {id(context.pubnub)}')
    context.pubnub.subscribe().channels('foo').execute()


@when('I subscribe with timetoken {timetoken}')
def step_impl(context: PNContext, timetoken: str): # noqa F811
    print(f'WHEN I subscribe with TT {id(context.pubnub)}')
    callback = AcceptanceCallback()
    context.pubnub.add_listener(callback)
    context.pubnub.subscribe().channels('foo').with_timetoken(int(timetoken)).execute()
