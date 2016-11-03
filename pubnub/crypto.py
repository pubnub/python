import hashlib
import json

from Cryptodome.Cipher import AES

try:
    from base64 import decodebytes, encodebytes
except ImportError:
    from base64 import decodestring, encodestring

import sys

try:
    from hashlib import sha256
    digestmod = sha256
except ImportError:
    import Cryptodome.Hash.SHA256 as digestmod
    sha256 = digestmod.new

if sys.version_info > (3, 0):
    v = 3
else:
    v = 2

Initial16bytes = '0123456789012345'


def pad(msg, block_size=16):
    padding = block_size - (len(msg) % block_size)

    if v == 3:
        return msg + (chr(padding) * padding).encode('utf-8')
    else:
        return msg + chr(padding) * padding


def depad(msg):
    return msg[0:-ord(msg[-1])]


def get_secret(key):
    if v == 3:
        return hashlib.sha256(key.encode("utf-8")).hexdigest()
    else:
        return hashlib.sha256(key).hexdigest()


def encrypt(key, msg):
    secret = get_secret(key)

    if v == 3:
        cipher = AES.new(bytes(secret[0:32], 'utf-8'), AES.MODE_CBC, bytes(Initial16bytes, 'utf-8'))
        return encodebytes(cipher.encrypt(pad(msg.encode('utf-8')))).decode('utf-8').replace("\n", "")
    else:
        cipher = AES.new(secret[0:32], AES.MODE_CBC, Initial16bytes)
        return encodestring(cipher.encrypt(pad(msg))).replace("\n", "")


def decrypt(key, msg):
    secret = get_secret(key)

    if v == 3:
        cipher = AES.new(bytes(secret[0:32], 'utf-8'), AES.MODE_CBC, bytes(Initial16bytes, 'utf-8'))
        plain = depad((cipher.decrypt(decodebytes(msg.encode('utf-8')))).decode('utf-8'))
    else:
        cipher = AES.new(secret[0:32], AES.MODE_CBC, Initial16bytes)
        plain = depad(cipher.decrypt(decodestring(msg)))

    try:
        return json.loads(plain)
    except Exception:
        return plain
