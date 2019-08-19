from pubnub.pubnub import PubNub
from pubnub.pnconfiguration import PNConfiguration
from pubnub.endpoints.space.get_spaces import GetSpaces


SUB_KEY = 'sub'
AUTH = 'auth'


def test_get_spaces():
    config = PNConfiguration()
    config.subscribe_key = SUB_KEY
    config.auth_key = AUTH
    spaces = PubNub(config).get_spaces()
    spaces.include(['a', 'b']).limit(30).end('XXX')

    assert spaces.build_path() == GetSpaces.GET_SPACES_PATH % SUB_KEY

    params = spaces.custom_params()
    assert params['include'] == ['a', 'b']
    assert params['limit'] == 30
    assert params['end'] == 'XXX'
    assert 'count' not in params

    spaces.start('YYY').count(True)
    params = spaces.custom_params()
    assert 'end' not in params
    assert params['start'] == 'YYY'
    assert params['count'] is True

    assert AUTH == spaces.build_params_callback()({})['auth']
