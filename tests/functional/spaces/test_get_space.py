import pytest

from pubnub.pubnub import PubNub
from pubnub.pnconfiguration import PNConfiguration
from pubnub.endpoints.space.get_space import GetSpace
from pubnub.exceptions import PubNubException


SUB_KEY = 'sub'
AUTH = 'auth'


def test_get_space():
    config = PNConfiguration()
    config.subscribe_key = SUB_KEY
    config.auth_key = AUTH
    space = PubNub(config).get_space()
    space.include(['a', 'b'])
    with pytest.raises(PubNubException):
        space.build_path()

    space.space_id('foo')
    assert space.build_path() == GetSpace.GET_SPACE_PATH % (SUB_KEY, 'foo')

    params = space.custom_params()
    assert params['include'] == ['a', 'b']
    assert AUTH == space.build_params_callback()({})['auth']
