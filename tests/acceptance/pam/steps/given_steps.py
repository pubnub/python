from behave import given
from tests.helper import pnconf_pam_acceptance_copy
from pubnub.pubnub import PubNub
from pubnub.models.consumer.v3.channel import Channel
from pubnub.models.consumer.v3.group import Group
from pubnub.models.consumer.v3.uuid import UUID
from tests.helper import PAM_TOKEN_WITH_ALL_PERMS_GRANTED, PAM_TOKEN_EXPIRED, PAM_TOKEN_WITH_PUBLISH_ENABLED


@given("I have a keyset with access manager enabled")
def step_impl(context):
    pubnub_instance = PubNub(pnconf_pam_acceptance_copy())
    context.peer = pubnub_instance

    context.authorized_uuid = None

    context.channels_to_grant = []
    context.resources_to_grant = {
        "CHANNEL": {},
        "UUID": {},
        "CHANNEL_GROUPS": {}
    }


@given("I have a keyset with access manager enabled - without secret key")
def step_impl(context):
    pubnub_instance = PubNub(pnconf_pam_acceptance_copy())
    pubnub_instance.config.secret_key = None
    context.peer_without_secret_key = pubnub_instance


@given("a valid token with permissions to publish with channel {channel}")
def step_impl(context, channel):
    context.token = PAM_TOKEN_WITH_PUBLISH_ENABLED


@given("an expired token with permissions to publish with channel {channel}")
def step_impl(context, channel):
    context.token = PAM_TOKEN_EXPIRED


@given("the token string {token}")
def step_impl(context, token):
    context.token = token.strip("'")


@given("a token")
def step_impl(context):
    context.token = PAM_TOKEN_WITH_PUBLISH_ENABLED


@given("the TTL {ttl}")
def step_impl(context, ttl):
    context.TTL = ttl


@given("token pattern permission READ")
def step_impl(context):
    assert context.token_resource["read"]


@given("token pattern permission WRITE")
def step_impl(context):
    assert context.token_resource["write"]


@given("token pattern permission MANAGE")
def step_impl(context):
    assert context.token_resource["manage"]


@given("token pattern permission UPDATE")
def step_impl(context):
    assert context.token_resource["update"]


@given("token pattern permission JOIN")
def step_impl(context):
    assert context.token_resource["join"]


@given("token pattern permission DELETE")
def step_impl(context):
    assert context.token_resource["delete"]


@given("the {uuid_pattern} UUID pattern access permissions")
def step_impl(context, uuid_pattern):
    context.resource_type_to_grant = "UUID"
    context.resource_name_to_grant = uuid_pattern.strip("'")

    context.resources_to_grant[context.resource_type_to_grant][context.resource_name_to_grant] = UUID.pattern(
        context.resource_name_to_grant
    )


@given("token resource permission WRITE")
def step_impl(context):
    assert context.token_resource["write"]


@given("token resource permission MANAGE")
def step_impl(context):
    assert context.token_resource["manage"]


@given("token resource permission UPDATE")
def step_impl(context):
    assert context.token_resource["update"]


@given("token resource permission JOIN")
def step_impl(context):
    assert context.token_resource["join"]


@given("token resource permission DELETE")
def step_impl(context):
    assert context.token_resource["delete"]


@given("grant pattern permission READ")
def step_impl(context):
    context.resources_to_grant[context.resource_type_to_grant][context.resource_name_to_grant].read()


@given("grant pattern permission WRITE")
def step_impl(context):
    context.resources_to_grant[context.resource_type_to_grant][context.resource_name_to_grant].write()


@given("grant pattern permission GET")
def step_impl(context):
    context.resources_to_grant[context.resource_type_to_grant][context.resource_name_to_grant].get()


@given("grant pattern permission MANAGE")
def step_impl(context):
    context.resources_to_grant[context.resource_type_to_grant][context.resource_name_to_grant].manage()


@given("grant pattern permission UPDATE")
def step_impl(context):
    context.resources_to_grant[context.resource_type_to_grant][context.resource_name_to_grant].update()


@given("grant pattern permission JOIN")
def step_impl(context):
    context.resources_to_grant[context.resource_type_to_grant][context.resource_name_to_grant].join()


@given("grant pattern permission DELETE")
def step_impl(context):
    context.resources_to_grant[context.resource_type_to_grant][context.resource_name_to_grant].delete()


@given("the {group_pattern} CHANNEL_GROUP pattern access permissions")
def step_impl(context, group_pattern):
    context.resource_type_to_grant = "CHANNEL_GROUPS"
    context.resource_name_to_grant = group_pattern.strip("'")

    context.resources_to_grant[context.resource_type_to_grant][context.resource_name_to_grant] = Group.pattern(
        context.resource_name_to_grant
    )


@given("token pattern permission GET")
def step_impl(context):
    assert context.token_resource["get"]


