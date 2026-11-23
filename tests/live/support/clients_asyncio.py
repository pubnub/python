"""Client layer of the asyncio docset: PubNubAsyncio clients (pubnub/pubnub_asyncio.py, EventEngineSubscriptionManager
by default). stop() is a coroutine, so close() must run on the test's own event loop."""
import asyncio

from pubnub.pubnub_asyncio import PubNubAsyncio
from .clients import BaseClients


class AsyncioClients(BaseClients):
    client_class = PubNubAsyncio

    def asyncio(self, role='open', user_id=None, secret=True):
        """Kept from the old harness: aclients.asyncio('open', 'publisher')."""
        return self.make(role, user_id, secret)

    async def close(self):
        pending = [x for x in (self.subscriptions_of(c) for c in self._made if isinstance(c, PubNubAsyncio)) if x]
        for client in self._made:
            if not isinstance(client, PubNubAsyncio):
                continue
            try:
                # Always leave: a sample can subscribe without the test knowing, and a client that stops without
                # a leave stays an occupant of the shared channel until the presence timeout.
                # unsubscribe_all() raises AttributeError on a client that never subscribed (SDK finding)
                try:
                    client.unsubscribe_all()
                    # The leave request is a fire-and-forget task: let it run before stop() cancels pending tasks.
                    await asyncio.sleep(1)
                except AttributeError:
                    pass
            finally:
                await client.stop()
        self.send_leaves(pending)
        self._made = []
