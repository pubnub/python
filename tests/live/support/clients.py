"""Client configuration shared by both docsets. The client layers are clients_sync.py and clients_asyncio.py.

Roles: 'open' (no Access Manager), 'pam' (Access Manager keyset, with the secret key unless secret=False). User ids are
the literal names the tests pass in, there is no run suffix.
"""
import logging
import threading
import time

from pubnub.pnconfiguration import PNConfiguration

from . import env

UNREACHABLE_ORIGIN = '127.0.0.1:1'


PRESENCE_TIMEOUT = 20


def config(role='open', user_id=None, secret=True):
    keys = env.require(role)
    cfg = PNConfiguration()
    prefix = 'PAM_' if role == 'pam' else ''
    cfg.publish_key = keys[prefix + 'PUBLISH_KEY']
    cfg.subscribe_key = keys[prefix + 'SUBSCRIBE_KEY']
    if role == 'pam' and secret:
        cfg.secret_key = keys['PAM_SECRET_KEY']
    cfg.user_id = user_id or 'user'
    # Request threads default to non-daemon (pubnub/pnconfiguration.py, daemon = False). A long poll cannot be
    # interrupted by stop(), so it would hold the process open for up to 310 seconds. Helper clients set daemon=True,
    # so that the lingering thread check sees only real leaks.
    cfg.daemon = True
    # A client that stops without a leave stays an occupant of a shared channel for the presence timeout (default
    # 300 s), and the next test would count it. A short presence timeout lets it drop out between tests.
    cfg.set_presence_timeout(PRESENCE_TIMEOUT)
    return cfg


def unreachable_config(role='open', user_id='unreachable'):
    """A configuration whose origin refuses every connection (no request leaves the machine)."""
    cfg = config(role, user_id)
    cfg.origin = UNREACHABLE_ORIGIN
    cfg.ssl = False
    return cfg


class BaseClients:
    """Hands out clients of one docset and stops them all after the test. Subclasses build the client type."""

    client_class = None

    def __init__(self):
        self._made = []
        self._owners = {}

    def make(self, role='open', user_id=None, secret=True):
        client = self.client_class(config(role, user_id, secret))
        self._made.append(client)
        self._owners[id(client)] = (role, user_id or 'user')
        return client

    def subscriptions_of(self, client):
        """(role, user ID, channels, groups) a client is subscribed to, read before it unsubscribes. None if unknown."""
        owner = self._owners.get(id(client))
        if owner is None:
            return None
        try:
            channels = [c for c in client.get_subscribed_channels() if not c.endswith('-pnpres')]
            groups = [g for g in client.get_subscribed_channel_groups() if not g.endswith('-pnpres')]
        except Exception:  # a client that never subscribed has no subscription manager state (SDK finding)
            return None
        return (*owner, channels, groups) if channels or groups else None

    @staticmethod
    def send_leaves(pending):
        """An explicit leave per client. A client that stops without unsubscribing sends no leave (stop() never
        does), and one that stays an occupant makes the next test miss the join event of the same user ID."""
        from pubnub.endpoints.presence.leave import Leave
        from pubnub.pubnub import PubNub
        for role, user, channels, groups in pending:
            leaver = PubNub(config(role, user))
            try:
                request = Leave(leaver)
                if channels:
                    request.channels(channels)
                if groups:
                    request.channel_groups(groups)
                request.sync()
            except Exception:  # best effort: the janitor and the presence timeout are the backstop
                logging.getLogger(__name__).debug('leave failed, janitor and presence timeout clean up', exc_info=True)
            finally:
                leaver.stop()

    def track(self, client):
        """Stop a client the test built itself (for example from a sample's own configuration).
        Its later request threads are daemon threads, so a long poll that is still in flight cannot hold the process."""
        client.config.daemon = True
        self._made.append(client)
        return client

    def open(self, user_id=None):
        return self.make('open', user_id)

    def pam(self, user_id=None, secret=True):
        return self.make('pam', user_id, secret)

    config = staticmethod(config)


def lingering_threads(wait=10.0):
    """Names of non-daemon threads that are still alive after waiting. The Python analog of an open handle check."""
    deadline = time.monotonic() + wait
    while True:
        alive = [t for t in threading.enumerate() if t is not threading.main_thread() and not t.daemon and t.is_alive()]
        if not alive or time.monotonic() >= deadline:
            return [t.name for t in alive]
        time.sleep(0.25)
