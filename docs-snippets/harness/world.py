"""Client factories and the ledger of created resources. Closes every client it made."""
import json
import os
import threading
from pathlib import Path
import time

from pubnub.pnconfiguration import PNConfiguration
from pubnub.pubnub import PubNub
from pubnub.pubnub_asyncio import PubNubAsyncio

from . import env, names, registry


def ledger_path():
    base = os.environ.get('DOCS_SNIPPETS_LEDGER_DIR') or str(registry.ROOT / '.run')
    return Path(base) / f'ledger-{names.run_suffix()}.jsonl'


def record(kind, name):
    """Remember a resource this run created, so the janitor can remove it."""
    path = ledger_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('a') as f:
        f.write(json.dumps({'kind': kind, 'name': name, 'ts': int(time.time())}) + '\n')


def config(role='open', user_id=None, secret=True):
    keys = env.require(role)
    cfg = PNConfiguration()
    prefix = 'PAM_' if role == 'pam' else ''
    cfg.publish_key = keys[prefix + 'PUBLISH_KEY']
    cfg.subscribe_key = keys[prefix + 'SUBSCRIBE_KEY']
    if role == 'pam' and secret:
        cfg.secret_key = keys['PAM_SECRET_KEY']
    cfg.user_id = names.with_suffix(user_id or 'user')
    # Request threads default to non-daemon. A long poll cannot be interrupted by stop(), so it would hold the process
    # open for up to 310 seconds. The suite sets daemon=True so that the lingering thread check sees only real leaks.
    cfg.daemon = True
    return cfg


class Clients:
    """Hands out clients and stops them all at the end of the step."""

    def __init__(self):
        self._made = []

    def sync(self, role='open', user_id=None, secret=True):
        client = PubNub(config(role, user_id, secret))
        self._made.append(client)
        return client

    def asyncio(self, role='open', user_id=None, secret=True):
        client = PubNubAsyncio(config(role, user_id, secret))
        self._made.append(client)
        return client

    def close_sync(self):
        for client in self._made:
            if isinstance(client, PubNub):
                try:
                    if getattr(client, 'subscribed_by_suite', False):
                        client.unsubscribe_all()
                finally:
                    client.stop()

    async def close_asyncio(self):
        for client in self._made:
            if isinstance(client, PubNubAsyncio):
                try:
                    # unsubscribe_all() raises AttributeError on a client that never subscribed (SDK finding)
                    if getattr(client, 'subscribed_by_suite', False):
                        client.unsubscribe_all()
                finally:
                    await client.stop()


def lingering_threads(wait=10.0):
    """Names of non-daemon threads that are still alive after waiting. The Python analog of an open handle check."""
    deadline = time.monotonic() + wait
    while True:
        alive = [t for t in threading.enumerate() if t is not threading.main_thread() and not t.daemon and t.is_alive()]
        if not alive or time.monotonic() >= deadline:
            return [t.name for t in alive]
        time.sleep(0.25)
