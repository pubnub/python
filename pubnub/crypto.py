import hashlib
import json
import sys

from .crypto_core import PubNubCrypto
from Cryptodome.Cipher import AES

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
    def encrypt(self, key, msg):
        secret = self.get_secret(key)

        if v == 3:
            cipher = AES.new(bytes(secret[0:32], 'utf-8'), AES.MODE_CBC, bytes(Initial16bytes, 'utf-8'))
            return encodebytes(cipher.encrypt(self.pad(msg.encode('utf-8')))).decode('utf-8').replace("\n", "")
        else:
            cipher = AES.new(secret[0:32], AES.MODE_CBC, Initial16bytes)
            return encodestring(cipher.encrypt(self.pad(msg))).replace("\n", "")

    def decrypt(self, key, msg):
        secret = self.get_secret(key)

        if v == 3:
            cipher = AES.new(bytes(secret[0:32], 'utf-8'), AES.MODE_CBC, bytes(Initial16bytes, 'utf-8'))
            plain = self.depad((cipher.decrypt(decodebytes(msg.encode('utf-8')))).decode('utf-8'))
        else:
            cipher = AES.new(secret[0:32], AES.MODE_CBC, Initial16bytes)
            plain = self.depad(cipher.decrypt(decodestring(msg)))

        try:
            return json.loads(plain)
        except Exception:
            return plain

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
