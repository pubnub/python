"""Scenario data and helpers of the configuration page, shared by the sync and asyncio tests: literal resource names
(NAMES, read by the janitor through support/resources.py) and the helpers the tests call outside the snippet markers.
Coroutine twins of a sync helper carry an "_async" suffix, and the asyncio tests import them under the sync name.
"""
from support import assertions as a
from support.clients import config as client_config

NAMES = ['configured_user', 'filtered']


USER_ID_ERROR = 'UUID missing or invalid type'  # pubnub/pnconfiguration.py, validate_not_empty_string


UNREACHABLE = '127.0.0.1:1'


def real_keys(config):
    """Copy the keyset of the open role onto a config the sample built with made up keys."""
    real = client_config('open')
    config.subscribe_key = real.subscribe_key
    config.publish_key = real.publish_key


def works(clients, pubnub, config):
    """Overwrite the made up keys and prove the client talks to the service. Returns the time() envelope."""
    clients._made.append(pubnub)
    real_keys(config)
    config.daemon = True
    envelope = pubnub.time().sync()
    a.timetoken(str(envelope.result))
    return envelope


class RequestCounter:
    """Replaces the request handler call so that a validation branch can prove no request was sent."""

    def __init__(self):
        self.calls = 0

    def __call__(self, *args, **kwargs):
        self.calls += 1
        raise RuntimeError('a request was sent')


async def works_async(aclients, pubnub, config):
    """Overwrite the made up keys and prove the client talks to the service. Returns the time() envelope."""
    aclients._made.append(pubnub)
    real_keys(config)
    envelope = await pubnub.time().future()
    a.ok(not envelope.status.is_error(), 'time() succeeded')
    a.timetoken(str(envelope.result))
    return envelope


class RequestCounter_async:
    """Replaces the network call of the request handler so that a validation branch can prove nothing was sent."""

    def __init__(self):
        self.calls = 0

    async def __call__(self, *args, **kwargs):
        self.calls += 1
        raise RuntimeError('a request was sent')
