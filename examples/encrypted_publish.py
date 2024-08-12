from os import getenv
from pubnub.pubnub import PubNub
from pubnub.pnconfiguration import PNConfiguration
from pubnub.crypto import AesCbcCryptoModule

config = PNConfiguration()
config.publish_key = getenv('PUBLISH_KEY', 'demo')
config.subscribe_key = getenv('SUBSCRIBE_KEY', 'demo')
config.cipher_key = getenv('CIPHER_KEY', 'my_cipher_key')
config.uuid = 'example-python'
config.crypto_module = AesCbcCryptoModule(config)

pubnub = PubNub(config)

message = 'Plaintext_message'
if config.cipher_key and not config.crypto_module:
    message = f'cryptodome({type(config.crypto)})'
if config.crypto_module:
    message = f'crypto_module({type(config.crypto_module)})'

pubnub.publish().channel('example').message(message).sync()
print(f'published: {message}')
