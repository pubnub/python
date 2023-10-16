from behave import when
from tests.acceptance.encryption.environment import PNContext, get_crypto_module, get_asset_path
from pubnub.exceptions import PubNubException


@when("I decrypt '{filename}' file")
def step_impl(context: PNContext, filename):
    crypto = get_crypto_module(context)
    with open(get_asset_path() + filename, 'rb') as file_handle:
        try:
            file_bytes = file_handle.read()
            crypto.decrypt_file(file_bytes)
            context.outcome = 'success'
        except PubNubException as e:
            context.outcome = str(e).replace('None: ', '')


@when("I encrypt '{filename}' file as '{file_mode}'")
def step_impl(context: PNContext, filename, file_mode):
    crypto = get_crypto_module(context)
    with open(get_asset_path() + filename, 'rb') as fh:
        file_data = fh.read()
        try:
            context.encrypted_file = crypto.encrypt_file(file_data)
            context.decrypted_file = crypto.decrypt_file(context.encrypted_file)
            context.outcome = 'success' if context.decrypted_file == file_data else 'failed'
        except PubNubException as e:
            context.outcome = str(e).replace('None: ', '')


@when("I decrypt '{filename}' file as '{file_mode}'")
def step_impl(context: PNContext, filename, file_mode):
    crypto = get_crypto_module(context)
    with open(get_asset_path() + filename, 'rb') as file_handle:
        try:
            file_bytes = file_handle.read()
            context.decrypted_file = crypto.decrypt_file(file_bytes)
            context.outcome = 'success'
        except PubNubException as e:
            context.outcome = str(e).replace('None: ', '')
