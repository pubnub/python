import json

from behave import when
import pubnub
from pubnub.exceptions import PubNubException


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
        context.pam_call_error = json.loads(err._errormsg)


@when("I parse the token")
def step_impl(context):
    context.parsed_token = context.peer.parse_token(context.token)


@when("I grant a token specifying those permissions")
def step_impl(context):
    execute_pam_call(context)


@when("I publish a message using that auth token with channel {channel}")
def step_impl(context, channel):
    context.peer_without_secret_key.set_token(context.token)
    context.publish_result = context.peer_without_secret_key.publish().channel(
        channel.strip("'")
    ).message("Tejjjjj").sync()


@when("I attempt to publish a message using that auth token with channel {channel}")
def step_impl(context, channel):
    try:
        context.peer_without_secret_key.set_token(context.token)
        context.pam_call_result = context.peer_without_secret_key.publish().channel(
            channel.strip("'")
        ).message("Tejjjjj").sync()
    except PubNubException as err:
        context.pam_call_result = err


@when("I revoke a token")
def step_impl(context):
    try:
        context.revoke_result = context.peer.revoke_token(context.token).sync()
    except PubNubException as err:
        context.pam_call_error = json.loads(err._errormsg)
