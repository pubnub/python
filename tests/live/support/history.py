"""Seed helpers for Message Persistence tests: publish outside the markers, then wait until the service shows exactly
the seeded timetokens. A retried publish can be stored twice (F3), so a seed run counts its own retries."""
from dataclasses import dataclass, field

from . import retry
from .wait import asettled, settled


@dataclass
class SeedRun:
    retried: int = 0
    tokens: list = field(default_factory=list)


def seed_publish(run, client, channel, message, **options):
    """Publish one message (sync) and remember its timetoken."""
    def once():
        builder = client.publish().channel(channel).message(message)
        for name, value in options.items():
            builder = getattr(builder, name)(value)
        return builder.sync()

    attempts = {'n': 0}

    def counted():
        attempts['n'] += 1
        return once()

    envelope = retry.retry_transient(counted, label=f'seed publish to {channel}')
    run.retried += attempts['n'] - 1
    run.tokens.append(envelope.result.timetoken)
    return envelope


def _stored_tokens(envelope, channel):
    return [item.timetoken for item in envelope.result.channels.get(channel, [])]


def settle_seeded(run, client, channel):
    """The channel's history holds every seeded timetoken (a retried publish may add one more)."""
    def check():
        stored = _stored_tokens(client.fetch_messages().channels([channel]).count(100).sync(), channel)
        missing = [t for t in run.tokens if t not in stored]
        if missing:
            raise AssertionError(f'not stored yet: {missing}')
        if len(stored) > len(run.tokens) + run.retried:
            raise AssertionError(f'{len(stored)} stored, expected at most {len(run.tokens) + run.retried}')
    settled(check, timeout=30, what=f'history of {channel} holds the seeded messages')


async def asettle_seeded(run, client, channel):
    async def check():
        envelope = await client.fetch_messages().channels([channel]).count(100).future()
        if envelope.is_error():
            raise AssertionError(f'fetch_messages failed: {envelope}')
        stored = _stored_tokens(envelope, channel)
        missing = [t for t in run.tokens if t not in stored]
        if missing:
            raise AssertionError(f'not stored yet: {missing}')
    await asettled(check, timeout=30, what=f'history of {channel} holds the seeded messages')
