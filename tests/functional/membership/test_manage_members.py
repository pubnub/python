import pytest
from pubnub.pubnub import PubNub
from pubnub.pnconfiguration import PNConfiguration
from pubnub.endpoints.membership.manage_members import ManageMembers
from pubnub.exceptions import PubNubException


SUB_KEY = 'sub'
AUTH = 'auth'


def test_manage_members():
    config = PNConfiguration()
    config.subscribe_key = SUB_KEY
    config.auth_key = AUTH
    membership = PubNub(config).manage_members()
    membership.include(['custom']).limit(30).end('XXX')

    with pytest.raises(PubNubException):
        membership.validate_params()

    membership.space_id('foo')
    assert membership.build_path() == ManageMembers.MANAGE_MEMBERS_PATH % (SUB_KEY, 'foo')

    params = membership.custom_params()
    assert params['include'] == 'custom'
    assert params['limit'] == 30
    assert params['end'] == 'XXX'
    assert 'count' not in params

    membership.start('YYY').count(True)
    params = membership.custom_params()
    assert 'end' not in params
    assert params['start'] == 'YYY'
    assert params['count'] is True

    assert AUTH == membership.build_params_callback()({})['auth']
    membership.data({'add': [{'id': 'user'}]})
    assert membership.build_data() == '{"add": [{"id": "user"}]}'
