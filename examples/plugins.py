from pubnub import pnconfiguration
from pubnub.models.consumer.plugin import HookPoint, Plugin
from pubnub.pubnub import PubNub
from pubnub.pnconfiguration import PNConfiguration
from pubnub_beta.entities import entity_plugins


config = PNConfiguration()
config.uuid = 'test'
config.publish_key = 'test'
config.subscribe_key = 'test'
pn = PubNub(config, plugins=entity_plugins)
pn.spaces_metadata()