"""Docs page: encryption (sync only, the asyncio docs have no encryption page).

Source: docs/sdks/python/api-reference/encryption.md. The client of each docs sample is built by the sample itself,
so the page snippets show the crypto module lines on a PNConfiguration that the step created.
"""
import os
import tempfile
from pathlib import Path

from Cryptodome.Cipher import AES
from pubnub.crypto import AesCbcCryptoModule, LegacyCryptoModule, PubNubAesCbcCryptor, PubNubCryptoModule
from pubnub.enums import PNStatusCategory
from pubnub.exceptions import PubNubException
from pubnub.pubnub import PubNub

from harness import assertions as a
from harness import names, world
from harness.listeners import listen
from harness.step import step
from harness.wait import eventually

FIXTURE_BYTES = (Path(__file__).resolve().parent.parent / 'fixtures' / 'sample.gif').read_bytes()
CBC_HEADER_B64 = 'UE5FRA'  # base64 of the "PNED" sentinel that starts every 256-bit AES-CBC payload


def reader(clients, user, module=None, key='my_cipher_key'):
    """A client that reads with the given crypto module, or with none."""
    config = world.config('open', user)
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


@step('crypto_module_aes_cbc', role='open')
def test_aes_cbc_crypto_module(clients):
    channel = names.with_suffix('my_channel')
    secret = {'secret': 'knights who say ni'}
    config = world.config('open', 'encrypting_publisher')

    # snippet.crypto_module_aes_cbc
    #  encrypts using 256-bit AES-CBC cipher (recommended)
    #  decrypts data encrypted with the legacy (AES and GCM) and the 256-bit AES-CBC ciphers
    config.cipher_key = "my_cipher_key"
    config.cipher_mode = AES.MODE_GCM  # optional, used for the legacy module only
    config.fallback_cipher_mode = AES.MODE_CBC  # optional, used for the legacy module only
    config.crypto_module = AesCbcCryptoModule(config)
    pubnub = PubNub(config)
    # snippet.end
    clients._made.append(pubnub)
    same_key = listen(reader(clients, 'same_key', AesCbcCryptoModule), channel)
    no_key = listen(reader(clients, 'no_key'), channel)
    wrong_key = listen(reader(clients, 'wrong_key', AesCbcCryptoModule, key='another_cipher_key'), channel)

    envelope = pubnub.publish().channel(channel).message(secret).sync()

    a.timetoken(envelope.result.timetoken)
    a.eq(only_message(same_key), secret, 'a subscriber with the same key reads the message')
    unreadable = only_message(no_key)
    a.ok(isinstance(unreadable, str) and unreadable.startswith(CBC_HEADER_B64), 'without a key the 256-bit payload')
    a.ok('ni' not in unreadable, 'the plain text is not in the payload')
    a.ok(isinstance(only_message(wrong_key), str), 'a wrong key leaves the payload encrypted')
    a.ok(only_message(wrong_key) != secret, 'a wrong key does not read the message')
    a.ok(wrong_key.messages[0].error is not None, 'the wrong key is reported as an error on the message')
    a.contains(wrong_key.categories, PNStatusCategory.PNDecryptionErrorCategory, 'decryption error status')


@step('crypto_module_legacy', role='open')
def test_legacy_crypto_module(clients):
    channel = names.with_suffix('my_channel')
    secret = {'secret': 'legacy knights'}
    config = world.config('open', 'legacy_publisher')

    # snippet.crypto_module_legacy
    #  encrypts with 128-bit cipher key entropy (legacy) with GCM
    #  decrypts data encrypted with the legacy (AES and GCM) and the 256-bit AES-CBC ciphers
    config.cipher_key = "my_cipher_key"
    config.cipher_mode = AES.MODE_GCM  # optional, used for the legacy module only
    config.fallback_cipher_mode = AES.MODE_CBC  # optional, used for the legacy module only
    config.crypto_module = LegacyCryptoModule(config)
    pubnub = PubNub(config)
    # snippet.end
    clients._made.append(pubnub)
    legacy_reader = listen(reader(clients, 'legacy_reader', LegacyCryptoModule), channel)
    cbc_reader = listen(reader(clients, 'cbc_reader', AesCbcCryptoModule), channel)
    no_key = listen(reader(clients, 'no_key'), channel)

    pubnub.publish().channel(channel).message(secret).sync()

    a.eq(only_message(legacy_reader), secret, 'the legacy module reads its own payload')
    a.eq(only_message(cbc_reader), secret, 'the 256-bit module reads the legacy payload')
    unreadable = only_message(no_key)
    a.ok(isinstance(unreadable, str), 'without a key the payload is a string')
    a.ok(not unreadable.startswith(CBC_HEADER_B64), 'the legacy payload has no 256-bit header')
    a.ok(unreadable != secret and 'legacy' not in unreadable, 'the plain text is not in the payload')

    # The other direction: a message from a 256-bit client is readable by the legacy module
    cbc_config = world.config('open', 'cbc_publisher')
    cbc_config.cipher_key = 'my_cipher_key'
    cbc_config.cipher_mode = AES.MODE_GCM
    cbc_config.fallback_cipher_mode = AES.MODE_CBC
    cbc_config.crypto_module = AesCbcCryptoModule(cbc_config)
    cbc_publisher = PubNub(cbc_config)
    clients._made.append(cbc_publisher)
    cbc_publisher.publish().channel(channel).message('from-cbc').sync()
    eventually(lambda: a.contains([m.message for m in legacy_reader.messages], 'from-cbc', 'legacy reads 256-bit'))
    eventually(lambda: a.eq(len(no_key.messages), 2, 'second message arrived'))
    a.ok(no_key.messages[1].message.startswith(CBC_HEADER_B64), 'the 256-bit payload carries its header')


