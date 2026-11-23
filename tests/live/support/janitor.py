"""Janitor: cleans exactly the names of resources.py, revokes the application-level Access Manager (v2) grant and can
wait until a client without a token is refused again.

Runs before and after a live run (hooks.py) and after a failure or cancel in CI (cli.py janitor). The old six-hour
sweep by name pattern and the ledger are gone: nothing that is not listed is touched.
"""
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
import time

from pubnub.endpoints.presence.leave import Leave
from pubnub.enums import PNPushEnvironment, PNPushType
from pubnub.exceptions import PubNubException
from pubnub.models.consumer.objects_v2.channel_members import PNUUID
from pubnub.models.consumer.objects_v2.memberships import PNChannelMembership
from pubnub.pubnub import PubNub

from . import env, redact, resources
from .clients import config

FLAGS = ('read', 'write', 'manage', 'delete', 'get', 'update', 'join')
CLOSED_ROUNDS = 3
WORKERS = 8


@dataclass
class Report:
    removed: dict = field(default_factory=dict)
    failed: list = field(default_factory=list)
    critical: list = field(default_factory=list)
    skipped: list = field(default_factory=list)

    def count(self, what):
        self.removed[what] = self.removed.get(what, 0) + 1


def _missing(error):
    return isinstance(error, PubNubException) and (error.get_status_code() == 404 or '404' in str(error))


def _attempt(report, label, fn):
    try:
        fn()
        return True
    except Exception as error:  # collected, the caller decides whether it fails the run
        if not _missing(error):
            report.failed.append(redact.scrub(f'{label}: {type(error).__name__}: {error}'))
        return False


def revoke_application_grant(client):
    """Close the application-level v2 grant (no channel, no auth key): all flags false, ttl 1."""
    builder = client.grant()
    for flag in FLAGS:
        builder = getattr(builder, flag)(False)
    return builder.ttl(1).sync()


def verify_application_grant_closed(timeout=120):
    """A pam client without the secret key and without a token must get 403 on publish and on a history read,
    CLOSED_ROUNDS times in a row. Returns the seconds it took."""
    started = time.monotonic()
    rounds, last = 0, ''
    attempt = 0
    while True:
        attempt += 1
        probe = PubNub(config('pam', f'janitor-probe-{attempt}', secret=False))
        channel = f'janitor-probe-{int(time.time())}-{attempt}'
        open_calls, unclear = [], []
        for label, call in (('publish', lambda: probe.publish().channel(channel).message({'probe': True}).sync()),
                            ('read', lambda: probe.fetch_messages().channels([channel]).count(1).sync())):
            try:
                call()
                open_calls.append(label)
            except PubNubException as error:
                if error.get_status_code() != 403:
                    unclear.append(f'{label}: {error.get_status_code()}')
        probe.stop()
        if not open_calls and not unclear:
            rounds += 1
            if rounds >= CLOSED_ROUNDS:
                return round(time.monotonic() - started, 1)
            time.sleep(1)
            continue
        rounds = 0
        last = ', '.join(open_calls + unclear)
        if time.monotonic() - started + 3 > timeout:
            raise RuntimeError(redact.scrub(f'the pam keyset still lets a client without a token through after '
                                            f'{timeout}s ({last})'))
        time.sleep(3)


def _clean_name(client, name, names, report):
    if _attempt(report, f'delete history of {name}', lambda: client.delete_messages().channel(name).sync()):
        report.count('history')
    listed = None
    try:
        listed = client.list_files(channel=name).sync()
    except Exception as error:
        if not _missing(error):
            report.failed.append(redact.scrub(f'list files of {name}: {type(error).__name__}: {error}'))
    for item in (listed.result.data if listed else []) or []:
        if _attempt(report, f'delete file {item.get("name")} on {name}',
                    lambda: client.delete_file(channel=name, file_name=item['name'], file_id=item['id']).sync()):
            report.count('files')
    if _attempt(report, f'remove channel group {name}',
                lambda: client.remove_channel_group().channel_group(name).sync()):
        report.count('channel_groups')
    try:
        memberships = client.get_memberships(uuid=name, limit=100).sync().result.data or []
        mine = [m['channel']['id'] for m in memberships if m['channel']['id'] in names]
        if mine:
            client.remove_memberships(uuid=name, channel_memberships=[PNChannelMembership.channel(c) for c in mine]) \
                .sync()
            report.count('memberships')
        members = client.get_channel_members(channel=name, limit=100).sync().result.data or []
        mine = [m['uuid']['id'] for m in members if m['uuid']['id'] in names]
        if mine:
            client.remove_channel_members(channel=name, uuids=[PNUUID.uuid(u) for u in mine]).sync()
            report.count('members')
    except Exception as error:
        if not _missing(error):
            report.failed.append(redact.scrub(f'memberships of {name}: {type(error).__name__}: {error}'))
    if _attempt(report, f'remove user metadata {name}', lambda: client.remove_uuid_metadata(uuid=name).sync()):
        report.count('uuid_metadata')
    if _attempt(report, f'remove channel metadata {name}',
                lambda: client.remove_channel_metadata(channel=name).sync()):
        report.count('channel_metadata')