@given("grant resource permission WRITE")
def step_impl(context):
    context.resources_to_grant[context.resource_type_to_grant][context.resource_name_to_grant].write()


@given("grant resource permission GET")
def step_impl(context):
    context.resources_to_grant[context.resource_type_to_grant][context.resource_name_to_grant].get()


@given("grant resource permission MANAGE")
def step_impl(context):
    context.resources_to_grant[context.resource_type_to_grant][context.resource_name_to_grant].manage()


@given("grant resource permission UPDATE")
def step_impl(context):
    context.resources_to_grant[context.resource_type_to_grant][context.resource_name_to_grant].update()


@given("grant resource permission JOIN")
def step_impl(context):
    context.resources_to_grant[context.resource_type_to_grant][context.resource_name_to_grant].join()


@given("grant resource permission DELETE")
def step_impl(context):
    context.resources_to_grant[context.resource_type_to_grant][context.resource_name_to_grant].delete()


@given("the {channel_group} CHANNEL_GROUP resource access permissions")
def step_impl(context, channel_group):
    context.resource_type_to_grant = "CHANNEL_GROUPS"
    context.resource_name_to_grant = channel_group.strip("'")

    context.resources_to_grant[context.resource_type_to_grant][context.resource_name_to_grant] = Group.id(
        context.resource_name_to_grant
    )


@given("the {uuid} UUID resource access permissions")
def step_impl(context, uuid):
    context.resource_type_to_grant = "UUID"
    context.resource_name_to_grant = uuid.strip("'")

    context.resources_to_grant[context.resource_type_to_grant][context.resource_name_to_grant] = UUID.id(
        context.resource_name_to_grant
    )


@given("the {channel_pattern} CHANNEL pattern access permissions")
def step_impl(context, channel_pattern):
    context.resource_type_to_grant = "CHANNEL"
    context.resource_name_to_grant = channel_pattern.strip("'")

    context.resources_to_grant[context.resource_type_to_grant][context.resource_name_to_grant] = Channel.pattern(
        context.resource_name_to_grant
    )


@given("token resource permission GET")
def step_impl(context):
    assert context.token_resource["get"]


@given("I have a known token containing UUID pattern Permissions")
def step_impl(context):
    context.token = PAM_TOKEN_WITH_ALL_PERMS_GRANTED


@given("I have a known token containing UUID resource permissions")
def step_impl(context):
    context.token = PAM_TOKEN_WITH_ALL_PERMS_GRANTED


@given("I have a known token containing an authorized UUID")
def step_impl(context):
    context.token = PAM_TOKEN_WITH_ALL_PERMS_GRANTED


@given("token resource permission READ")
def step_impl(context):
    assert context.token_resource["read"]


@given("the authorized UUID {authorized_uuid}")
def step_impl(context, authorized_uuid):
    context.authorized_uuid = authorized_uuid.strip('"')


@given("the {channel} CHANNEL resource access permissions")
def step_impl(context, channel):
    context.resource_type_to_grant = "CHANNEL"
    context.resource_name_to_grant = channel.strip("'")

    context.resources_to_grant[context.resource_type_to_grant][context.resource_name_to_grant] = Channel.id(
        context.resource_name_to_grant
    )


@given("grant resource permission READ")
def step_impl(context):
    context.resources_to_grant[context.resource_type_to_grant][context.resource_name_to_grant].read()


@given("deny resource permission GET")
def step_impl(context):
    context.resources_to_grant[context.resource_type_to_grant][context.resource_name_to_grant]._get = False


@given("the error status code is {status}")
def step_impl(context, status):
    assert context.pam_call_error["status"] == int(status)


@given("the error message is {err_msg}")
def step_impl(context, err_msg):
    assert context.pam_call_error["error"]["message"] == err_msg.strip("'")


@given("the error source is {err_source}")
def step_impl(context, err_source):
    assert context.pam_call_error["error"]["source"] == err_source.strip("'")


@given("the error detail message is {err_detail}")
def step_impl(context, err_detail):
    err_detail = err_detail.strip("'")
    if err_detail == "not empty":
        assert context.pam_call_error["error"]["details"][0]["message"]
    else:
        assert context.pam_call_error["error"]["details"][0]["message"] == err_detail


@given("the error detail location is {err_detail_location}")
def step_impl(context, err_detail_location):
    assert context.pam_call_error["error"]["details"][0]["location"] == err_detail_location.strip("'")


@given("the error detail location type is {err_detail_location_type}")
def step_impl(context, err_detail_location_type):
    assert context.pam_call_error["error"]["details"][0]["locationType"] == err_detail_location_type.strip("'")


@given("the error service is {service_name}")
def step_impl(context, service_name):
    assert context.pam_call_error["service"] == service_name.strip("'")


@given("the auth error message is {message}")
def step_impl(context, message):
    assert context.pam_call_error["message"] == message.strip("'")
