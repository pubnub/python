import hashlib
import json
import logging
import secrets

from base64 import decodebytes, encodebytes, b64decode, b64encode
from Cryptodome.Cipher import AES
from Cryptodome.Util.Padding import pad, unpad
from pubnub.crypto_core import PubNubCrypto, PubNubCryptor, PubNubLegacyCryptor, PubNubAesCbcCryptor, CryptoHeader, \
    CryptorPayload
from pubnub.exceptions import PubNubException
from typing import Union, Dict


Initial16bytes = '0123456789012345'


class PubNubCryptodome(PubNubCrypto):
    mode = AES.MODE_CBC
    fallback_mode = None

    def __init__(self, pubnub_config):
        super().__init__(pubnub_config)
        self.mode = pubnub_config.cipher_mode
        self.fallback_mode = pubnub_config.fallback_cipher_mode

    def encrypt(self, key, msg, use_random_iv=False):
        secret = self.get_secret(key)
        initialization_vector = self.get_initialization_vector(use_random_iv)

        cipher = AES.new(bytes(secret[0:32], 'utf-8'), self.mode, bytes(initialization_vector, 'utf-8'))
        encrypted_message = cipher.encrypt(self.pad(msg.encode('utf-8')))
        msg_with_iv = self.append_random_iv(encrypted_message, use_random_iv, bytes(initialization_vector, "utf-8"))

        return encodebytes(msg_with_iv).decode('utf-8').replace("\n", "")

    def decrypt(self, key, msg, use_random_iv=False):
        secret = self.get_secret(key)

        decoded_message = decodebytes(msg.encode("utf-8"))
        initialization_vector, extracted_message = self.extract_random_iv(decoded_message, use_random_iv)
        cipher = AES.new(bytes(secret[0:32], "utf-8"), self.mode, initialization_vector)
        try:
            plain = self.depad((cipher.decrypt(extracted_message)).decode('utf-8'))
        except UnicodeDecodeError as e:
            if not self.fallback_mode:
                raise e

            cipher = AES.new(bytes(secret[0:32], "utf-8"), self.fallback_mode, initialization_vector)
            plain = self.depad((cipher.decrypt(extracted_message)).decode('utf-8'))

        try:
            return json.loads(plain)
        except Exception:
            return plain

    def append_random_iv(self, message, use_random_iv, initialization_vector):
        if self.pubnub_configuration.use_random_initialization_vector or use_random_iv:
            return initialization_vector + message
        else:
            return message

    def extract_random_iv(self, message, use_random_iv):
        if self.pubnub_configuration.use_random_initialization_vector or use_random_iv:
            return message[0:16], message[16:]
        else:
            return bytes(Initial16bytes, "utf-8"), message

    def get_initialization_vector(self, use_random_iv):
        if self.pubnub_configuration.use_random_initialization_vector or use_random_iv:
            return secrets.token_urlsafe(16)[:16]
        else:
            return Initial16bytes

    def pad(self, msg, block_size=16):
        padding = block_size - (len(msg) % block_size)
        return msg + (chr(padding) * padding).encode('utf-8')

    def depad(self, msg):
        return msg[0:-ord(msg[-1])]

    def get_secret(self, key):
        return hashlib.sha256(key.encode("utf-8")).hexdigest()


class PubNubFileCrypto(PubNubCryptodome):
    def encrypt(self, key, file, use_random_iv=True):

        secret = self.get_secret(key)
        initialization_vector = self.get_initialization_vector(use_random_iv)
        cipher = AES.new(bytes(secret[0:32], "utf-8"), self.mode, bytes(initialization_vector, 'utf-8'))
        initialization_vector = bytes(initialization_vector, 'utf-8')

        return self.append_random_iv(
            cipher.encrypt(pad(file, 16)),
            use_random_iv=True,
            initialization_vector=initialization_vector
        )

    def decrypt(self, key, file, use_random_iv=True):
        secret = self.get_secret(key)
        initialization_vector, extracted_file = self.extract_random_iv(file, use_random_iv)
        try:
            cipher = AES.new(bytes(secret[0:32], "utf-8"), self.mode, initialization_vector)
            result = unpad(cipher.decrypt(extracted_file), 16)
        except ValueError:
            if not self.fallback_mode:  # No fallback mode so we return the original content
                return file
            cipher = AES.new(bytes(secret[0:32], "utf-8"), self.fallback_mode, initialization_vector)
            result = unpad(cipher.decrypt(extracted_file), 16)

        return result


