"""Docs page: encryption (sync only, the asyncio docs have no encryption page).

Source: docs/sdks/python/api-reference/encryption.md. The client of each docs sample is built by the sample itself,
so the page snippets show the crypto module lines on a PNConfiguration that the step created.
"""
# ruff: noqa: E303 (the cipher_mode_experiment sample keeps the two blank lines of examples/crypto.py)
import os
import tempfile

from pubnub.crypto import AesCbcCryptoModule, PubNubAesCbcCryptor, PubNubCryptoModule
from pubnub.enums import PNStatusCategory
from pubnub.exceptions import PubNubException
from pubnub import pubnub as pubnub_module
from pubnub.pubnub import PubNub

from support import assertions as a, env
from support.clients import config as client_config
from support.listen import listen
from support.wait import eventually
from shared.encryption import CBC_HEADER_B64, FIXTURE_BYTES, only_message, reader


def test_crypto_module_aes_cbc(clients):
    """Snippet: crypto_module_aes_cbc."""
    channel = 'my_channel'
    payload = {'text': 'knights who say ni'}
    config = client_config('open', 'encrypting_publisher')

    # snippet.crypto_module_aes_cbc
    from Cryptodome.Cipher import AES
    from pubnub.crypto import AesCbcCryptoModule
    from pubnub.pubnub import PubNub

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

    envelope = pubnub.publish().channel(channel).message(payload).sync()

    a.timetoken(envelope.result.timetoken)
    a.eq(only_message(same_key), payload, 'a subscriber with the same key reads the message')
    unreadable = only_message(no_key)
    a.ok(isinstance(unreadable, str) and unreadable.startswith(CBC_HEADER_B64), 'without a key the 256-bit payload')
    a.ok('ni' not in unreadable, 'the plain text is not in the payload')
    a.ok(isinstance(only_message(wrong_key), str), 'a wrong key leaves the payload encrypted')
    a.ok(only_message(wrong_key) != payload, 'a wrong key does not read the message')
    a.ok(wrong_key.messages[0].error is not None, 'the wrong key is reported as an error on the message')
    a.contains(wrong_key.categories, PNStatusCategory.PNDecryptionErrorCategory, 'decryption error status')


def test_crypto_module_legacy(clients):
    """Snippet: crypto_module_legacy."""
    channel = 'my_channel'
    payload = {'text': 'legacy knights'}
    config = client_config('open', 'legacy_publisher')

    # snippet.crypto_module_legacy
    from Cryptodome.Cipher import AES
    from pubnub.crypto import LegacyCryptoModule
    from pubnub.pubnub import PubNub

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

    pubnub.publish().channel(channel).message(payload).sync()

    a.eq(only_message(legacy_reader), payload, 'the legacy module reads its own payload')
    a.eq(only_message(cbc_reader), payload, 'the 256-bit module reads the legacy payload')
    unreadable = only_message(no_key)
    a.ok(isinstance(unreadable, str), 'without a key the payload is a string')
    a.ok(not unreadable.startswith(CBC_HEADER_B64), 'the legacy payload has no 256-bit header')
    a.ok(unreadable != payload and 'legacy' not in unreadable, 'the plain text is not in the payload')

    # The other direction: a message from a 256-bit client is readable by the legacy module
    cbc_config = client_config('open', 'cbc_publisher')
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


def _other_key_client(clients):
    """A client whose crypto module uses another cipher key. A helper, because the sample imports the crypto classes
    itself, which makes their names local to the whole test function."""
    other = PubNub(client_config('open', 'other_key'))
    clients._made.append(other)
    other.crypto = PubNubCryptoModule({
        PubNubAesCbcCryptor.CRYPTOR_ID: PubNubAesCbcCryptor('anotherCipherKey')
    }, PubNubAesCbcCryptor)
    return other


def test_crypto_module_partial(clients):
    """Snippet: crypto_module_partial."""
    config = client_config('open', 'partial_crypto')
    pubnub = PubNub(config)  # pubnub instance without encryption
    clients._made.append(pubnub)
    other = _other_key_client(clients)
    a.eq(pubnub.crypto, None, 'no crypto module before the sample')

    # snippet.crypto_module_partial
    from pubnub.crypto import PubNubCryptoModule
    from pubnub.crypto_core import PubNubAesCbcCryptor

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


def test_encrypt_file(clients):
    """Snippets: encrypt_file, decrypt_file."""
    pubnub = reader(clients, 'file_crypto', AesCbcCryptoModule)
    plain = reader(clients, 'file_plain')
    channel = 'ch1'
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
    target = tempfile.mkdtemp(prefix='pubnub-live-')
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


