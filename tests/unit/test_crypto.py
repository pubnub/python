from pubnub.pubnub import PubNub
from pubnub.pnconfiguration import PNConfiguration
from pubnub.crypto import PubNubCryptodome, PubNubCrypto, AesCbcCryptoModule, PubNubCryptoModule
from pubnub.crypto_core import PubNubAesCbcCryptor, PubNubLegacyCryptor
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
        pubnub = PubNub(pnconf_file_copy())
        with open(file_for_upload.strpath, "rb") as fd:
            encrypted_file = pubnub.encrypt(KEY, fd.read())

        decrypted_file = pubnub.decrypt(KEY, encrypted_file)
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

    def test_header_encoder(self):
        crypto = AesCbcCryptoModule('myCipherKey', True)
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
        crypto = AesCbcCryptoModule('myCipherKey', True)
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
        crypto = AesCbcCryptoModule('myCipherKey', True)
        test_message = 'Hello world encrypted with aesCbcModule'
        encrypted_message = crypto.encrypt(test_message)
        decrypted_message = crypto.decrypt(encrypted_message)
        assert decrypted_message == test_message

    def test_decrypt(self):
        crypto = AesCbcCryptoModule('myCipherKey', True)
        msg = 'UE5FRAFBQ1JIEKzlyoyC/jB1hrjCPY7zm+X2f7skPd0LBocV74cRYdrkRQ2BPKeA22gX/98pMqvcZtFB6TCGp3Zf1M8F730nlfk='
        decrypted = crypto.decrypt(msg)
        assert decrypted == 'Hello world encrypted with aesCbcModule'

        msg = 'T3J9iXI87PG9YY/lhuwmGRZsJgA5y8sFLtUpdFmNgrU1IAitgAkVok6YP7lacBiVhBJSJw39lXCHOLxl2d98Bg=='
        decrypted = crypto.decrypt(msg)
        assert decrypted == 'Hello world encrypted with legacyModuleRandomIv'

        crypto = AesCbcCryptoModule('myCipherKey', False)
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
        crypto = AesCbcCryptoModule(self.cipher_key, False)
        phpmess = "KGc+SNJD7mIveY+KNIL/L9ZzAjC0dCJCju+HXRwSW2k="
        decrypted = crypto.decrypt(phpmess)
        assert decrypted == 'PHP can backwards Legacy static'

        crypto = AesCbcCryptoModule(self.cipher_key, True)
        phpmess = "PXjHv0L05kgj0mqIE9s7n4LDPrLtjnfamMoHyiMoL0R1uzSMsYp7dDfqEWrnoaqS"
        decrypted = crypto.decrypt(phpmess)
        assert decrypted == 'PHP can backwards Legacy random'

        crypto = AesCbcCryptoModule(self.cipher_key, True)
        phpmess = "UE5FRAFBQ1JIEHvl3cY3RYsHnbKm6VR51XG/Y7HodnkumKHxo+mrsxbIjZvFpVuILQ0oZysVwjNsDNMKiMfZteoJ8P1/" \
            "mvPmbuQKLErBzS2l7vEohCwbmAJODPR2yNhJGB8989reTZ7Y7Q=="
        decrypted = crypto.decrypt(phpmess)
        assert decrypted == 'PHP can into space with headers and aes cbc and other shiny stuff'
