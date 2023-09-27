from behave import given
from tests.acceptance.encryption.environment import PNContext
from pubnub.crypto_core import PubNubAesCbcCryptor, PubNubLegacyCryptor


@given("Crypto module with '{cryptor}' cryptor")
def step_impl(context: PNContext, cryptor):
    if cryptor == 'legacy':
        context.cryptor = PubNubLegacyCryptor
    else:
        context.cryptor = PubNubAesCbcCryptor


@given("Crypto module with default '{default_cryptor}' and additional '{additional_cryptor}' cryptors")
def step_impl(context: PNContext, default_cryptor, additional_cryptor):
    context.cryptor = list()
    if default_cryptor == 'legacy':
        context.cryptor.append(PubNubLegacyCryptor)
    else:
        context.cryptor.append(PubNubAesCbcCryptor)

    if additional_cryptor == 'legacy':
        context.cryptor.append(PubNubLegacyCryptor)
    else:
        context.cryptor.append(PubNubAesCbcCryptor)


@given("Legacy code with '{cipher_key}' cipher key and '{vector}' vector")
def step_impl(context: PNContext, cipher_key, vector):
    context.cipher_key = cipher_key
    context.use_random_iv = True if vector == 'random' else False


@given("with '{cipher_key}' cipher key")
def step_impl(context: PNContext, cipher_key):
    context.cipher_key = cipher_key


@given("with '{vector}' vector")
def step_impl(context: PNContext, vector):
    context.use_random_iv = True if vector == 'random' else False
