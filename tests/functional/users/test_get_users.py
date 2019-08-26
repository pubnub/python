from pubnub.pubnub import PubNub
from pubnub.pnconfiguration import PNConfiguration
from pubnub.endpoints.users.get_users import GetUsers


SUB_KEY = 'sub'
AUTH = 'auth'


def test_get_users():
    config = PNConfiguration()
    config.subscribe_key = SUB_KEY
    config.auth_key = AUTH
    users = PubNub(config).get_users()
    users.include(['a', 'b']).limit(30).end('XXX')

    assert users.build_path() == GetUsers.GET_USERS_PATH % SUB_KEY

    params = users.custom_params()
    assert params['include'] == ['a', 'b']
    assert params['limit'] == 30
    assert params['end'] == 'XXX'
    assert 'count' not in params

    users.start('YYY').count(True)
    params = users.custom_params()
    assert 'end' not in params
    assert params['start'] == 'YYY'
    assert params['count'] is True

    assert AUTH == users.build_params_callback()({})['auth']
