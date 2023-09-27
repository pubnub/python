from behave import then
from tests.acceptance.encryption.environment import PNContext, get_asset_path


@then("I receive '{outcome}'")
def step_impl(context: PNContext, outcome):
    assert outcome == context.outcome


@then("Successfully decrypt an encrypted file with legacy code")
def step_impl(context: PNContext):
    assert context.outcome == 'success'


@then("Decrypted file content equal to the '{filename}' file content")
def step_impl(context: PNContext, filename):
    with open(get_asset_path() + filename, 'rb') as fh:
        file_content = fh.read()
        decrypted = context.decrypted_file
        assert decrypted == file_content
