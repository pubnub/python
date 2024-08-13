from os import getenv
from pprint import pprint
from time import sleep

from pubnub.pnconfiguration import PNConfiguration
from pubnub.pubnub import PubNub


channel = 'example'

config = config = PNConfiguration()
config.publish_key = getenv('PUBLISH_KEY')
config.subscribe_key = getenv('SUBSCRIBE_KEY')
config.secret_key = getenv('SECRET_KEY')
config.cipher_key = getenv('CIPHER_KEY')
config.user_id = 'example'

pn = PubNub(config)

# let's build some message history

pn.publish().channel(channel).message('message zero zero').sync()
pn.publish().channel(channel).message('message zero one').sync()
pn.publish().channel(channel).message('message one zero').sync()
pn.publish().channel(channel).message('message one one').sync()

# give some time to store messages
sleep(3)

# fetching messages
messages = pn.fetch_messages().channels(channel).sync()
pprint([message.__dict__ for message in messages.result.channels[channel]])
