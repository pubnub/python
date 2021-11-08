from pubnub.pubnub import PubNub
from pubnub.models.consumer.v3.channel import Channel
from tests.integrational.vcr_helper import pn_vcr
from tests.helper import pnconf_pam_stub_copy
from pubnub.models.consumer.v3.access_manager import PNGrantTokenResult, PNRevokeTokenResult

pubnub = PubNub(pnconf_pam_stub_copy())
pubnub.config.uuid = "test_revoke"


@pn_vcr.use_cassette(
    'tests/integrational/fixtures/native_sync/pam/revoke_token.yaml',
    filter_query_parameters=['uuid', 'seqn', 'pnsdk', 'timestamp', 'signature']
)
def test_grant_and_revoke_token():

    grant_envelope = pubnub.grant_token()\
        .channels([Channel.id("test_channel").read().write().manage().update().join().delete()])\
        .authorized_uuid("test")\
        .ttl(60)\
        .sync()

    assert isinstance(grant_envelope.result, PNGrantTokenResult)
    token = grant_envelope.result.get_token()
    assert token

    revoke_envelope = pubnub.revoke_token(token).sync()
    assert isinstance(revoke_envelope.result, PNRevokeTokenResult)
    assert revoke_envelope.result.status == 200
