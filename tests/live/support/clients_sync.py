"""Client layer of the sync docset: PubNub clients (pubnub/pubnub.py, NativeSubscriptionManager)."""
from pubnub.pubnub import PubNub

from .clients import BaseClients


class SyncClients(BaseClients):
    client_class = PubNub

    def sync(self, role='open', user_id=None, secret=True):
        """Kept from the old harness: clients.sync('open', 'publisher')."""
        return self.make(role, user_id, secret)

    def close(self):
        pending = [x for x in (self.subscriptions_of(c) for c in self._made if isinstance(c, PubNub)) if x]
        for client in self._made:
            if not isinstance(client, PubNub):
                continue
            try:
                # Always leave: a sample can subscribe without the test knowing, and a client that stops without
                # a leave stays an occupant of the shared channel until the presence timeout.
                client.unsubscribe_all()
            finally:
                client.stop()
        self.send_leaves(pending)
        self._made = []
