import pytest

from pubnub.pubnub import PubNub
from pubnub.pnconfiguration import PNConfiguration
from pubnub.endpoints.space.delete_space import DeleteSpace
from pubnub.exceptions import PubNubException


SUB_KEY = 'sub'
AUTH = 'auth'


def test_delete_space():
    config = PNConfiguration()
    config.subscribe_key = SUB_KEY
    config.auth_key = AUTH
    space = PubNub(config).delete_space()
    with pytest.raises(PubNubException):
        space.build_path()

    space.space_id('foo')
    assert space.build_path() == DeleteSpace.DELETE_DELETE_PATH % (SUB_KEY, 'foo')
    assert AUTH == space.build_params_callback()({})['auth']
