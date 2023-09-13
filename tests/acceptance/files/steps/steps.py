from behave import given, when, then
from pubnub.exceptions import PubNubException
from tests.helper import pnconf_demo_copy
from pubnub.pubnub import PubNub


@given(u'the demo keyset')
def step_impl(context):
    config = pnconf_demo_copy()
    config.origin = "localhost:8090"
    config.ssl = False
    pubnub_instance = PubNub(config)
    context.peer = pubnub_instance


@when(u'I send a file with \'{space_id}\' space id and \'{type}\' type')
def step_impl(context, space_id, type):
    try:
        with open('tests/acceptance/files/test.txt', 'rb') as file_object:
            envelope = context.peer.send_file().channel('test').message('test').should_store(True).ttl(200). \
                file_name('test.txt').file_object(file_object).space_id(space_id).type(type).sync()
            context.status = envelope.status
            context.result = envelope.result
    except PubNubException as error:
        context.status = error


@then(u'I receive a successful response')
def step_impl(context):
    assert context.status.error is None
    assert 'file_id' in context.result.__dict__


@then(u'I receive an error response')
def step_impl(context):
    assert type(context.status) == PubNubException


@when(u'I list files')
def step_impl(context):
    envelope = context.peer.list_files().channel('test').sync()
    context.status = envelope.status
    context.result = envelope.result


@then(u'I receive successful response')
def step_impl(context):
    assert type(context.status) is PubNubException or context.status.error is None


@when(u'I publish file message')
def step_impl(context):
    try:
        envelope = context.peer.publish_file_message().channel('test').message('test').should_store(True).ttl(200).\
            file_name('test.txt').file_id('1338').sync()
        context.status = envelope.status
        context.result = envelope.result
    except PubNubException as error:
        context.status = error


@then(u'I receive error response')
def step_impl(context):
    assert type(context.status) is PubNubException or context.status.error is True


@when(u'I delete file')
def step_impl(context):
    envelope = context.peer.delete_file().channel('test').file_name('test.txt').file_id('1338').sync()
    context.status = envelope.status
    context.result = envelope.result


@when(u'I download file')
def step_impl(context):
    envelope = context.peer.get_file_url().channel('test').file_name('test.txt').file_id('1338').sync()
    context.status = envelope.status
    context.result = envelope.result


@when(u'I send file')
def step_impl(context):
    try:
        with open('tests/acceptance/files/test.txt', 'rb') as file_object:
            envelope = context.peer.send_file().channel('test').message('test').should_store(True).ttl(200). \
                file_name('test.txt').file_object(file_object).sync()
            context.status = envelope.status
            context.result = envelope.result
    except PubNubException as error:
        context.status = error
