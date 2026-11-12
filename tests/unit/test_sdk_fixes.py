import base64
from types import SimpleNamespace
from unittest.mock import Mock

import cbor2
import pytest

from pubnub.event_engine.models import states
from pubnub.event_engine.statemachine import StateMachine
from pubnub.exceptions import PubNubException
from pubnub.models.consumer.history import PNFetchMessageItem, PNFetchMessagesResult
from pubnub.models.consumer.objects_v2.common import MemberIncludes, MembershipIncludes
from pubnub.pubnub import PubNub
from pubnub.pubnub_asyncio import EventEngineSubscriptionManager
from tests.helper import pnconf_copy, pnconf_pam_copy


# PubNubCore.reconnect() and disconnect()


def test_reconnect_delegates_to_subscription_manager():
    pubnub = PubNub(pnconf_copy())
    pubnub._subscription_manager = Mock(spec=['reconnect', 'disconnect'])

    pubnub.reconnect()

    pubnub._subscription_manager.reconnect.assert_called_once_with()


def test_disconnect_delegates_to_subscription_manager():
    pubnub = PubNub(pnconf_copy())
    pubnub._subscription_manager = Mock(spec=['reconnect', 'disconnect'])

    pubnub.disconnect()

    pubnub._subscription_manager.disconnect.assert_called_once_with()


def test_disconnect_without_manager_support_raises_pubnub_exception():
    pubnub = PubNub(pnconf_copy())
    pubnub._subscription_manager = Mock(spec=['reconnect'])

    with pytest.raises(PubNubException):
        pubnub.disconnect()


def test_reconnect_without_subscription_manager_raises_clear_error():
    config = pnconf_copy()
    config.enable_subscribe = False
    pubnub = PubNub(config)

    with pytest.raises(Exception, match="Subscription manager is not enabled"):
        pubnub.reconnect()


# Event engine context before the first subscribe


def test_state_machine_initial_context_has_empty_channels_and_groups():
    machine = StateMachine(states.UnsubscribedState, name="subscribe")

    assert machine.get_context().channels == []
    assert machine.get_context().groups == []


def test_contexts_do_not_share_channel_lists():
    first = states.PNContext()
    second = states.PNContext()

    first.channels.append('ch1')

    assert second.channels == []


def make_event_engine_manager():
    config = pnconf_copy()
    config.enable_presence_heartbeat = False
    pubnub = SimpleNamespace(config=config)
    return EventEngineSubscriptionManager(pubnub)


def test_event_engine_manager_before_first_subscribe():
    manager = make_event_engine_manager()
    try:
        assert manager.get_subscribed_channels() == []
        assert manager.get_subscribed_channel_groups() == []

        manager.unsubscribe_all()

        assert manager.event_engine.get_state_name() == 'UnsubscribedState'
        assert manager.get_subscribed_channels() == []
    finally:
        manager.loop.close()


def test_disconnect_with_event_engine_manager_raises_pubnub_exception():
    manager = make_event_engine_manager()
    try:
        pubnub = PubNub(pnconf_copy())
        pubnub._subscription_manager = manager

        with pytest.raises(PubNubException):
            pubnub.disconnect()
    finally:
        manager.loop.close()


# Objects If-Match header and total count


def test_if_match_header_does_not_leak_to_later_requests():
    pubnub = PubNub(pnconf_copy())

    with_etag = pubnub.set_channel_metadata().channel('ch1').if_matches_etag('etag-1')
    later = pubnub.set_channel_metadata().channel('ch1')
    other_endpoint = pubnub.get_all_channel_metadata()

    assert with_etag._custom_headers['If-Match'] == 'etag-1'
    assert with_etag.request_headers()['If-Match'] == 'etag-1'
    assert 'If-Match' not in later.request_headers()
    assert 'If-Match' not in other_endpoint.request_headers()


def test_if_match_header_is_per_instance():
    pubnub = PubNub(pnconf_copy())

    first = pubnub.set_uuid_metadata().if_matches_etag('etag-1')
    second = pubnub.set_uuid_metadata().if_matches_etag('etag-2')

    assert first._custom_headers['If-Match'] == 'etag-1'
    assert second._custom_headers['If-Match'] == 'etag-2'


def test_membership_includes_total_count_requests_count():
    pubnub = PubNub(pnconf_copy())

    params = pubnub.get_memberships(uuid='user-1', include=MembershipIncludes(total_count=True)).custom_params()

    assert params['count'] is True


def test_member_includes_total_count_requests_count():
    pubnub = PubNub(pnconf_copy())

    params = pubnub.get_channel_members(channel='ch1', include=MemberIncludes(total_count=True)).custom_params()

    assert params['count'] is True


def test_includes_without_total_count_do_not_request_count():
    pubnub = PubNub(pnconf_copy())

    params = pubnub.get_memberships(uuid='user-1', include=MembershipIncludes(custom=True)).custom_params()

    assert 'count' not in params


def test_deprecated_include_total_count_still_requests_count():
    pubnub = PubNub(pnconf_copy())

    params = pubnub.get_memberships(uuid='user-1', include_total_count=True).custom_params()

    assert params['count'] is True


# parse_token with malformed input


def encode_token(payload):
    return base64.b64encode(cbor2.dumps(payload)).decode('utf-8')


@pytest.mark.parametrize('token', [
    None,
    '',
    123,
    'abc',
    'not a token!!',
    'qEF2AkF0GmFLd-NDdHRsGQWgQ3Jlc6VEY2hhbqFjY2gx',
    base64.b64encode(b'not cbor at all').decode('utf-8'),
    encode_token(42),
    encode_token(['v', 't']),
    encode_token({'v': 2}),
    encode_token({'v': 2, 't': 1, 'ttl': 1, 'meta': {}, 'res': ['chan'], 'pat': {}}),
])
def test_parse_token_raises_pubnub_exception_for_invalid_tokens(token):
    pubnub = PubNub(pnconf_copy())

    with pytest.raises(PubNubException):
        pubnub.parse_token(token)


# Grant flags


def test_grant_accepts_delete_as_the_only_flag():
    pubnub = PubNub(pnconf_pam_copy())

    pubnub.grant().channels('ch1').delete(True).validate_params()


def test_grant_without_flags_still_fails():
    pubnub = PubNub(pnconf_pam_copy())

    with pytest.raises(PubNubException, match="At least one flag should be specified"):
        pubnub.grant().channels('ch1').validate_params()


# fetch_messages custom message type


def test_fetch_messages_parses_custom_message_type():
    envelope = {
        'channels': {
            'ch1': [
                {'message': 'with type', 'timetoken': '17000000000000000', 'custom_message_type': 'text-message'},
                {'message': 'without type', 'timetoken': '17000000000000001'},
            ]
        }
    }

    result = PNFetchMessagesResult.from_json(envelope)

    with_type, without_type = result.channels['ch1']
    assert with_type.custom_message_type == 'text-message'
    assert without_type.custom_message_type is None


def test_fetch_message_item_defaults_custom_message_type_to_none():
    assert PNFetchMessageItem('message', '17000000000000000').custom_message_type is None
