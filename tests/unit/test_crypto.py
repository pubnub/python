import pytest

from pubnub.pubnub import PubNub
from pubnub.pnconfiguration import PNConfiguration
from pubnub.crypto import PubNubCryptodome, PubNubCrypto, PubNubFileCrypto, AesCbcCryptoModule, \
    PubNubCryptoModule
from pubnub.crypto_core import PubNubAesCbcCryptor, PubNubLegacyCryptor, CryptorPayload
from pubnub.exceptions import PubNubException
from tests.helper import pnconf_file_copy, hardcoded_iv_config_copy, pnconf_env_copy


crypto = PubNubCryptodome(pnconf_file_copy())
crypto_hardcoded_iv = PubNubCryptodome(hardcoded_iv_config_copy())
todecode = 'QfD1NCBJCmt1aPPGU2cshw=='
plaintext_message = "hey-0"
KEY = 'testKey'


class TestPubNubCryptodome:
    def test_decode_aes(self):
        multiline_test_message = """

        dfjn
        t564

        sdfhp\n
        """

        assert crypto.decrypt(KEY, crypto.encrypt(KEY, multiline_test_message)) == multiline_test_message

    def test_decode_aes_default_hardcoded_iv(self):
        assert crypto_hardcoded_iv.decrypt(KEY, todecode) == plaintext_message

    def test_message_encryption_with_random_iv(self, pn_crypto=crypto):
        encrypted = pn_crypto.encrypt(KEY, plaintext_message, use_random_iv=True)
        decrypted = pn_crypto.decrypt(KEY, encrypted, use_random_iv=True)

        assert decrypted == plaintext_message

    def test_message_encryption_with_random_iv_taken_from_config(self):
        pn_config = pnconf_file_copy()
        pn_config.use_random_initialization_vector = True
        crypto_with_custom_settings = PubNubCryptodome(pn_config)

        self.test_message_encryption_with_random_iv(crypto_with_custom_settings)

    def test_append_random_iv(self):
        msg = crypto.append_random_iv(plaintext_message, use_random_iv=True, initialization_vector="1234567890123456")
        assert "1234567890123456" in msg

    def test_extract_random_iv(self):
        msg = crypto.append_random_iv(plaintext_message, use_random_iv=True, initialization_vector="1234567890123456")
        iv, extracted_message = crypto.extract_random_iv(msg, use_random_iv=True)
        assert extracted_message == plaintext_message

    def test_get_initialization_vector_is_random(self):
        iv = crypto.get_initialization_vector(use_random_iv=True)
        iv2 = crypto.get_initialization_vector(use_random_iv=True)

        assert len(iv) == 16
        assert iv != iv2


class TestPubNubFileCrypto:
    def test_encrypt_and_decrypt_file(self, file_for_upload, file_upload_test_data):
        config = pnconf_file_copy()
        config.cipher_key = 'myCipherKey'
        pubnub = PubNub(config)
        with open(file_for_upload.strpath, "rb") as fd:

            encrypted_file = pubnub.crypto.encrypt_file(fd.read())
            decrypted_file = pubnub.crypto.decrypt_file(encrypted_file)
        assert file_upload_test_data["FILE_CONTENT"] == decrypted_file.decode("utf-8")


class TestPubNubCryptoInterface:
    def test_get_default_crypto(self):
        config = pnconf_env_copy()
        assert isinstance(config.crypto, PubNubCrypto)
        assert isinstance(config.crypto, PubNubCryptodome)

    def test_get_custom_crypto(self):
        class CustomCryptor(PubNubCrypto):
            pass

        config = pnconf_env_copy()
        config.cryptor = CustomCryptor
        assert isinstance(config.crypto, PubNubCrypto)
        assert isinstance(config.crypto, CustomCryptor)


