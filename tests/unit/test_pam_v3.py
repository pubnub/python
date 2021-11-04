from pubnub.pubnub import PubNub
from tests.helper import pnconf_pam_copy


TEST_TOKEN = (
    "qEF2AkF0GmFLd-NDdHRsGQWgQ3Jlc6VEY2hhbqFjY2gxGP9DZ3JwoWNjZzEY_0N1c3KgQ3NwY6BEdXVpZKFldXVpZDEY_"
    "0NwYXSlRGNoYW6gQ2dycKBDdXNyoENzcGOgRHV1aWShYl4kAURtZXRho2VzY29yZRhkZWNvbG9yY3JlZGZhdXRob3JlcGFu"
    "ZHVEdXVpZGtteWF1dGh1dWlkMUNzaWdYIP2vlxHik0EPZwtgYxAW3-LsBaX_WgWdYvtAXpYbKll3"
)


pubnub = PubNub(pnconf_pam_copy())


def test_v3_token_parsing():
    token = pubnub.parse_token(TEST_TOKEN)
    assert token["version"] == 2
    assert token["timestamp"] == 1632335843
    assert token["ttl"] == 1440
    assert token["authorized_uuid"] == "myauthuuid1"
    assert token["meta"] == {"score": 100, "color": "red", "author": "pandu"}
    assert token["resources"]["channels"]["ch1"]
