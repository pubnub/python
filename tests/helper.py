from pubnub import utils

from pubnub.pnconfiguration import PNConfiguration

pnconf = PNConfiguration()
pnconf.publish_key = "pub-c-739aa0fc-3ed5-472b-af26-aca1b333ec52"
pnconf.subscribe_key = "sub-c-33f55052-190b-11e6-bfbc-02ee2ddab7fe"

sdk_name = "Python-UnitTest"


def encode(data):
    return utils.encode(data)