class TestPubNubCryptoModule:
    cipher_key = 'myCipherKey'

    def config(self, cipherKey, use_random_iv):
        conf = pnconf_env_copy()
        conf.cipher_key = cipherKey
        conf.use_random_initialization_vector = use_random_iv
        return conf

    def test_header_encoder(self):
        crypto = AesCbcCryptoModule(self.config('myCipherKey', True))
        header = crypto.encode_header()
        assert b'PNED\x01ACRH\x00' == header

        cryptor_data = b'\x21'
        header = crypto.encode_header(cryptor_data=cryptor_data)
        assert b'PNED\x01ACRH\x01' + cryptor_data == header

        cryptor_data = b'\x21' * 255
        header = crypto.encode_header(cryptor_data=cryptor_data)
        assert b'PNED\x01ACRH\xff\x00\xff' + cryptor_data == header

        try:
            header = crypto.encode_header(cryptor_data=(' ' * 65536).encode())
        except PubNubException as e:
            assert e.__str__() == 'None: Cryptor data is too long'

    def test_header_decoder(self):
        crypto = AesCbcCryptoModule(self.config('myCipherKey', True))
        header = crypto.decode_header(b'PNED\x01ACRH\x00')
        assert header['header_ver'] == 1
        assert header['cryptor_id'] == 'ACRH'
        assert header['cryptor_data'] == b''

        cryptor_data = b'\x21'
        header = crypto.decode_header(b'PNED\x01ACRH\x01' + cryptor_data)
        assert header['cryptor_data'] == cryptor_data

        cryptor_data = b'\x21' * 254
        header = crypto.decode_header(b'PNED\x01ACRH\xfe' + cryptor_data)
        assert header['cryptor_data'] == cryptor_data

        cryptor_data = b'\x21' * 255
        header = crypto.decode_header(b'PNED\x01ACRH\xff\x00\xff' + cryptor_data)
        assert header['cryptor_data'] == cryptor_data

    def test_aes_cbc_crypto_module(self):
        crypto = AesCbcCryptoModule(self.config('myCipherKey', True))
        test_message = 'Hello world encrypted with aesCbcModule'
        encrypted_message = crypto.encrypt(test_message)
        decrypted_message = crypto.decrypt(encrypted_message)
        assert decrypted_message == test_message

    def test_decrypt(self):
        crypto = AesCbcCryptoModule(self.config('myCipherKey', True))
        msg = 'UE5FRAFBQ1JIEKzlyoyC/jB1hrjCPY7zm+X2f7skPd0LBocV74cRYdrkRQ2BPKeA22gX/98pMqvcZtFB6TCGp3Zf1M8F730nlfk='
        decrypted = crypto.decrypt(msg)
        assert decrypted == 'Hello world encrypted with aesCbcModule'

        msg = 'T3J9iXI87PG9YY/lhuwmGRZsJgA5y8sFLtUpdFmNgrU1IAitgAkVok6YP7lacBiVhBJSJw39lXCHOLxl2d98Bg=='
        decrypted = crypto.decrypt(msg)
        assert decrypted == 'Hello world encrypted with legacyModuleRandomIv'

        crypto = AesCbcCryptoModule(self.config('myCipherKey', False))
        msg = 'OtYBNABjeAZ9X4A91FQLFBo4th8et/pIAsiafUSw2+L8iWqJlte8x/eCL5cyjzQa'
        decrypted = crypto.decrypt(msg)
        assert decrypted == 'Hello world encrypted with legacyModuleStaticIv'

    def test_encrypt_decrypt_aes(self):
        class MockCryptor(PubNubAesCbcCryptor):
            def get_initialization_vector(self) -> str:
                return b'\x00' * 16

        cryptor = MockCryptor('myCipherKey')
        crypto = PubNubCryptoModule({cryptor.CRYPTOR_ID: cryptor}, cryptor)

        encrypted = 'UE5FRAFBQ1JIEAAAAAAAAAAAAAAAAAAAAABbjKTFb0xLzByXntZkq2G7lHIGg5ZdQd73GwVG6o3ftw=='
        message = 'We are the knights who say NI!'

        assert crypto.encrypt(message) == encrypted

    def test_encrypt_module_decrypt_legacy_static_iv(self):
        cryptor = PubNubLegacyCryptor(self.cipher_key, False)
        crypto = PubNubCryptoModule({cryptor.CRYPTOR_ID: cryptor}, cryptor)
        original_message = 'We are the knights who say NI!'
        encrypted = crypto.encrypt(original_message)

        # decrypt with legacy crypto
        config = PNConfiguration()
        config.cipher_key = self.cipher_key
        config.use_random_initialization_vector = False
        crypto = PubNubCryptodome(config)
        decrypted = crypto.decrypt(self.cipher_key, encrypted)

        assert decrypted == original_message

    def test_encrypt_module_decrypt_legacy_random_iv(self):
        cryptor = PubNubLegacyCryptor(self.cipher_key, True)
        crypto = PubNubCryptoModule({cryptor.CRYPTOR_ID: cryptor}, cryptor)
        original_message = 'We are the knights who say NI!'
        encrypted = crypto.encrypt(original_message)

        # decrypt with legacy crypto
        config = PNConfiguration()
        config.cipher_key = self.cipher_key
        config.use_random_initialization_vector = True
        crypto = PubNubCryptodome(config)
        decrypted = crypto.decrypt(self.cipher_key, encrypted)

        assert decrypted == original_message

    def test_php_encrypted_crosscheck(self):
        crypto = AesCbcCryptoModule(self.config(self.cipher_key, False))
        phpmess = "KGc+SNJD7mIveY+KNIL/L9ZzAjC0dCJCju+HXRwSW2k="
        decrypted = crypto.decrypt(phpmess)
        assert decrypted == 'PHP can backwards Legacy static'

        crypto = AesCbcCryptoModule(self.config(self.cipher_key, True))
        phpmess = "PXjHv0L05kgj0mqIE9s7n4LDPrLtjnfamMoHyiMoL0R1uzSMsYp7dDfqEWrnoaqS"
        decrypted = crypto.decrypt(phpmess)
        assert decrypted == 'PHP can backwards Legacy random'

        crypto = AesCbcCryptoModule(self.config(self.cipher_key, True))
        phpmess = "UE5FRAFBQ1JIEHvl3cY3RYsHnbKm6VR51XG/Y7HodnkumKHxo+mrsxbIjZvFpVuILQ0oZysVwjNsDNMKiMfZteoJ8P1/" \
            "mvPmbuQKLErBzS2l7vEohCwbmAJODPR2yNhJGB8989reTZ7Y7Q=="
        decrypted = crypto.decrypt(phpmess)
        assert decrypted == 'PHP can into space with headers and aes cbc and other shiny stuff'


