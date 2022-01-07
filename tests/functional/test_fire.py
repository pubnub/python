from pubnub.pubnub import PubNub
from pubnub.endpoints.pubsub.fire import Fire
from tests.helper import url_encode, pnconf_copy
import json

pnconf = pnconf_copy()

SUB_KEY = pnconf.subscribe_key
PUB_KEY = pnconf.publish_key
CHAN = 'chan'
MSG = 'x'
MSG_ENCODED = url_encode(MSG)
META = ['m1', 'm2']
AUTH = 'auth'


def test_fire():
    pnconf.auth_key = AUTH
    fire = PubNub(pnconf).fire()

    fire.channel(CHAN).message(MSG)
    assert fire.build_path() == Fire.FIRE_GET_PATH % (PUB_KEY, SUB_KEY, CHAN, 0, MSG_ENCODED)
    fire.use_post(True)
    assert fire.build_path() == Fire.FIRE_POST_PATH % (PUB_KEY, SUB_KEY, CHAN, 0)

    params = fire.custom_params()
    assert params['store'] == '0'
    assert params['norep'] == '1'

    fire.meta(META)
    assert 'meta' in fire.build_params_callback()({})
    assert json.dumps(META) == fire.build_params_callback()({})['meta']
    assert 'auth' in fire.build_params_callback()({})
    assert AUTH == fire.build_params_callback()({})['auth']
