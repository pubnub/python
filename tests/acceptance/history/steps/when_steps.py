from behave import when


@when("I fetch message history for '{channel}' channel")
def step_impl(context, channel):
    envelope = context.peer.fetch_messages().channels(channel).include_message_type(True).include_type(True).sync()
    context.status = envelope.status
    context.result = envelope.result
    context.messages = envelope.result.channels[channel]


@when("I fetch message history with '{flag}' set to '{value}' for '{channel}' channel")
def step_impl(context, flag, value, channel):
    request = context.peer.fetch_messages().channels(channel)
    value = True if value == 'true' else False
    if flag == 'includeMessageType':
        request.include_message_type(value)
    if flag == 'includeType':
        request.include_type(value)
    if flag == 'includeSpaceId':
        request.include_space_id(value)

    envelope = request.sync()
    context.status = envelope.status
    context.result = envelope.result
    context.messages = envelope.result.channels[channel]
