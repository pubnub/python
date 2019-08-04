import pytest
import json

from pubnub.pubnub import PubNub
from pubnub.pnconfiguration import PNConfiguration
from pubnub.endpoints.users.update_user import UpdateUser
from pubnub.exceptions import PubNubException


SUB_KEY = 'sub'
AUTH = 'auth'


def test_update_user():
    config = PNConfiguration()
    config.subscribe_key = SUB_KEY
    config.auth_key = AUTH
    user = PubNub(config).update_user()
    with pytest.raises(PubNubException):
        user.build_path()

    user.user_id('foo')
    assert user.build_path() == UpdateUser.UPDATE_USER_PATH % (SUB_KEY, 'foo')
    with pytest.raises(PubNubException):
        user.validate_params()
    user.data({'name': 'username'})
    user.validate_params()
    assert json.loads(user.build_data()) == {'name': 'username'}
    assert AUTH == user.build_params_callback()({})['auth']
