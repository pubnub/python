import hashlib
import json
import sys
import random

from .crypto_core import PubNubCrypto
from Cryptodome.Cipher import AES
from Cryptodome.Util.Padding import pad, unpad

Initial16bytes = '0123456789012345'

if sys.version_info > (3, 0):
    v = 3
else:
    v = 2

try:
    from base64 import decodebytes, encodebytes
except ImportError:
    from base64 import decodestring, encodestring

try:
    from hashlib import sha256
    digestmod = sha256
except ImportError:
    import Cryptodome.Hash.SHA256 as digestmod
    sha256 = digestmod.new


class PubNubCryptodome(PubNubCrypto):
    def __init__(self, pubnub_config):
        self.pubnub_configuration = pubnub_config

    def encrypt(self, key, msg, use_random_iv=False):
        secret = self.get_secret(key)
        initialization_vector = self.get_initialization_vector(use_random_iv)

        if v == 3:
            cipher = AES.new(bytes(secret[0:32], 'utf-8'), AES.MODE_CBC, bytes(initialization_vector, 'utf-8'))
            encrypted_message = cipher.encrypt(self.pad(msg.encode('utf-8')))
            msg_with_iv = self.append_random_iv(encrypted_message, use_random_iv, bytes(initialization_vector, "utf-8"))

            return encodebytes(msg_with_iv).decode('utf-8').replace("\n", "")

        else:
            cipher = AES.new(secret[0:32], AES.MODE_CBC, initialization_vector)
            encrypted_message = cipher.encrypt(self.pad(msg))
            msg_with_iv = self.append_random_iv(encrypted_message, use_random_iv, initialization_vector)
            return encodestring(msg_with_iv).replace("\n", "")

    def decrypt(self, key, msg, use_random_iv=False):
        secret = self.get_secret(key)

        if v == 3:
            decoded_message = decodebytes(msg.encode("utf-8"))
            initialization_vector, extracted_message = self.extract_random_iv(decoded_message, use_random_iv)
            cipher = AES.new(bytes(secret[0:32], "utf-8"), AES.MODE_CBC, initialization_vector)
            plain = self.depad((cipher.decrypt(extracted_message)).decode('utf-8'))

        else:
            decoded_message = decodestring(msg)
            initialization_vector, extracted_message = self.extract_random_iv(decoded_message, use_random_iv)
            cipher = AES.new(secret[0:32], AES.MODE_CBC, initialization_vector)
            plain = self.depad(cipher.decrypt(extracted_message))

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
            if v == 3:
                return bytes(Initial16bytes, "utf-8"), message
            else:
                return Initial16bytes, message

    def get_initialization_vector(self, use_random_iv):
        if self.pubnub_configuration.use_random_initialization_vector or use_random_iv:
            return "{0:016}".format(random.randint(0, 9999999999999999))
        else:
            return Initial16bytes

    def pad(self, msg, block_size=16):
        padding = block_size - (len(msg) % block_size)

        if v == 3:
            return msg + (chr(padding) * padding).encode('utf-8')
        else:
            return msg + chr(padding) * padding

    def depad(self, msg):
        return msg[0:-ord(msg[-1])]

    def get_secret(self, key):
        if v == 3:
            return hashlib.sha256(key.encode("utf-8")).hexdigest()
        else:
            return hashlib.sha256(key).hexdigest()


class PubNubFileCrypto(PubNubCryptodome):
    def encrypt(self, key, file):
        secret = self.get_secret(key)
        initialization_vector = self.get_initialization_vector(use_random_iv=True)

        if v == 3:
            cipher = AES.new(bytes(secret[0:32], "utf-8"), AES.MODE_CBC, bytes(initialization_vector, 'utf-8'))
            initialization_vector = bytes(initialization_vector, 'utf-8')
        else:
            cipher = AES.new(secret[0:32], AES.MODE_CBC, initialization_vector)

        return self.append_random_iv(
            cipher.encrypt(pad(file, 16)),
            use_random_iv=True,
            initialization_vector=initialization_vector
        )

    def decrypt(self, key, file):
        secret = self.get_secret(key)
        initialization_vector, extracted_file = self.extract_random_iv(file, use_random_iv=True)

        if v == 3:
            cipher = AES.new(bytes(secret[0:32], "utf-8"), AES.MODE_CBC, initialization_vector)
        else:
            cipher = AES.new(secret[0:32], AES.MODE_CBC, initialization_vector)

        return unpad(cipher.decrypt(extracted_file), 16)
