"""Cleanup registry: cleanup_after_test(label, fn) runs fn after the test body, newest first, before the test's clients
stop. A 404 is silent, any other failure is printed (redacted) and never hides the test result.

record(kind, name) keeps the call shape of the old harness ledger: it registers the removal of one resource the test
created. Kinds: channel_group, history, uuid_metadata, channel_metadata.
"""
from pubnub.exceptions import PubNubException

from . import redact

_pending = []


def cleanup_after_test(label, fn):
    _pending.append((label, fn))


def _is_404(error):
    return isinstance(error, PubNubException) and (error.get_status_code() == 404 or '404' in str(error))


def run_cleanups():
    """Run and clear every registered cleanup. Never raises."""
    try:
        while _pending:
            label, fn = _pending.pop()
            try:
                fn()
            except Exception as error:  # a cleanup must never replace the test's own result
                if not _is_404(error):
                    print(redact.scrub(f'cleanup {label!r} failed: {type(error).__name__}: {error}'))
    finally:
        stop_helper()


def _helper():
    global _client
    if _client is None:
        from .clients_sync import SyncClients
        _client = SyncClients().sync('open', 'cleanup')
    return _client


_client = None


def stop_helper():
    global _client
    if _client is not None:
        _client.stop()
        _client = None


def record(kind, name):
    """Register the removal of a resource of the open keyset that the test created."""
    if kind == 'channel_group':
        cleanup_after_test(f'remove channel group {name}',
                           lambda: _helper().remove_channel_group().channel_group(name).sync())
    elif kind == 'history':
        cleanup_after_test(f'delete history of {name}', lambda: _helper().delete_messages().channel(name).sync())
    elif kind == 'uuid_metadata':
        cleanup_after_test(f'remove user metadata {name}', lambda: _helper().remove_uuid_metadata(uuid=name).sync())
    elif kind == 'channel_metadata':
        cleanup_after_test(f'remove channel metadata {name}',
                           lambda: _helper().remove_channel_metadata(channel=name).sync())
    else:
        raise ValueError(f'unknown cleanup kind {kind!r}')