class PubNubCryptoModule(PubNubCrypto):
    FALLBACK_CRYPTOR_ID: str = '0000'
    cryptor_map = {}
    default_cryptor_id: str

    def __init__(self, cryptor_map: Dict[str, PubNubCryptor], default_cryptor: PubNubCryptor):
        self.cryptor_map = cryptor_map
        self.default_cryptor_id = default_cryptor.CRYPTOR_ID

    def _validate_cryptor_id(self, cryptor_id: str) -> str:
        cryptor_id = cryptor_id or self.default_cryptor_id

        if len(cryptor_id) != 4:
            logging.error(f'Malformed cryptor id: {cryptor_id}')
            raise PubNubException('Malformed cryptor id')

        if cryptor_id not in self.cryptor_map.keys():
            logging.error(f'Unsupported cryptor: {cryptor_id}')
            raise PubNubException('unknown cryptor error')
        return cryptor_id

    def _get_cryptor(self, cryptor_id):
        if not cryptor_id or cryptor_id not in self.cryptor_map:
            raise PubNubException('unknown cryptor error')
        return self.cryptor_map[cryptor_id]

    # encrypt string
    def encrypt(self, message: str, cryptor_id: str = None) -> str:
        if not len(message):
            raise PubNubException('encryption error')
        cryptor_id = self._validate_cryptor_id(cryptor_id)
        data = message.encode('utf-8')
        crypto_payload = self.cryptor_map[cryptor_id].encrypt(data)
        header = self.encode_header(cryptor_id=cryptor_id, cryptor_data=crypto_payload['cryptor_data'])
        return b64encode(header + crypto_payload['data']).decode()

    def decrypt(self, message):
        data = b64decode(message)
        header = self.decode_header(data)
        if header:
            cryptor_id = header['cryptor_id']
            payload = CryptorPayload(data=data[header['length']:], cryptor_data=header['cryptor_data'])
        if not header:
            cryptor_id = self.FALLBACK_CRYPTOR_ID
            payload = CryptorPayload(data=data)

        if not len(payload['data']):
            raise PubNubException('decryption error')

        if cryptor_id not in self.cryptor_map.keys():
            raise PubNubException('unknown cryptor error')

        message = self._get_cryptor(cryptor_id).decrypt(payload)
        try:
            return json.loads(message)
        except Exception:
            return message

    def encrypt_file(self, file_data, cryptor_id: str = None):
        if not len(file_data):
            raise PubNubException('encryption error')
        cryptor_id = self._validate_cryptor_id(cryptor_id)
        crypto_payload = self.cryptor_map[cryptor_id].encrypt(file_data)
        header = self.encode_header(cryptor_id=cryptor_id, cryptor_data=crypto_payload['cryptor_data'])
        return header + crypto_payload['data']

    def decrypt_file(self, file_data):
        header = self.decode_header(file_data)
        if header:
            cryptor_id = header['cryptor_id']
            payload = CryptorPayload(data=file_data[header['length']:], cryptor_data=header['cryptor_data'])
        else:
            cryptor_id = self.FALLBACK_CRYPTOR_ID
            payload = CryptorPayload(data=file_data)

        if not len(payload['data']):
            raise PubNubException('decryption error')

        if cryptor_id not in self.cryptor_map.keys():
            raise PubNubException('unknown cryptor error')

        return self._get_cryptor(cryptor_id).decrypt(payload, binary_mode=True)

    def encode_header(self, cryptor_id: str = None, cryptor_data: any = None) -> str:
        if cryptor_id == self.FALLBACK_CRYPTOR_ID:
            return b''
        if cryptor_data and len(cryptor_data) > 65535:
            raise PubNubException('Cryptor data is too long')
        cryptor_id = self._validate_cryptor_id(cryptor_id)

        sentinel = b'PNED'
        version = CryptoHeader.header_ver.to_bytes(1, byteorder='big')
        crid = bytes(cryptor_id, 'utf-8')

        if cryptor_data:
            crd = cryptor_data
            cryptor_data_len = len(cryptor_data)
        else:
            crd = b''
            cryptor_data_len = 0

        if cryptor_data_len < 255:
            crlen = cryptor_data_len.to_bytes(1, byteorder='big')
        else:
            crlen = b'\xff' + cryptor_data_len.to_bytes(2, byteorder='big')
        return sentinel + version + crid + crlen + crd

    def decode_header(self, header: bytes) -> Union[None, CryptoHeader]:
        try:
            sentinel = header[:4]
            if sentinel != b'PNED':
                return False
        except ValueError:
            return False

        try:
            header_version = header[4]
            if header_version > CryptoHeader.header_ver:
                raise PubNubException('unknown cryptor error')

            cryptor_id = header[5:9].decode()
            crlen = header[9]
            if crlen < 255:
                cryptor_data = header[10: 10 + crlen]
                hlen = 10 + crlen
            else:
                crlen = int(header[10:12].hex(), 16)
                cryptor_data = header[12:12 + crlen]
                hlen = 12 + crlen

            return CryptoHeader(sentinel=sentinel, header_ver=header_version, cryptor_id=cryptor_id,
                                cryptor_data=cryptor_data, length=hlen)
        except IndexError:
            raise PubNubException('decryption error')


class LegacyCryptoModule(PubNubCryptoModule):
    def __init__(self, config) -> None:
        cryptor_map = {
            PubNubLegacyCryptor.CRYPTOR_ID: PubNubLegacyCryptor(config.cipher_key,
                                                                config.use_random_initialization_vector,
                                                                config.cipher_mode,
                                                                config.fallback_cipher_mode),
            PubNubAesCbcCryptor.CRYPTOR_ID: PubNubAesCbcCryptor(config.cipher_key),
        }
        super().__init__(cryptor_map, PubNubLegacyCryptor)


class AesCbcCryptoModule(PubNubCryptoModule):
    def __init__(self, config) -> None:
        cryptor_map = {
            PubNubLegacyCryptor.CRYPTOR_ID: PubNubLegacyCryptor(config.cipher_key,
                                                                config.use_random_initialization_vector,
                                                                config.cipher_mode,
                                                                config.fallback_cipher_mode),
            PubNubAesCbcCryptor.CRYPTOR_ID: PubNubAesCbcCryptor(config.cipher_key),
        }
        super().__init__(cryptor_map, PubNubAesCbcCryptor)
