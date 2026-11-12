"""Mask key values, key shapes and Access Manager tokens in any text the suite prints or writes."""
import re
import urllib.parse

_secrets = set()

_SHAPES = [
    re.compile(r'\b(?:pub|sub|sec)-c-[0-9a-fA-F-]{20,}'),
    # Access Manager (v3) tokens are CBOR in base64url, so a real one starts with "qEF2". Granted tokens are also
    # registered, which is the main protection.
    re.compile(r'\bqEF2[A-Za-z0-9_\-%=]{40,}'),
]
MASK = '***'


def register(value):
    """Remember a value (key, granted token) so that scrub() masks it and its URL-encoded forms."""
    if not value or len(value) < 6:
        return
    _secrets.add(value)
    _secrets.add(urllib.parse.quote(value, safe=''))
    _secrets.add(urllib.parse.quote(value))


def registered():
    return set(_secrets)


def scrub(text):
    if not text:
        return text
    out = str(text)
    for secret in sorted(_secrets, key=len, reverse=True):
        out = out.replace(secret, MASK)
    for shape in _SHAPES:
        out = shape.sub(MASK, out)
    return out


def leaks(text):
    """Return the registered secrets that still appear in text (used by the reporter self-test)."""
    return [s for s in _secrets if s in str(text)]