@step('crypto_module_partial', role='open')
def test_partial_crypto_module(clients):
    config = world.config('open', 'partial_crypto')
    pubnub = PubNub(config)  # pubnub instance without encryption
    clients._made.append(pubnub)
    other = PubNub(world.config('open', 'other_key'))
    clients._made.append(other)
    other.crypto = PubNubCryptoModule({
        PubNubAesCbcCryptor.CRYPTOR_ID: PubNubAesCbcCryptor('anotherCipherKey')
    }, PubNubAesCbcCryptor)
    a.eq(pubnub.crypto, None, 'no crypto module before the sample')

    # snippet.crypto_module_partial
    pubnub.crypto = PubNubCryptoModule({
        PubNubAesCbcCryptor.CRYPTOR_ID: PubNubAesCbcCryptor('myCipherKey')
    }, PubNubAesCbcCryptor)
    encrypted = pubnub.crypto.encrypt('My Secret Text')  # encrypted wih AES cryptor and `myCipherKey` cipher key
    decrypted = pubnub.crypto.decrypt(encrypted)
    # snippet.end
    a.eq(decrypted, 'My Secret Text', 'round trip')
    a.ok(encrypted != 'My Secret Text' and 'Secret' not in encrypted, 'the payload is encrypted')
    a.ok(encrypted.startswith(CBC_HEADER_B64), 'the payload is the 256-bit format')
    a.eq(pubnub.crypto.decrypt(pubnub.crypto.encrypt('{"a": 1}')), {'a': 1}, 'json text decodes to the object')
    a.raises(PubNubException, other.crypto.decrypt, encrypted, match='decryption error')


@step('encrypt_file', 'decrypt_file', role='open')
def test_encrypt_and_decrypt_file(clients):
    pubnub = reader(clients, 'file_crypto', AesCbcCryptoModule)
    plain = reader(clients, 'file_plain')
    channel = names.with_suffix('ch1')
    payload_to_encrypt = FIXTURE_BYTES

    # snippet.encrypt_file
    encrypted_payload = pubnub.crypto.encrypt_file(payload_to_encrypt)
    # snippet.end
    a.ok(isinstance(encrypted_payload, bytes), 'bytes come back')
    a.ok(encrypted_payload != FIXTURE_BYTES and encrypted_payload.startswith(b'PNED'), '256-bit encrypted bytes')
    payload_to_decrypt_in_bytes = encrypted_payload

    # snippet.decrypt_file
    decrypted_payload = pubnub.crypto.decrypt_file(payload_to_decrypt_in_bytes)
    # snippet.end
    a.eq(decrypted_payload, FIXTURE_BYTES, 'round trip')

    # The same module on the file API: what is stored is encrypted, what the same client downloads is plain
    target = tempfile.mkdtemp(prefix='docs-snippets-')
    path = os.path.join(target, 'sample.gif')
    with open(path, 'wb') as f:
        f.write(FIXTURE_BYTES)
    uploaded = None
    try:
        with open(path, 'rb') as sample_file:
            uploaded = pubnub.send_file().channel(channel).file_name('sample.gif') \
                .file_object(sample_file).sync().result
        downloaded = pubnub.download_file().channel(channel).file_id(uploaded.file_id).file_name('sample.gif').sync()
        a.eq(downloaded.result.data, FIXTURE_BYTES, 'the encrypting client downloads the original')
        stored = plain.download_file().channel(channel).file_id(uploaded.file_id).file_name('sample.gif').sync()
        a.ok(stored.result.data != FIXTURE_BYTES, 'the stored file is not the original')
        a.ok(stored.result.data.startswith(b'PNED'), 'the stored file is in the 256-bit format')
        a.eq(pubnub.crypto.decrypt_file(stored.result.data), FIXTURE_BYTES, 'the stored bytes decrypt to the original')
    finally:
        if uploaded is not None:
            try:
                pubnub.delete_file().channel(channel).file_id(uploaded.file_id).file_name('sample.gif').sync()
            except Exception as e:
                print('cleanup: could not delete the file (' + type(e).__name__ + ')')
        os.remove(path)
        os.rmdir(target)