class TestDecryptionFailureRaises:
    """Decrypt failures must raise PubNubException, never silently return ciphertext."""

    cipher_key = 'myCipherKey'

    @pytest.mark.parametrize('use_random_iv', [True, False])
    def test_file_decrypt_wrong_key_raises(self, use_random_iv):
        config = pnconf_file_copy()
        config.cipher_key = self.cipher_key
        config.use_random_initialization_vector = use_random_iv
        crypto = PubNubFileCrypto(config)
        encrypted = crypto.encrypt(self.cipher_key, b'secret file content', use_random_iv=use_random_iv)

        with pytest.raises(PubNubException) as exc_info:
            crypto.decrypt('totallyWrongKey', encrypted, use_random_iv=use_random_iv)
        assert 'decryption error' in str(exc_info.value)
        assert exc_info.value is not encrypted

    def test_module_decrypt_file_corrupt_raises(self):
        # The AES-CBC cryptor validates PKCS#7 padding, so corrupting the ciphertext
        # is detected and surfaces as a generic decryption error.
        config = pnconf_file_copy()
        config.cipher_key = self.cipher_key
        module = AesCbcCryptoModule(config)
        encrypted = module.encrypt_file(b'secret file content')
        corrupted = bytearray(encrypted)
        corrupted[-1] ^= 0xFF

        with pytest.raises(PubNubException) as exc_info:
            module.decrypt_file(bytes(corrupted))
        assert 'decryption error' in str(exc_info.value)


class TestPaddingOracleHardening:
    """Distinct crypto failures must produce an identical
    generic error, leaking no PyCryptodome mode-specific message."""

    cipher_key = 'myCipherKey'
    _leak_substrings = ('padding', 'pkcs', 'boundary', 'block', 'incorrect')

    def _bad_padding_payload(self, cryptor):
        # Flip a byte in the first ciphertext block to corrupt the decrypted PKCS#7
        # padding while keeping the input block-aligned (so unpad, not decrypt, fails).
        payload = cryptor.encrypt(b'A' * 20)
        corrupted = bytearray(payload['data'])
        corrupted[15] ^= 0xFF

        return CryptorPayload(data=bytes(corrupted), cryptor_data=payload['cryptor_data'])

    def _wrong_length_payload(self, cryptor):
        payload = cryptor.encrypt(b'A' * 20)
        return CryptorPayload(data=payload['data'][:-3], cryptor_data=payload['cryptor_data'])

    def _assert_generic(self, message):
        assert 'decryption error' in message
        lowered = message.lower()

        for leak in self._leak_substrings:
            assert leak not in lowered, f"error message leaks crypto detail: {message!r}"

    @pytest.mark.parametrize('binary_mode', [True, False])
    def test_aes_cbc_failures_identical(self, binary_mode):
        cryptor = PubNubAesCbcCryptor(self.cipher_key)

        with pytest.raises(PubNubException) as bad_padding:
            cryptor.decrypt(self._bad_padding_payload(cryptor), binary_mode=binary_mode)
        with pytest.raises(PubNubException) as wrong_length:
            cryptor.decrypt(self._wrong_length_payload(cryptor), binary_mode=binary_mode)

        self._assert_generic(str(bad_padding.value))
        self._assert_generic(str(wrong_length.value))

        assert str(bad_padding.value) == str(wrong_length.value)

    def test_cryptodome_message_wrong_key(self):
        config = pnconf_file_copy()
        config.cipher_key = self.cipher_key
        config.use_random_initialization_vector = True
        crypto = PubNubCryptodome(config)
        encrypted = crypto.encrypt(self.cipher_key, 'a secret message', use_random_iv=True)

        with pytest.raises(PubNubException) as exc_info:
            crypto.decrypt('totallyWrongKey', encrypted, use_random_iv=True)
        self._assert_generic(str(exc_info.value))
