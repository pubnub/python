from pubnub.pubnub import PubNub
from tests.helper import pnconf_pam_copy


TEST_TOKEN = (
    'p0F2AkF0GmB4Sd9DdHRsD0NyZXOkRGNoYW6iY2ZvbwFjYmFyAUNncnCiY2ZvbwFjYmFyAUN1c3KgQ'
    '3NwY6BDcGF0pERjaGFuoENncnCgQ3VzcqBDc3BjoERtZXRhoENzaWdYIBHsbMOeRAHUvsCURvZ3Yehv74QvPT4xqfHY5JPONmyJ'
)

pubnub = PubNub(pnconf_pam_copy())


def test_v3_token_parsing():
    token = pubnub.parse_token(TEST_TOKEN)
    assert token['v'] == 2  # Token version
    assert token['t'] == 1618495967  # Token creation time
    assert token['ttl'] == 15
    assert token['res']
    assert token['sig']
