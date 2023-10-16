import os
import requests

from tests.acceptance import MOCK_SERVER_URL, CONTRACT_INIT_ENDPOINT, CONTRACT_EXPECT_ENDPOINT
from typing import Union
from pubnub.pubnub import PubNub
from pubnub.crypto import PubNubCryptoModule
from pubnub.crypto_core import PubNubCryptor
from pubnub.pnconfiguration import PNConfiguration
from pubnub.pubnub_asyncio import SubscribeCallback
from behave.runner import Context


class AcceptanceCallback(SubscribeCallback):
    message = None
    status = None
    presence = None

    def status(self, pubnub, status):
        self.status = status

    def message(self, pubnub, message):
        self.message = message

    def presence(self, pubnub, presence):
        self.presence = presence


class PNContext(Context):
    peer: PubNub
    crypto_module: PubNubCryptoModule
    pn_config: PNConfiguration
    subscribe_response: any
    cryptor: Union[list[PubNubCryptor], PubNubCryptor]
    use_random_iv: bool
    cipher_key: str
    outcome: str
    encrypted_file: any
    decrypted_file: any
    input_data: any


def get_crypto_module(context: PNContext):
    cipher_key = context.cipher_key if 'cipher_key' in context else None
    use_random_iv = context.use_random_iv if 'use_random_iv' in context else None

    if not isinstance(context.cryptor, list):
        cryptor_map = {context.cryptor.CRYPTOR_ID: _init_cryptor(context.cryptor, cipher_key, use_random_iv)}
        default_cryptor = context.cryptor
    else:
        cryptor_map = {cryptor.CRYPTOR_ID: _init_cryptor(cryptor, cipher_key, use_random_iv)
                       for cryptor in context.cryptor}
        default_cryptor = context.cryptor[0]

    return PubNubCryptoModule(cryptor_map=cryptor_map, default_cryptor=default_cryptor)


def _init_cryptor(cryptor: PubNubCryptor, cipher_key=None, use_random_iv=None):
    if cryptor.CRYPTOR_ID == '0000':
        return cryptor(cipher_key=cipher_key, use_random_iv=use_random_iv)
    if cryptor.CRYPTOR_ID == 'ACRH':
        return cryptor(cipher_key=cipher_key)


def get_asset_path():
    return os.getcwd() + '/tests/acceptance/encryption/assets/'


def before_scenario(context: Context, feature):
    for tag in feature.tags:
        if "contract" in tag:
            _, contract_name = tag.split("=")
            response = requests.get(MOCK_SERVER_URL + CONTRACT_INIT_ENDPOINT + contract_name)
            assert response


def after_scenario(context: Context, feature):
    for tag in feature.tags:
        if "contract" in tag:
            response = requests.get(MOCK_SERVER_URL + CONTRACT_EXPECT_ENDPOINT)
            assert response

            response_json = response.json()

            assert not response_json["expectations"]["failed"]
            assert not response_json["expectations"]["pending"]
