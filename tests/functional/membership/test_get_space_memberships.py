import pytest
from pubnub.pubnub import PubNub
from pubnub.pnconfiguration import PNConfiguration
from pubnub.endpoints.membership.get_space_memberships import GetSpaceMemberships
from pubnub.exceptions import PubNubException


SUB_KEY = 'sub'
AUTH = 'auth'


def test_get_space_memberships():
    config = PNConfiguration()
    config.subscribe_key = SUB_KEY
    config.auth_key = AUTH
    membership = PubNub(config).get_space_memberships()
    membership.include(['a', 'b']).limit(30).end('XXX')

    with pytest.raises(PubNubException):
        membership.validate_params()

    membership.user_id('foo')
    assert membership.build_path() == GetSpaceMemberships.GET_SPACE_MEMBERSHIPS_PATH % (SUB_KEY, 'foo')

    params = membership.custom_params()
    assert params['include'] == 'a,b'
    assert params['limit'] == 30
    assert params['end'] == 'XXX'
    assert 'count' not in params

    membership.start('YYY').count(True)
    params = membership.custom_params()
    assert 'end' not in params
    assert params['start'] == 'YYY'
    assert params['count'] is True

    assert AUTH == membership.build_params_callback()({})['auth']
