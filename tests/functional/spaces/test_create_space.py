import pytest
import json
from pubnub.pubnub import PubNub
from pubnub.pnconfiguration import PNConfiguration
from pubnub.endpoints.space.create_space import CreateSpace
from pubnub.exceptions import PubNubException


SUB_KEY = 'sub'
AUTH = 'auth'


def test_create_space():
    config = PNConfiguration()
    config.subscribe_key = SUB_KEY
    config.auth_key = AUTH
    space = PubNub(config).create_space()
    with pytest.raises(PubNubException):
        space.validate_params()
    space.include({'name': 'a'})
    with pytest.raises(PubNubException):
        space.validate_params()
    space.include({'id': 'x'})
    with pytest.raises(PubNubException):
        space.validate_params()
    space.include('custom')
    with pytest.raises(PubNubException):
        space.validate_params()
    space.data({'id': 'x', 'name': 'a'})
    space.validate_params()

    assert space.build_path() == CreateSpace.CREATE_SPACE_PATH % SUB_KEY
    assert AUTH == space.build_params_callback()({})['auth']
    assert json.loads(space.build_data()) == {'id': 'x', 'name': 'a'}
