import pytest
import json
from pubnub.pubnub import PubNub
from pubnub.pnconfiguration import PNConfiguration
from pubnub.endpoints.users.create_user import CreateUser
from pubnub.exceptions import PubNubException


SUB_KEY = 'sub'
AUTH = 'auth'


def test_create_user():
    config = PNConfiguration()
    config.subscribe_key = SUB_KEY
    config.auth_key = AUTH
    user = PubNub(config).create_user()
    with pytest.raises(PubNubException):
        user.validate_params()
    user.include({'name': 'a'})
    with pytest.raises(PubNubException):
        user.validate_params()
    user.include({'id': 'x'})
    with pytest.raises(PubNubException):
        user.validate_params()
    user.include('id')
    with pytest.raises(PubNubException):
        user.validate_params()
    user.data({'id': 'user', 'name': 'username'})
    user.validate_params()

    assert user.build_path() == CreateUser.CREATE_USER_PATH % SUB_KEY
    assert AUTH == user.build_params_callback()({})['auth']
    assert json.loads(user.build_data()) == {'id': 'user', 'name': 'username'}
