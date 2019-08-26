import pytest

from pubnub.pubnub import PubNub
from pubnub.pnconfiguration import PNConfiguration
from pubnub.endpoints.users.delete_user import DeleteUser
from pubnub.exceptions import PubNubException


SUB_KEY = 'sub'
AUTH = 'auth'


def test_delete_user():
    config = PNConfiguration()
    config.subscribe_key = SUB_KEY
    config.auth_key = AUTH
    user = PubNub(config).delete_user()
    with pytest.raises(PubNubException):
        user.build_path()

    user.user_id('foo')
    assert user.build_path() == DeleteUser.DELETE_USER_PATH % (SUB_KEY, 'foo')
    assert AUTH == user.build_params_callback()({})['auth']