PRESENCE_BATCH = 20


def _clean_presence(role, client, names, report):
    """Make every user ID that is still an occupant of a suite channel leave it. Occupants stay for the presence timeout
    when a client stopped without a leave or a sample only set state, and a later here_now would count them."""
    # Global here_now is a paid feature that the keysets do not have, so ask for the known names in batches.
    by_user = {}
    ordered = sorted(names)
    for start in range(0, len(ordered), PRESENCE_BATCH):
        batch = ordered[start:start + PRESENCE_BATCH]
        try:
            listed = client.here_now().channels(batch).include_uuids(True).sync().result
        except Exception as error:
            if not _missing(error):
                report.failed.append(redact.scrub(f'list occupants ({role}): {type(error).__name__}: {error}'))
            return
        for entry in listed.channels or []:
            for occupant in entry.occupants or []:
                by_user.setdefault(occupant.uuid, set()).add(entry.channel_name)
    for user, channels in sorted(by_user.items()):
        leaver = PubNub(config(role, user))
        try:
            if _attempt(report, f'leave {user}', lambda: Leave(leaver).channels(sorted(channels)).sync()):
                report.count('presence_occupants')
        finally:
            leaver.stop()


def _clean_push(client, report):
    for device in resources.PUSH_DEVICES:
        for push_type in (PNPushType.FCM, PNPushType.GCM):
            _attempt(report, f'remove push device {device}',
                     lambda: client.remove_device_from_push().push_type(push_type).device_id(device).sync())
        for push_type in (PNPushType.APNS, PNPushType.APNS2):
            for environment in (PNPushEnvironment.DEVELOPMENT, PNPushEnvironment.PRODUCTION):
                _attempt(report, f'remove push device {device}',
                         lambda: client.remove_device_from_push().push_type(push_type).device_id(device)
                         .topic(resources.PUSH_TOPIC).environment(environment).sync())
        report.count('push_devices')


def run(roles=None):
    """Clean every role that has keys (or only `roles`). Never raises, the caller reads the report."""
    report = Report()
    names = resources.all_names()
    name_set = set(names)
    for role in roles or env.KEYSET_ROLES:
        if env.missing(role):
            report.skipped.append(f'{role}: no keys')
            continue
        client = PubNub(config(role, 'janitor'))
        try:
            if role == 'pam':
                try:
                    revoke_application_grant(client)
                    report.count('application_grant_revoked')
                except Exception as error:
                    report.critical.append(redact.scrub(f'revoke of the application-level grant failed: {error}'))
            with ThreadPoolExecutor(WORKERS) as pool:
                list(pool.map(lambda n: _clean_name(client, n, name_set, report), names))
            _clean_presence(role, client, name_set, report)
            if role == 'open':
                _clean_push(client, report)
        finally:
            client.stop()
    return report


def format_report(report):
    lines = ['janitor: ' + (', '.join(f'{k} {v}' for k, v in sorted(report.removed.items())) or 'nothing to do')]
    lines += [f'janitor: skipped {s}' for s in report.skipped]
    # One line per distinct error: 80 names that fail with the same 403 are one problem, not 80.
    groups = {}
    for failure in report.failed:
        label, _, error = failure.partition(': ')
        groups.setdefault(error, []).append(label)
    for error, labels in groups.items():
        lines.append(f'janitor: FAILED {len(labels)}x {error[:300]}')
        lines += [f'janitor:   {label}' for label in labels[:3]]
        if len(labels) > 3:
            lines.append(f'janitor:   and {len(labels) - 3} more')
    lines += [f'janitor: CRITICAL {c}' for c in report.critical]
    return lines


def main(argv=()):
    roles = None
    if '--role' in argv:
        roles = [argv[list(argv).index('--role') + 1]]
    report = run(roles)
    for line in format_report(report):
        print(line)
    return 1 if report.failed or report.critical else 0
