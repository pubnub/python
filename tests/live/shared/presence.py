"""Shared scenario data of the presence page for both docsets: literal resource names (NAMES,
read by the janitor through support/resources.py) and the helpers the sync and asyncio tests call outside
the snippet markers. Moved from the old docs-snippets/<docset>/ modules. Coroutine twins of a sync helper
carry an "_async" suffix, and the asyncio tests import them under the sync name.
"""
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
