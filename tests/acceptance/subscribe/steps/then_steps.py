import asyncio
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
async def step_impl(ctx: PNContext):
    await busypie.wait() \
        .at_most(15) \
        .poll_delay(1) \
        .poll_interval(1) \
        .until_async(lambda: ctx.callback.message_result)

    response = ctx.callback.message_result
    assert isinstance(response, PNMessageResult)
    assert response.message is not None
    await ctx.pubnub.stop()


@then("I observe the following")
@async_run_until_complete
async def step_impl(ctx):
    def parse_log_line(line: str):
        line_type = 'event' if line.startswith('Triggered event') else 'invocation'
        m = re.search('([A-Za-z])+(Event|Invocation)', line)
        name = m.group(0).replace('Invocation', '').replace('Event', '')
        name = name.replace('Invocation', '').replace('Event', '')
        name = re.sub(r'([A-Z])', r'_\1', name).upper().lstrip('_')
        return (line_type, name)

    normalized_log = [parse_log_line(log_line) for log_line in list(filter(
        lambda line: line.startswith('Triggered event') or line.startswith('Invoke effect'),
        ctx.log_stream.getvalue().splitlines()
    ))]
    for index, expected in enumerate(ctx.table):
        logged_type, logged_name = normalized_log[index]
        expected_type, expected_name = expected
        assert expected_type == logged_type, f'on line {index + 1} => {expected_type} != {logged_type}'
        assert expected_name == logged_name, f'on line {index + 1} => {expected_name} != {logged_name}'


@then("I receive an error in my subscribe response")
@async_run_until_complete
async def step_impl(ctx: PNContext):
    await busypie.wait() \
        .at_most(15) \
        .poll_delay(1) \
        .poll_interval(1) \
        .until_async(lambda: ctx.callback.status_result)

    status = ctx.callback.status_result
    assert isinstance(status, PNStatus)
    assert status.category == PNStatusCategory.PNDisconnectedCategory
    await ctx.pubnub.stop()


"""
Presence engine step definitions
"""


@then("I wait '{wait_time}' seconds")
@async_run_until_complete
async def step_impl(ctx: PNContext, wait_time: str):
    await asyncio.sleep(int(wait_time))


@then(u'I observe the following Events and Invocations of the Presence EE')
@async_run_until_complete
async def step_impl(ctx):
    def parse_log_line(line: str):
        line_type = 'event' if line.startswith('Triggered event') else 'invocation'
        m = re.search('([A-Za-z])+(Event|Invocation)', line)
        name = m.group(0).replace('Invocation', '').replace('Event', '')
        name = name.replace('Invocation', '').replace('Event', '').replace('GiveUp', 'Giveup')
        name = re.sub(r'([A-Z])', r'_\1', name).upper().lstrip('_')

        if name not in ['HEARTBEAT', 'HEARTBEAT_FAILURE', 'HEARTBEAT_SUCCESS', 'HEARTBEAT_GIVEUP']:
            name = name.replace('HEARTBEAT_', '')
        return (line_type, name)

    normalized_log = [parse_log_line(log_line) for log_line in list(filter(
        lambda line: line.startswith('Triggered event') or line.startswith('Invoke effect'),
        ctx.log_stream.getvalue().splitlines()
    ))]

    assert len(normalized_log) >= len(list(ctx.table)), f'Log lenght mismatch!' \
        f'Expected {len(list(ctx.table))}, but got {len(normalized_log)}:\n {normalized_log}'

    for index, expected in enumerate(ctx.table):
        logged_type, logged_name = normalized_log[index]
        expected_type, expected_name = expected
        assert expected_type == logged_type, f'on line {index + 1} => {expected_type} != {logged_type}'
        assert expected_name == logged_name, f'on line {index + 1} => {expected_name} != {logged_name}'


@then(u'I wait for getting Presence joined events')
@async_run_until_complete
async def step_impl(context: PNContext):
    await busypie.wait() \
        .at_most(15) \
        .poll_delay(1) \
        .poll_interval(1) \
        .until_async(lambda: context.callback.presence_result)


@then(u'I receive an error in my heartbeat response')
@async_run_until_complete
async def step_impl(ctx):
    await busypie.wait() \
        .at_most(20) \
        .poll_delay(3) \
        .until_async(lambda: 'HeartbeatGiveUpEvent' in ctx.log_stream.getvalue())


@then("I leave '{channel1}' and '{channel2}' channels with presence")
@async_run_until_complete
async def step_impl(context, channel1, channel2):
    context.pubnub.unsubscribe().channels([channel1, channel2]).execute()


@then(u'I don\'t observe any Events and Invocations of the Presence EE')
@async_run_until_complete
async def step_impl(context):
    assert len(context.log_stream.getvalue().splitlines()) == 0
