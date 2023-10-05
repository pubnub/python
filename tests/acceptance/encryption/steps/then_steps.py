from behave import then
from tests.acceptance.encryption.environment import PNContext, get_asset_path
from pubnub.pnconfiguration import PNConfiguration


@then("I receive '{outcome}'")
def step_impl(context: PNContext, outcome):
    assert outcome == context.outcome


@then("Successfully decrypt an encrypted file with legacy code")
def step_impl(context: PNContext):
    config = PNConfiguration()
    config.cipher_key = context.cipher_key
    config.use_random_initialization_vector = context.use_random_iv
    decrypted_legacy = config.file_crypto.decrypt(context.cipher_key, context.encrypted_file)
    assert decrypted_legacy == context.decrypted_file
    assert context.outcome == 'success'


@then("Decrypted file content equal to the '{filename}' file content")
def step_impl(context: PNContext, filename):
    with open(get_asset_path() + filename, 'rb') as fh:
        file_content = fh.read()
        decrypted = context.decrypted_file
        assert decrypted == file_content
