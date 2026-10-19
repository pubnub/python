from pubnub.pubnub import PubNub
from tests.helper import pnconf_pam_copy


# Token without category-level permissions.
TOKEN_WITHOUT_CATEGORIES = (
    "qEF2AkF0GmFLd-NDdHRsGQWgQ3Jlc6VEY2hhbqFjY2gxGP9DZ3JwoWNjZzEY_0N1c3KgQ3NwY6BEdXVpZKFldXVpZDEY_"
    "0NwYXSlRGNoYW6gQ2dycKBDdXNyoENzcGOgRHV1aWShYl4kAURtZXRho2VzY29yZRhkZWNvbG9yY3JlZGZhdXRob3JlcGFu"
    "ZHVEdXVpZGtteWF1dGh1dWlkMUNzaWdYIP2vlxHik0EPZwtgYxAW3-LsBaX_WgWdYvtAXpYbKll3"
)

# Token granting category-level GET permission for channels and UUIDs.
TOKEN_WITH_CATEGORIES = (
    "qGF2AmF0GmFLd-NjdHRsGQWgY3Jlc6BjcGF0oGRtZXRhoGNzaWdVcGxhY2Vob2xkZXItc2lnbmF0dXJlY2NhdKJkY2hh"
    "bhggZHV1aWQYIA=="
)

# Token granting category-level GET permission only for UUIDs.
TOKEN_WITH_UUID_CATEGORY = (
    "qGF2AmF0GmFLd-NjdHRsGQWgY3Jlc6BjcGF0oGRtZXRhoGNzaWdVcGxhY2Vob2xkZXItc2lnbmF0dXJlY2NhdKFkdXVp"
    "ZBgg"
)

# Token containing a channel category without the GET permission bit.
TOKEN_WITH_CHANNEL_CATEGORY_NO_GET = (
    "qGF2AmF0GmFLd-NjdHRsGQWgY3Jlc6BjcGF0oGRtZXRhoGNzaWdVcGxhY2Vob2xkZXItc2lnbmF0dXJlY2NhdKFkY2hh"
    "bgA="
)

# Token containing an unsupported category that should be ignored.
TOKEN_WITH_UNKNOWN_CATEGORY = (
    "qGF2AmF0GmFLd-NjdHRsGQWgY3Jlc6BjcGF0oGRtZXRhoGNzaWdVcGxhY2Vob2xkZXItc2lnbmF0dXJlY2NhdKFjZ3Jw"
    "GCA="
)

# Token granting GET on named resources and patterns, but not on categories.
TOKEN_WITH_RESOURCE_AND_PATTERN_GET = (
    "p2F2AmF0GmFLd-NjdHRsGQWgY3Jlc6JkY2hhbqFjY2gxGCBkdXVpZKFldXVpZDEYIGNwYXSiZGNoYW6hYi4qGCBkdXVp"
    "ZKFiLioYIGRtZXRhoGNzaWdVcGxhY2Vob2xkZXItc2lnbmF0dXJl"
)


pubnub = PubNub(pnconf_pam_copy())


def test_v3_token_parsing():
    token = pubnub.parse_token(TOKEN_WITHOUT_CATEGORIES)
    assert token["version"] == 2
    assert token["timestamp"] == 1632335843
    assert token["ttl"] == 1440
    assert token["authorized_uuid"] == "myauthuuid1"
    assert token["meta"] == {"score": 100, "color": "red", "author": "pandu"}
    assert token["resources"]["channels"]["ch1"]


def test_v3_token_parsing_without_categories():
    token = pubnub.parse_token(TOKEN_WITHOUT_CATEGORIES)
    assert "categories" not in token


def test_v3_token_parsing_categories():
    token = pubnub.parse_token(TOKEN_WITH_CATEGORIES)

    assert token["categories"] == {
        "channels": {"get": True},
        "uuids": {"get": True},
    }


def test_v3_token_parsing_single_category():
    token = pubnub.parse_token(TOKEN_WITH_UUID_CATEGORY)
    assert token["categories"] == {"uuids": {"get": True}}


def test_v3_token_parsing_category_without_get_bit():
    token = pubnub.parse_token(TOKEN_WITH_CHANNEL_CATEGORY_NO_GET)
    assert token["categories"] == {"channels": {"get": False}}


def test_v3_token_parsing_unknown_category_is_ignored():
    token = pubnub.parse_token(TOKEN_WITH_UNKNOWN_CATEGORY)
    assert "categories" not in token


def test_v3_token_parsing_resource_get_is_not_enumeration():
    token = pubnub.parse_token(TOKEN_WITH_RESOURCE_AND_PATTERN_GET)

    assert token["resources"]["channels"]["ch1"]["get"] is True
    assert token["patterns"]["channels"][".*"]["get"] is True
    assert token["resources"]["uuids"]["uuid1"]["get"] is True
    assert token["patterns"]["uuids"][".*"]["get"] is True
    assert "categories" not in token
