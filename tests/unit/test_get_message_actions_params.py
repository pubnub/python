import pytest

from pubnub.pubnub import PubNub
from tests.helper import pnconf_copy

pubnub = PubNub(pnconf_copy())


def test_start_and_end_are_both_sent():
    params = pubnub.get_message_actions().channel('ch').start('300').end('200').custom_params()

    assert params['start'] == '300'
    assert params['end'] == '200'


def test_start_and_end_are_both_sent_with_named_arguments():
    params = pubnub.get_message_actions(channel='ch', start='300', end='200').custom_params()

    assert params['start'] == '300'
    assert params['end'] == '200'


def test_end_only():
    params = pubnub.get_message_actions().channel('ch').end('200').custom_params()

    assert 'start' not in params
    assert params['end'] == '200'


def test_start_only():
    params = pubnub.get_message_actions().channel('ch').start('300').custom_params()

    assert params['start'] == '300'
    assert 'end' not in params


def test_no_bounds_and_default_limit():
    params = pubnub.get_message_actions().channel('ch').custom_params()

    assert params == {}


def test_limit_accepts_str():
    params = pubnub.get_message_actions().channel('ch').limit('50').custom_params()

    assert params['limit'] == '50'


def test_limit_accepts_int():
    params = pubnub.get_message_actions().channel('ch').limit(50).custom_params()

    assert params['limit'] == '50'


def test_limit_rejects_other_types():
    with pytest.raises(AssertionError):
        pubnub.get_message_actions().channel('ch').limit(5.5)

    with pytest.raises(AssertionError):
        pubnub.get_message_actions().channel('ch').limit(True)
