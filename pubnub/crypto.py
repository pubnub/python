import hashlib
import json
import random
from base64 import decodebytes, encodebytes

from .crypto_core import PubNubCrypto
from Cryptodome.Cipher import AES
from Cryptodome.Util.Padding import pad, unpad


Initial16bytes = '0123456789012345'


class PubNubCryptodome(PubNubCrypto):
    def __init__(self, pubnub_config):
        self.pubnub_configuration = pubnub_config

    def encrypt(self, key, msg, use_random_iv=False):
        secret = self.get_secret(key)
        initialization_vector = self.get_initialization_vector(use_random_iv)

        cipher = AES.new(bytes(secret[0:32], 'utf-8'), AES.MODE_CBC, bytes(initialization_vector, 'utf-8'))
        encrypted_message = cipher.encrypt(self.pad(msg.encode('utf-8')))
        msg_with_iv = self.append_random_iv(encrypted_message, use_random_iv, bytes(initialization_vector, "utf-8"))

        return encodebytes(msg_with_iv).decode('utf-8').replace("\n", "")

    def decrypt(self, key, msg, use_random_iv=False):
        secret = self.get_secret(key)

        decoded_message = decodebytes(msg.encode("utf-8"))
        initialization_vector, extracted_message = self.extract_random_iv(decoded_message, use_random_iv)
        cipher = AES.new(bytes(secret[0:32], "utf-8"), AES.MODE_CBC, initialization_vector)
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
            return "{0:016}".format(random.randint(0, 9999999999999999))
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
    def encrypt(self, key, file):
        secret = self.get_secret(key)
        initialization_vector = self.get_initialization_vector(use_random_iv=True)
        cipher = AES.new(bytes(secret[0:32], "utf-8"), AES.MODE_CBC, bytes(initialization_vector, 'utf-8'))
        initialization_vector = bytes(initialization_vector, 'utf-8')

        return self.append_random_iv(
            cipher.encrypt(pad(file, 16)),
            use_random_iv=True,
            initialization_vector=initialization_vector
        )

    def decrypt(self, key, file):
        secret = self.get_secret(key)
        initialization_vector, extracted_file = self.extract_random_iv(file, use_random_iv=True)
        cipher = AES.new(bytes(secret[0:32], "utf-8"), AES.MODE_CBC, initialization_vector)

        return unpad(cipher.decrypt(extracted_file), 16)
