import pytest

from pubnub.pubnub import PubNub
from pubnub.pnconfiguration import PNConfiguration
from pubnub.endpoints.users.get_user import GetUser
from pubnub.exceptions import PubNubException


SUB_KEY = 'sub'
AUTH = 'auth'


def test_get_user():
    config = PNConfiguration()
    config.subscribe_key = SUB_KEY
    config.auth_key = AUTH
    user = PubNub(config).get_user()
    user.include(['a', 'b'])
    with pytest.raises(PubNubException):
        user.build_path()

    user.user_id('foo')
    assert user.build_path() == GetUser.GET_USER_PATH % (SUB_KEY, 'foo')

    params = user.custom_params()
    assert params['include'] == ['a', 'b']
    assert AUTH == user.build_params_callback()({})['auth']
