from pubnub.pubnub import PubNub
from pubnub.crypto import PubNubCryptodome
from tests.helper import pnconf_file_copy, hardcoded_iv_config_copy

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
