import re
import busypie

from behave import then
from behave.api.async_step import async_run_until_complete
from pubnub.enums import PNStatusCategory
from pubnub.models.consumer.common import PNStatus
from pubnub.models.consumer.pubsub import PNMessageResult
from tests.acceptance.subscribe.environment import PNContext


@then("I receive the message in my subscribe response")
@async_run_until_complete
async def step_impl(context: PNContext):
    try:
        await busypie.wait() \
            .at_most(15) \
            .poll_delay(1) \
            .poll_interval(1) \
            .until_async(lambda: context.callback.message_result)
    except Exception:
        import ipdb
        ipdb.set_trace()

    response = context.callback.message_result
    assert isinstance(response, PNMessageResult)
    assert response.message is not None
    await context.pubnub.stop()


@then("I observe the following")
@async_run_until_complete
async def step_impl(context):
    def parse_log_line(line: str):
        line_type = 'event' if line.startswith('Triggered event') else 'invocation'
        m = re.search('([A-Za-z])+(Event|Effect)', line)
        name = m.group(0).replace('Effect', '').replace('Event', '')
        name = name.replace('Effect', '').replace('Event', '')
        name = re.sub(r'([A-Z])', r'_\1', name).upper().lstrip('_')
        return (line_type, name)

    normalized_log = [parse_log_line(log_line) for log_line in list(filter(
        lambda line: line.startswith('Triggered event') or line.startswith('Invoke effect'),
        context.log_stream.getvalue().splitlines()
    ))]
    try:
        for index, expected in enumerate(context.table):
            logged_type, logged_name = normalized_log[index]
            expected_type, expected_name = expected
            assert expected_type == logged_type, f'on line {index + 1} => {expected_type} != {logged_type}'
            assert expected_name == logged_name, f'on line {index + 1} => {expected_name} != {logged_name}'
    except Exception as e:
        import ipdb
        ipdb.set_trace()
        raise e


@then("I receive an error in my subscribe response")
@async_run_until_complete
async def step_impl(context: PNContext):
    await busypie.wait() \
        .at_most(15) \
        .poll_delay(1) \
        .poll_interval(1) \
        .until_async(lambda: context.callback.status_result)

    status = context.callback.status_result
    assert isinstance(status, PNStatus)
    assert status.category == PNStatusCategory.PNDisconnectedCategory
    await context.pubnub.stop()


"""
Presence engine step definitions
"""


@then(u'I wait {wait_time} seconds')
@async_run_until_complete
async def step_impl(context: PNContext, wait_time: str):
    await busypie.wait() \
        .at_most(int(wait_time)) \
        .poll_delay(1) \
        .poll_interval(1)


@then(u'I observe the following Events and Invocations of the Presence EE')
@async_run_until_complete
async def step_impl(context):
    pass


@then(u'I wait for getting Presence joined events')
@async_run_until_complete
async def step_impl(context: PNContext):
    pass


@then(u'I receive an error in my heartbeat response')
@async_run_until_complete
async def step_impl(context):
    pass


@then(u'I leave {channel1} and {channel2} channels with presence')
@async_run_until_complete
async def step_impl(context):
    pass


@then(u'I don\'t observe any Events and Invocations of the Presence EE')
@async_run_until_complete
async def step_impl(context):
    pass
