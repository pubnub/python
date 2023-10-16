from pubnub.pnconfiguration import PNConfiguration
from pubnub.pubnub import PubNub
from pubnub.crypto import AesCbcCryptoModule
from Cryptodome.Cipher import AES

my_cipher_key = 'myCipherKey'
my_message = 'myMessage'

# by default no configuration changes is needed
config = PNConfiguration()
config.uuid = 'myUUID'
config.cipher_key = my_cipher_key
pubnub = PubNub(config)

# message will be encrypted the same way it was encrypted previously
cbc_message = pubnub.crypto.encrypt(my_message)  # new way of using cryptographic module from pubnub
decrypted = config.crypto.decrypt(my_cipher_key, cbc_message)
assert decrypted == my_message

# also no configuration changes is needed if you previously updated the cipher_mode to GCM
config = PNConfiguration()
config.uuid = 'myUUID'
config.cipher_key = my_cipher_key
config.cipher_mode = AES.MODE_GCM
config.fallback_cipher_mode = AES.MODE_CBC
pubnub = PubNub(config)

# message will be encrypted the same way it was encrypted previously
gcm_message = pubnub.crypto.encrypt(my_message)  # new way of using cryptographic module from pubnub
decrypted = config.crypto.decrypt(my_cipher_key, gcm_message)
assert decrypted == my_message

# opt in to use crypto module with headers and improved entropy
config = PNConfiguration()
config.uuid = 'myUUID'
config.cipher_key = my_cipher_key
config.cipher_mode = AES.MODE_GCM
config.fallback_cipher_mode = AES.MODE_CBC
module = AesCbcCryptoModule(config)
config.crypto_module = module
pubnub = PubNub(config)
message = pubnub.crypto.encrypt(my_message)
# this encryption method is not compatible with previous crypto methods
try:
    decoded = config.crypto.decrypt(my_cipher_key, message)
except Exception:
    pass
# but can be decrypted with new crypto module
decrypted = pubnub.crypto.decrypt(message)
assert decrypted == my_message
