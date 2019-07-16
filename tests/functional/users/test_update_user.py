import pytest

from pubnub.pubnub import PubNub
from pubnub.pnconfiguration import PNConfiguration
from pubnub.endpoints.users.update_user import UpdateUser
from pubnub.exceptions import PubNubException


SUB_KEY = 'sub'
AUTH = 'auth'


def test_fetch_user():
    config = PNConfiguration()
    config.subscribe_key = SUB_KEY
    config.auth_key = AUTH
    user = PubNub(config).update_user()
    user.include({'a': 3, 'b': 1})
    with pytest.raises(PubNubException):
        user.build_path()

    user.user_id('foo')
    assert user.build_path() == UpdateUser.UPDATE_USER_PATH % (SUB_KEY, 'foo')
    assert user.build_data() == '{"a": 3, "b": 1}'
    assert AUTH == user.build_params_callback()({})['auth']
