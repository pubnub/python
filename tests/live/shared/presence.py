"""Shared scenario data of the presence page for both docsets: literal resource names (NAMES,
read by the janitor through support/resources.py) and the helpers the sync and asyncio tests call outside
the snippet markers. Moved from the old docs-snippets/<docset>/ modules. Coroutine twins of a sync helper
carry an "_async" suffix, and the asyncio tests import them under the sync name.
"""
from support import assertions as a
from support.clients import BaseClients, config
from support.wait import PRESENCE_TIMEOUT, settled

NAMES = ['cg2', 'cg3', 'gr1', 'gr2', 'gr3', 'grouped_1', 'grouped_2', 'grouped_3', 'some-other-uuid', 'such_uuid']


class Printed:
    """Everything the docs code printed so far."""

    def __init__(self, capsys):
        self._capsys = capsys
        self._parts = []

    def text(self):
        self._parts.append(self._capsys.readouterr().out)
        return ''.join(self._parts)


def occupants_of(here_now, channel):
    """uuids of one channel in a PNHereNowResult, sorted. The result holds a list of PNHereNowChannelData."""
    found = [c for c in here_now.result.channels if c.channel_name == channel]
    return sorted(o.uuid for o in found[0].occupants) if found and found[0].occupants is not None else None


def occupancy_of(here_now, channel):
    found = [c for c in here_now.result.channels if c.channel_name == channel]
    return found[0].occupancy if found else None


def own_occupants(here_now, channel, mine):
    """The test's own user IDs that here_now lists on a channel, sorted. Shared channels are persistent, so other
    occupants (a user ID of an earlier test whose leave the service has not applied yet) are ignored."""
    return sorted(set(occupants_of(here_now, channel) or []) & set(mine))


def consistent(here_now):
    """Counts of one here_now response agree with its own lists (when it lists the user IDs)."""
    for c in here_now.result.channels:
        if c.occupants:
            a.eq(c.occupancy, len(c.occupants), f'occupancy of {c.channel_name} counts its listed occupants')
    a.eq(here_now.result.total_occupancy, sum(c.occupancy for c in here_now.result.channels), 'total occupancy')


def not_present(channel, user_ids):
    """Precondition of a join test: the user IDs are not occupants of the channel, on consecutive here_now reads.

    The service emits a join only for a user ID that is not already an occupant, and a user ID of an earlier test
    stays listed until its leave is applied or it times out. An explicit leave first, then the wait. Blocking: the
    asyncio tests call it too, before they start the subscriptions it concerns.
    """
    from pubnub.pubnub import PubNub
    BaseClients.send_leaves([('open', uid, [channel], []) for uid in user_ids])
    reader = PubNub(config('open', 'presence_check'))
    try:
        def gone():
            here = reader.here_now().channels(channel).include_uuids(True).sync()
            a.eq(own_occupants(here, channel, user_ids), [], f'{", ".join(user_ids)} still listed on {channel}')
        settled(gone, timeout=PRESENCE_TIMEOUT, what=f'user IDs not present on {channel}')
    finally:
        reader.stop()
