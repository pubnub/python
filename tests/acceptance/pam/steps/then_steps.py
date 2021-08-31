from behave import then


@then("the token contains the TTL 60")
def step_impl(context):
    assert context.parsed_token["ttl"] == 60


@then("the token does not contain an authorized uuid")
def step_impl(context):
    assert not context.parsed_token.get("authorized_uuid")


@then("the token has {channel} CHANNEL resource access permissions")
def step_impl(context, channel):
    context.token_resource = context.parsed_token["res"]["chan"].get(channel.strip("'"))
    assert context.token_resource


@then("the token contains the authorized UUID {test_uuid}")
def step_impl(context, test_uuid):
    assert context.parsed_token.get("uuid") == test_uuid.strip('"')


@then("the parsed token output contains the authorized UUID {authorized_uuid}")
def step_impl(context, authorized_uuid):
    assert context.parsed_token.get("uuid") == authorized_uuid.strip('"')


@then("the token has {uuid} UUID resource access permissions")
def step_impl(context, uuid):
    context.token_resource = context.parsed_token["res"]["uuid"].get(uuid.strip("'"))
    assert context.token_resource


@then("the token has {pattern} UUID pattern access permissions")
def step_impl(context, pattern):
    context.token_resource = context.parsed_token["pat"]["uuid"].get(pattern.strip("'"))


@then("the token has {channel_group} CHANNEL_GROUP resource access permissions")
def step_impl(context, channel_group):
    context.token_resource = context.parsed_token["res"]["grp"].get(channel_group.strip("'"))
    assert context.token_resource


@then("the token has {channel_pattern} CHANNEL pattern access permissions")
def step_impl(context, channel_pattern):
    context.token_resource = context.parsed_token["pat"]["chan"].get(channel_pattern.strip("'"))
    assert context.token_resource


@then("the token has {channel_group} CHANNEL_GROUP pattern access permissions")
def step_impl(context, channel_group):
    context.token_resource = context.parsed_token["pat"]["grp"].get(channel_group.strip("'"))
    assert context.token_resource


@then("I see the error message {error} and details {error_details}")
def step_impl(context, error, error_details):
    assert context.grant_call_error["error"]["message"] == error.strip("'")
    assert context.grant_call_error["error"]["details"][0]["message"] == error_details.strip("'")


@then("an error is returned")
def step_impl(context):
    assert context.grant_call_error
