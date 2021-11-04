import json

from behave import when
import pubnub


def execute_pam_call(context):
    context.grant_result = context.peer.grant_token().channels(
        list(context.resources_to_grant["CHANNEL"].values())
    ).groups(
        list(context.resources_to_grant["CHANNEL_GROUPS"].values())
    ).uuids(
        list(context.resources_to_grant["UUID"].values())
    ).ttl(context.TTL).authorized_uuid(context.authorized_uuid).sync()

    context.token = context.grant_result.result.get_token()
    context.parsed_token = context.peer.parse_token(context.token)


@when("I attempt to grant a token specifying those permissions")
def step_impl(context):
    try:
        execute_pam_call(context)
    except pubnub.exceptions.PubNubException as err:
        context.grant_call_error = json.loads(err._errormsg)


@when("I parse the token")
def step_impl(context):
    context.parsed_token = context.peer.parse_token(context.token_to_parse)


@when("I grant a token specifying those permissions")
def step_impl(context):
    execute_pam_call(context)
