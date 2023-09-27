import hashlib
import json
import random

from abc import abstractmethod
from Cryptodome.Cipher import AES


class PubNubCrypto:
    def __init__(self, pubnub_config):
        self.pubnub_configuration = pubnub_config

    @abstractmethod
    def encrypt(self, key, msg):
        pass

    @abstractmethod
    def decrypt(self, key, msg):
        pass


class CryptoHeader(dict):
    sentinel: str
    cryptor_ver: int
    cryptor_id: str
    cryptor_data: any
    length: any


class CryptorPayload(dict):
    data: bytes
    cryptor_data: bytes


class PubNubCryptor:
    CRYPTOR_ID: str
    CRYPTOR_VERSION: int = 1

    @abstractmethod
    def encrypt(self, data: bytes) -> CryptorPayload:
        pass

    @abstractmethod
    def decrypt(self, payload: CryptorPayload, binary_mode: bool = False) -> bytes:
        pass


class PubNubLegacyCryptor(PubNubCryptor):
    CRYPTOR_ID = '0000'
    Initial16bytes = b'0123456789012345'

    def __init__(self, cipher_key, use_random_iv=False, cipher_mode=AES.MODE_CBC, fallback_cipher_mode=None):
        self.cipher_key = cipher_key
        self.use_random_iv = use_random_iv
        self.mode = cipher_mode
        self.fallback_mode = fallback_cipher_mode

    def encrypt(self, msg, *, key=None, use_random_iv=None):
        key = key or self.cipher_key
        use_random_iv = use_random_iv or self.use_random_iv

        secret = self.get_secret(key)
        initialization_vector = self.get_initialization_vector(use_random_iv)

        cipher = AES.new(bytes(secret[0:32], 'utf-8'), self.mode, initialization_vector)
        encrypted_message = cipher.encrypt(self.pad(msg))
        msg_with_iv = self.append_random_iv(encrypted_message, use_random_iv, initialization_vector)
        return CryptorPayload(data=msg_with_iv, cryptor_data=initialization_vector)

    def decrypt(self, payload: CryptorPayload, key=None, use_random_iv=False, binary_mode: bool = False):
        key = key or self.cipher_key
        use_random_iv = use_random_iv or self.use_random_iv
        secret = self.get_secret(key)
        msg = payload['data']
        initialization_vector, extracted_message = self.extract_random_iv(msg, use_random_iv)
        cipher = AES.new(bytes(secret[0:32], "utf-8"), self.mode, initialization_vector)
        if binary_mode:
            return self.depad(cipher.decrypt(extracted_message), binary_mode)
        try:
            plain = self.depad((cipher.decrypt(extracted_message)).decode('utf-8'), binary_mode)
        except UnicodeDecodeError as e:
            if not self.fallback_mode:
                raise e

            cipher = AES.new(bytes(secret[0:32], "utf-8"), self.fallback_mode, initialization_vector)
            plain = self.depad((cipher.decrypt(extracted_message)).decode('utf-8'), binary_mode)

        try:
            return json.loads(plain)
        except Exception:
            return plain

    def append_random_iv(self, message, use_random_iv, initialization_vector):
        if self.use_random_iv or use_random_iv:
            return initialization_vector + message
        else:
            return message

    def extract_random_iv(self, message, use_random_iv):
        if use_random_iv:
            return message[0:16], message[16:]
        else:
            return self.Initial16bytes, message

    def get_initialization_vector(self, use_random_iv) -> bytes:
        if self.use_random_iv or use_random_iv:
            return bytes("{0:016}".format(random.randint(0, 9999999999999999)), 'utf-8')
        else:
            return self.Initial16bytes

    def pad(self, msg, block_size=16):
        padding = block_size - (len(msg) % block_size)
        return msg + (chr(padding) * padding).encode('utf-8')

    def depad(self, msg, binary_mode: bool = False):
        if binary_mode:
            return msg[0:-msg[-1]]
        else:
            return msg[0:-ord(msg[-1])]

    def get_secret(self, key):
        return hashlib.sha256(key.encode("utf-8")).hexdigest()


class PubNubAesCbcCryptor(PubNubCryptor):
    CRYPTOR_ID = 'ACRH'
    CRYPTOR_VERSION: int = 1
    mode = AES.MODE_CBC

    def __init__(self, cipher_key):
        self.cipher_key = cipher_key

    def get_initialization_vector(self) -> bytes:
        return random.randbytes(16)

    def get_secret(self, key) -> str:
        return hashlib.sha256(key.encode("utf-8")).digest()

    def pad(self, msg: bytes, block_size=AES.block_size) -> bytes:
        padding = block_size - (len(msg) % block_size)
        return msg + bytes(chr(padding) * padding, 'utf-8')

    def depad(self, msg: bytes) -> bytes:
        return msg[:-msg[-1]]

    def encrypt(self, data: bytes, key=None) -> CryptorPayload:
        key = key or self.cipher_key
        secret = self.get_secret(key)
        iv = self.get_initialization_vector()
        cipher = AES.new(secret, mode=self.mode, iv=iv)
        encrypted = cipher.encrypt(self.pad(data))
        return CryptorPayload(data=encrypted, cryptor_data=iv)

    def decrypt(self, payload: CryptorPayload, key=None, binary_mode: bool = False):
        key = key or self.cipher_key
        secret = self.get_secret(key)
        iv = payload['cryptor_data']
        cipher = AES.new(secret, mode=self.mode, iv=iv)
        if binary_mode:
            return self.depad(cipher.decrypt(payload['data']))
        else:
            return self.depad(cipher.decrypt(payload['data'])).decode()