def test_cipher_mode_experiment(clients, monkeypatch, capsys):
    """Snippet: cipher_mode_experiment. The whole examples/crypto.py sample, run as a script on the open keyset."""
    keys = env.require('open')
    monkeypatch.setenv('PN_KEY_PUBLISH', keys['PUBLISH_KEY'])
    monkeypatch.setenv('PN_KEY_SUBSCRIBE', keys['SUBSCRIBE_KEY'])
    monkeypatch.delenv('PN_KEY_SECRET', raising=False)
    monkeypatch.delenv('PN_KEY_CIPHER', raising=False)
    # The sample imports PubNub itself, which makes the name local to this whole function: patch through the module.
    original_init = pubnub_module.PubNub.__init__

    def tracked_init(self, *args, **kwargs):
        """The sample builds its own clients, so stop them after the test like every other client."""
        original_init(self, *args, **kwargs)
        self.config.daemon = True
        clients.track(self)

    monkeypatch.setattr(pubnub_module.PubNub, '__init__', tracked_init)

    # snippet.cipher_mode_experiment
    from Cryptodome.Cipher import AES
    from os import getenv
    from pubnub.pnconfiguration import PNConfiguration
    from pubnub.pubnub import PubNub
    from pubnub.crypto import PubNubCryptoModule
    from pubnub.crypto_core import PubNubAesCbcCryptor
    from pubnub.exceptions import PubNubException
    from time import sleep

    channel = 'cipher_algorithm_experiment'

    def PNFactory(cipher_mode=AES.MODE_GCM, fallback_cipher_mode=AES.MODE_CBC) -> PubNub:
        config = PNConfiguration()
        config.publish_key = getenv('PN_KEY_PUBLISH')
        config.subscribe_key = getenv('PN_KEY_SUBSCRIBE')
        config.secret_key = getenv('PN_KEY_SECRET')
        config.cipher_key = getenv('PN_KEY_CIPHER', 'my_secret_cipher_key')
        config.user_id = 'experiment'
        config.cipher_mode = cipher_mode
        config.fallback_cipher_mode = fallback_cipher_mode

        return PubNub(config)

    # let's build history with legacy AES.CBC
    pn = PNFactory(cipher_mode=AES.MODE_CBC, fallback_cipher_mode=None)
    pn.publish().channel(channel).message('message encrypted with CBC').sync()
    pn.publish().channel(channel).message('message encrypted with CBC').sync()

    # now with upgraded config
    pn = PNFactory(cipher_mode=AES.MODE_GCM, fallback_cipher_mode=AES.MODE_CBC)
    pn.publish().channel(channel).message('message encrypted with GCM').sync()
    pn.publish().channel(channel).message('message encrypted with GCM').sync()

    # give some time to store messages
    sleep(3)

    # after upgrade decoding with GCM and fallback CBC
    pn = PNFactory(cipher_mode=AES.MODE_GCM, fallback_cipher_mode=AES.MODE_CBC)
    messages = pn.history().channel(channel).sync()
    print([message.entry for message in messages.result.messages])

    # before upgrade decoding with CBC and without fallback
    pn = PNFactory(cipher_mode=AES.MODE_CBC, fallback_cipher_mode=None)
    try:
        messages = pn.history().channel(channel).sync()
        print([message.entry for message in messages.result.messages])
    except PubNubException:
        print('Unable to decode - Exception has been thrown')

    #  partial encrypt/decrypt example
    config = PNConfiguration()
    config.publish_key = getenv('PN_KEY_PUBLISH')
    config.subscribe_key = getenv('PN_KEY_SUBSCRIBE')
    config.user_id = 'experiment'
    pubnub = PubNub(config)  # pubnub instance without encryption
    pubnub.crypto = PubNubCryptoModule({
        PubNubAesCbcCryptor.CRYPTOR_ID: PubNubAesCbcCryptor('myCipherKey')
    }, PubNubAesCbcCryptor)

    text_to_encrypt = 'My Secret Text'
    encrypted = pubnub.crypto.encrypt(text_to_encrypt)  # encrypted wih AES cryptor and `myCipherKey` cipher key
    decrypted = pubnub.crypto.decrypt(encrypted)
    print(f'Source: {text_to_encrypt}\nEncrypted: {encrypted}\nDecrypted: {decrypted}')
    # snippet.end

    printed = capsys.readouterr().out.strip().split('\n')
    a.eq(printed[0], str(['message encrypted with CBC'] * 2 + ['message encrypted with GCM'] * 2),
         'GCM with a CBC fallback decodes the whole history')
    a.eq(printed[1], 'Unable to decode - Exception has been thrown', 'CBC without a fallback cannot read GCM messages')
    a.ok(printed[-1].endswith('Decrypted: My Secret Text'), 'the partial encryption round trip')
