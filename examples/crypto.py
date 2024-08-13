from Cryptodome.Cipher import AES
from os import getenv
from pubnub.pnconfiguration import PNConfiguration
from pubnub.pubnub import PubNub
from pubnub.crypto import PubNubCryptoModule
from pubnub.crypto_core import PubNubAesCbcCryptor
from time import sleep

channel = 'cipher_algorithm_experiment'


def PNFactory(cipher_mode=AES.MODE_GCM, fallback_cipher_mode=AES.MODE_CBC) -> PubNub:
    config = PNConfiguration()
    config.publish_key = getenv('PN_KEY_PUBLISH')
    config.subscribe_key = getenv('PN_KEY_SUBSCRIBE')
    config.secret_key = getenv('PN_KEY_SECRET')
    config.cipher_key = getenv('PN_KEY_CIPHER', 'my_secret_cipher_key')
    config.user_id = 'experiment'
    config.cipher_mode = cipher_mode
    config.fallback_cipher_mode = fallback_cipher_mode

    return PubNub(config)


# let's build history with legacy AES.CBC
pn = PNFactory(cipher_mode=AES.MODE_CBC, fallback_cipher_mode=None)
pn.publish().channel(channel).message('message encrypted with CBC').sync()
pn.publish().channel(channel).message('message encrypted with CBC').sync()

# now with upgraded config
pn = PNFactory(cipher_mode=AES.MODE_GCM, fallback_cipher_mode=AES.MODE_CBC)
pn.publish().channel(channel).message('message encrypted with GCM').sync()
pn.publish().channel(channel).message('message encrypted with GCM').sync()

# give some time to store messages
sleep(3)

# after upgrade decoding with GCM and fallback CBC
pn = PNFactory(cipher_mode=AES.MODE_GCM, fallback_cipher_mode=AES.MODE_CBC)
messages = pn.history().channel(channel).sync()
print([message.entry for message in messages.result.messages])

# before upgrade decoding with CBC and without fallback
pn = PNFactory(cipher_mode=AES.MODE_CBC, fallback_cipher_mode=None)
try:
    messages = pn.history().channel(channel).sync()
    print([message.entry for message in messages.result.messages])
except UnicodeDecodeError:
    print('Unable to decode - Exception has been thrown')

#  partial encrypt/decrypt example
config = PNConfiguration()
config.publish_key = getenv('PN_KEY_PUBLISH')
config.subscribe_key = getenv('PN_KEY_SUBSCRIBE')
config.user_id = 'experiment'
pubnub = PubNub(config)  # pubnub instance without encryption
pubnub.crypto = PubNubCryptoModule({
    PubNubAesCbcCryptor.CRYPTOR_ID: PubNubAesCbcCryptor('myCipherKey')
}, PubNubAesCbcCryptor)

text_to_encrypt = 'My Secret Text'
encrypted = pubnub.crypto.encrypt(text_to_encrypt)  # encrypted wih AES cryptor and `myCipherKey` cipher key
decrypted = pubnub.crypto.decrypt(encrypted)
print(f'Source: {text_to_encrypt}\nEncrypted: {encrypted}\nDecrypted: {decrypted}')
