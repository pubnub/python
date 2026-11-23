"""Shared scenario data of the encryption page for both docsets: literal resource names (NAMES,
read by the janitor through support/resources.py) and the helpers the sync and asyncio tests call outside
the snippet markers. Moved from the old docs-snippets/<docset>/ modules. Coroutine twins of a sync helper
carry an "_async" suffix, and the asyncio tests import them under the sync name.
"""
from pathlib import Path

from Cryptodome.Cipher import AES
from pubnub.pubnub import PubNub

from support import assertions as a
from support.clients import config as client_config
from support.wait import eventually

NAMES = ['cipher_algorithm_experiment']


FIXTURE_BYTES = (Path(__file__).resolve().parent.parent / 'fixtures' / 'sample.gif').read_bytes()


CBC_HEADER_B64 = 'UE5FRA'  # base64 of the "PNED" sentinel that starts every 256-bit AES-CBC payload


def reader(clients, user, module=None, key='my_cipher_key'):
    """A client that reads with the given crypto module, or with none."""
    config = client_config('open', user)
    config.cipher_key = key
    config.cipher_mode = AES.MODE_GCM
    config.fallback_cipher_mode = AES.MODE_CBC
    if module is None:
        config.cipher_key = None
        config.cipher_mode = AES.MODE_CBC
        config.fallback_cipher_mode = None
    else:
        config.crypto_module = module(config)
    client = PubNub(config)
    clients._made.append(client)
    return client


def only_message(seen):
    eventually(lambda: a.eq(len(seen.messages), 1, 'messages received'))
    return seen.messages[0].message
