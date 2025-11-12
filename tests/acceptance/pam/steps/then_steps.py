import json
from behave import then

from pubnub.exceptions import PubNubException


@then("the token contains the TTL 60")
def step_impl(context):
    assert context.parsed_token["ttl"] == 60


@then("the token does not contain an authorized uuid")
def step_impl(context):
    assert not context.parsed_token.get("authorized_uuid")


@then("the token has {channel} CHANNEL resource access permissions")
def step_impl(context, channel):
    context.token_resource = context.parsed_token["resources"]["channels"].get(channel.strip("'"))
    assert context.token_resource

@then("token {data_type} permission {permission}")
def step_impl(context, data_type, permission):
    assert context.token_resource
    assert context.token_resource[permission.lower()] == True


@then("the token contains the authorized UUID {test_uuid}")
def step_impl(context, test_uuid):
    assert context.parsed_token.get("authorized_uuid") == test_uuid.strip('"')


@then("the parsed token output contains the authorized UUID {authorized_uuid}")
def step_impl(context, authorized_uuid):
    assert context.parsed_token.get("authorized_uuid") == authorized_uuid.strip('"')


@then("the token has {uuid} UUID resource access permissions")
def step_impl(context, uuid):
    context.token_resource = context.parsed_token["resources"]["uuids"].get(uuid.strip("'"))
    assert context.token_resource


@then("the token has {pattern} UUID pattern access permissions")
def step_impl(context, pattern):
    context.token_resource = context.parsed_token["patterns"]["uuids"].get(pattern.strip("'"))


@then("the token has {channel_group} CHANNEL_GROUP resource access permissions")
def step_impl(context, channel_group):
    context.token_resource = context.parsed_token["resources"]["groups"].get(channel_group.strip("'"))
    assert context.token_resource


@then("the token has {channel_pattern} CHANNEL pattern access permissions")
def step_impl(context, channel_pattern):
    context.token_resource = context.parsed_token["patterns"]["channels"].get(channel_pattern.strip("'"))
    assert context.token_resource


@then("the token has {channel_group} CHANNEL_GROUP pattern access permissions")
def step_impl(context, channel_group):
    context.token_resource = context.parsed_token["patterns"]["groups"].get(channel_group.strip("'"))
    assert context.token_resource


@then("I see the error message {error} and details {error_details}")
def step_impl(context, error, error_details):
    assert context.pam_call_error["error"]["message"] == error.strip("'")
    assert context.pam_call_error["error"]["details"][0]["message"] == error_details.strip("'")


@then("an error is returned")
def step_impl(context):
    assert context.pam_call_error


@then("I get confirmation that token has been revoked")
def step_impl(context):
    assert context.revoke_result.result.status == 200


@then("an auth error is returned")
def step_impl(context):
    assert isinstance(context.pam_call_result, PubNubException)
    context.pam_call_error = json.loads(context.pam_call_result._errormsg)


@then("the error status code is {error_code}")
def step_impl(context, error_code):
    assert context.pam_call_error['status'] == int(error_code)


@then("the auth error message is '{error_message}'")
@then("the error message is '{error_message}'")
def step_impl(context, error_message):
    if 'message' in context.pam_call_error:
        assert context.pam_call_error['message'] == error_message
    elif 'error' in context.pam_call_error and 'message' in context.pam_call_error['error']:
        assert context.pam_call_error['error']['message'] == error_message
    else:
        raise AssertionError("Unexpected payload: {}".format(context.pam_call_error))


@then("the error detail message is not empty")
def step_impl(context):
    if 'error' in context.pam_call_error and 'details' in context.pam_call_error['error']:
        assert len(context.pam_call_error['error']['details']) > 0
        assert 'message' in context.pam_call_error['error']['details'][0]
        assert len(context.pam_call_error['error']['details'][0]['message']) > 0
    else:
        raise AssertionError("Unexpected payload: {}".format(context.pam_call_error))


@then("the error detail message is '{details_message}'")
def step_impl(context, details_message):
    if 'error' in context.pam_call_error and 'details' in context.pam_call_error['error']:
        assert len(context.pam_call_error['error']['details']) > 0
        assert 'message' in context.pam_call_error['error']['details'][0]
        assert context.pam_call_error['error']['details'][0]['message'] == details_message
    else:
        raise AssertionError("Unexpected payload: {}".format(context.pam_call_error))


@then("the error detail location is '{details_location}'")
def step_impl(context, details_location):
    if 'error' in context.pam_call_error and 'details' in context.pam_call_error['error']:
        assert len(context.pam_call_error['error']['details']) > 0
        assert 'location' in context.pam_call_error['error']['details'][0]
        assert context.pam_call_error['error']['details'][0]['location'] == details_location
    else:
        raise AssertionError("Unexpected payload: {}".format(context.pam_call_error))


@then("the error detail location type is '{details_location_type}'")
def step_impl(context, details_location_type):
    if 'error' in context.pam_call_error and 'details' in context.pam_call_error['error']:
        assert len(context.pam_call_error['error']['details']) > 0
        assert 'locationType' in context.pam_call_error['error']['details'][0]
        assert context.pam_call_error['error']['details'][0]['locationType'] == details_location_type
    else:
        raise AssertionError("Unexpected payload: {}".format(context.pam_call_error))


@then("the error service is '{error_service}'")
def step_impl(context, error_service):
    assert context.pam_call_error['service'] == error_service


@then("the error source is '{error_source}'")
def step_impl(context, error_source):
    if 'error' in context.pam_call_error and 'source' in context.pam_call_error['error']:
        assert context.pam_call_error['error']['source'] == error_source
    else:
        raise AssertionError("Unexpected payload: {}".format(context.pam_call_error))


@then("the result is successful")
def step_impl(context):
    assert context.publish_result.result.timetoken
