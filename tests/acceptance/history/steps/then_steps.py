from behave import then
from pubnub.models.consumer.history import PNFetchMessagesResult


@then("I receive a successful response")
def step_impl(context):
    assert context.status.error is None
    assert type(context.result) == PNFetchMessagesResult


@then("history response contains messages with '{type1}' and '{type2}' message types")
def step_impl(context, type1, type2):
    assert all(str(item.message_type) in [type1, type2] for item in context.messages)


@then('history response contains messages with message types')
def step_impl(context):
    assert all('message_type' in item.__dict__.keys() for item in context.messages)


@then('history response contains messages without message types')
def step_impl(context):
    assert all('message_type' not in item.__dict__.keys() for item in context.messages)


@then('history response contains messages without space ids')
def step_impl(context):
    assert all('space_id' not in item.__dict__.keys() for item in context.messages)


@then('history response contains messages with space ids')
def step_impl(context):
    assert all('space_id' in item.__dict__.keys() for item in context.messages)
