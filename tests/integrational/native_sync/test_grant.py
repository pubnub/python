from pubnub.pubnub import PubNub
from tests.integrational.vcr_helper import pn_vcr
from tests.helper import pnconf_pam_copy
from pubnub.models.consumer.access_manager import PNAccessManagerGrantResult

pubnub = PubNub(pnconf_pam_copy())
pubnub.config.uuid = "test_grant"


@pn_vcr.use_cassette('tests/integrational/fixtures/native_sync/pam/grant_with_spaces.yaml',
                     filter_query_parameters=['uuid', 'seqn', 'pnsdk', 'timestamp', 'signature'])
def test_grant_auth_key_with_spaces():
    envelope = pubnub.grant()\
        .read(True)\
        .write(True)\
        .channels("test channel")\
        .auth_keys("client auth key with spaces")\
        .ttl(60)\
        .sync()

    assert isinstance(envelope.result, PNAccessManagerGrantResult)
