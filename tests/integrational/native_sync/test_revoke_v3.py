import pytest
import time
from pubnub.exceptions import PubNubException
from pubnub.pubnub import PubNub
from pubnub.models.consumer.v3.channel import Channel
from tests.integrational.vcr_helper import pn_vcr
from tests.helper import pnconf_pam_env_copy
from pubnub.models.consumer.v3.access_manager import PNGrantTokenResult, PNRevokeTokenResult

pubnub = PubNub(pnconf_pam_env_copy(uuid="test_revoke"))
pubnub_with_token = PubNub(pnconf_pam_env_copy(uuid="test_revoke_verify", auth_key=None, secret_key=None))


@pn_vcr.use_cassette(
    'tests/integrational/fixtures/native_sync/pam/revoke_token.json', serializer='pn_json',
    filter_query_parameters=['uuid', 'seqn', 'pnsdk', 'timestamp', 'signature']
)
def test_grant_and_revoke_token():
    grant_envelope = pubnub.grant_token() \
        .channels([Channel.id("test_channel").read().write().manage().update().join().delete()]) \
        .authorized_uuid("test") \
        .ttl(60) \
        .sync()

    assert isinstance(grant_envelope.result, PNGrantTokenResult)
    token = grant_envelope.result.get_token()
    assert token

    revoke_envelope = pubnub.revoke_token(token).sync()
    assert isinstance(revoke_envelope.result, PNRevokeTokenResult)
    assert revoke_envelope.result.status == 200


def test_revoke_token_verify_operations():
    with pn_vcr.use_cassette(
        'tests/integrational/fixtures/native_sync/pam/revoke_token_verify_operations.json', serializer='pn_json',
        filter_query_parameters=['uuid', 'seqn', 'pnsdk', 'timestamp', 'signature']
    ) as cassette:
        recording = (True if len(cassette.data) == 0 else False)  # we are recording blank cassette

        grant_envelope = pubnub.grant_token()\
            .channels([Channel.id("test_channel").read().write().manage().update().join().delete()])\
            .authorized_uuid("test_revoke_verify")\
            .ttl(1)\
            .sync()
        token = grant_envelope.result.get_token()
        assert token

        # Configure a new PubNub instance with the token
        pubnub_with_token.set_token(token)

        # Verify the token works before revocation
        try:
            pubnub_with_token.publish()\
                .channel("test_channel")\
                .message("test message")\
                .sync()
        except PubNubException:
            pytest.fail("Token should be valid before revocation")

        # Revoke the token
        revoke_envelope = pubnub.revoke_token(token).sync()
        assert revoke_envelope.result.status == 200

        if recording:
            time.sleep(10)

        # Verify operations fail after revocation
        with pytest.raises(PubNubException) as exc_info:
            pubnub_with_token.publish() \
                .channel("test_channel") \
                .message("test message") \
                .sync()
        assert "Token is revoked" in str(exc_info.value)


def test_revoke_expired_token():
    with pn_vcr.use_cassette(
        'tests/integrational/fixtures/native_sync/pam/revoke_expired_token.json', serializer='pn_json',
        filter_query_parameters=['uuid', 'seqn', 'pnsdk', 'timestamp', 'signature']
    ) as cassette:
        recording = (True if len(cassette.data) == 0 else False)  # we are recording blank cassette

        # Grant a token with minimum TTL (1 minute)
        grant_envelope = pubnub.grant_token()\
            .channels([Channel.id("test_channel").read()])\
            .authorized_uuid("test")\
            .ttl(1)\
            .sync()

        token = grant_envelope.result.get_token()

        # Wait for token to expire (in real scenario)
        # Note: In the test environment with VCR cassettes,
        # we're testing the API response for an expired token
        if recording:
            time.sleep(61)  # Wait for token to expire

        # Attempt to revoke expired token
        with pytest.raises(PubNubException) as exc_info:
            pubnub.revoke_token(token).sync()
        assert "Invalid token" in str(exc_info.value) or "Token expired" in str(exc_info.value)
