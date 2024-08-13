
from os import getenv
from pubnub.pubnub import PubNub
from pubnub.pnconfiguration import PNConfiguration

config = PNConfiguration()
config.publish_key = getenv('PUBLISH_KEY', 'demo')
config.subscribe_key = getenv('SUBSCRIBE_KEY', 'demo')
config.cipher_key = getenv('CIPHER_KEY', 'my_cipher_key')
config.uuid = 'example'
config.cipher_key = "my_cipher_key"
pubnub = PubNub(config)

messages = pubnub.fetch_messages().channels('example').count(30).decrypt_messages().sync()
for msg in messages.result.channels['example']:
    print(msg.message, f' !! Error during decryption: {msg.error}' if msg.error else '')
