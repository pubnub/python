import pytest
import json

from pubnub.pubnub import PubNub
from pubnub.pnconfiguration import PNConfiguration
from pubnub.endpoints.space.update_space import UpdateSpace
from pubnub.exceptions import PubNubException


SUB_KEY = 'sub'
AUTH = 'auth'


def test_update_space():
    config = PNConfiguration()
    config.subscribe_key = SUB_KEY
    config.auth_key = AUTH
    space = PubNub(config).update_space()
    space.include('custom')
    with pytest.raises(PubNubException):
        space.build_path()

    space.space_id('foo')
    assert space.build_path() == UpdateSpace.UPDATE_SPACE_PATH % (SUB_KEY, 'foo')
    with pytest.raises(PubNubException):
        space.validate_params()
    space.data({'name': 'bar'})
    assert json.loads(space.build_data()) == {'name': 'bar'}
    assert AUTH == space.build_params_callback()({})['auth']
