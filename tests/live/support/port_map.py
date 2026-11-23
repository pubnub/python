"""Port map: proof that the port from docs-snippets/ (the old suite) to tests/live/ lost no test.

    python -u tests/live/cli.py port-map            writes tests/live/port-map.json
    python -u tests/live/cli.py port-map --check    fails when a check fails or port-map.json is stale

Reads the old suite from git at BASE (the commit the docs preview reads, plan section 1.1) with the old registry
logic (the @step and @compile_only decorators), and the new tier with snippet_scan. Checks:
  1. every old snippet id (311) exists in the same docset of the new tier, and no id is new
  2. every old step (193 live, 3 compile-only) maps to exactly one new test or compile-only function that holds all
     its ids, no two old steps map to the same new function, and the mode is unchanged
  3. the old role of each step is one of the roles the new test uses
  4. the text the docs show for each id (docs_extract) is byte for byte the same in the old and the new file,
     except the approved changes of tests/live/port-text-changes.md (APPROVED_TEXT_CHANGES, and APPROVED_MODE_CHANGES
     for check 2). An approved entry whose text or mode no longer differs is reported too.
Pure reads (git show, files). No network.
"""
import ast
import json
import subprocess
from collections import Counter

from . import LIVE_DIR, REPO_ROOT, snippet_scan, snippets

BASE = 'f2d1601'
MAP_FILE = LIVE_DIR / 'port-map.json'
EXPECTED = {'ids': 311, 'live_steps': 193, 'compile_only': 3}


def base_available(base=BASE):
    """True when the commit of the old suite is in this checkout (the port proof needs its files)."""
    return subprocess.run(['git', 'cat-file', '-e', base + '^{commit}'], cwd=REPO_ROOT,
                          capture_output=True).returncode == 0


def _git(*args):
    return subprocess.run(['git', *args], cwd=REPO_ROOT, capture_output=True, text=True, check=True).stdout


def old_suite(base=BASE):
    steps, texts = [], {}
    for path in _git('ls-tree', '-r', '--name-only', base, 'docs-snippets/sync', 'docs-snippets/asyncio').split():
        if not path.endswith('.py') or path.rsplit('/', 1)[1].startswith('_'):
            continue
        docset = path.split('/')[1]
        text = _git('show', f'{base}:{path}')
        texts[path] = text
        for node in ast.walk(ast.parse(text)):
            if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue
            for deco in node.decorator_list:
                if isinstance(deco, ast.Call) and isinstance(deco.func, ast.Name) and \
                        deco.func.id in ('step', 'compile_only', 'stub'):
                    kw = {k.arg: ast.literal_eval(k.value) for k in deco.keywords}
                    steps.append({'docset': docset, 'old_file': path, 'old_test': node.name,
                                  'ids': [ast.literal_eval(a) for a in deco.args],
                                  'mode': {'step': 'live', 'compile_only': 'compile-only'}.get(deco.func.id, 'stub'),
                                  'role': kw.get('role', 'open')})
    return steps, texts


# Ids written after the port, each with the reason. They have no old step, so they are not part of the loss proof.
ADDED_AFTER_PORT = {
    # The whole examples/crypto.py sample, formerly embedded by a SHA pin (docs configuration page)
    ('sync', 'cipher_mode_experiment'),
}

# Sample text changes approved on 2026-11-23 (tests/live/port-text-changes.md sections 1 to 3), keyed by (docset, id).
# Check 4 accepts a differing docs text only for these keys, and reports a key whose text no longer differs, so the
# byte-for-byte proof stays strict for every other id.
_ENVELOPE_CHECK = ('section 1: the asyncio sample checks envelope.is_error() after the awaited call, and reads '
                   'the result only in the else branch (follow-up)')
_APNS_TOKEN = 'section 2: literal APNs device token instead of APNS2_DEVICE'
_SAMPLE_FILE = 'section 2: the sample opens "sample.gif" instead of the FIXTURE constant'
_SHORT_WAIT = 'section 3: live logging sample, asyncio.sleep(5) instead of asyncio.sleep(500)'
APPROVED_TEXT_CHANGES = {}
for _ident in (
        'add_channels_builder add_channels_named add_channels_to_push_kwargs add_message_action_builder '
        'add_message_action_named delete_channel_group_builder delete_file_builder delete_message_single_builder '
        'delete_message_single_named delete_messages_builder delete_messages_named download_file_builder '
        'fetch_history_builder fetch_history_multiple fetch_history_named fetch_history_range fire_message fire_post '
        'get_file_url_builder get_message_actions_builder get_message_actions_named get_state_builder '
        'grant_categories grant_channel_all_users grant_channel_ro_auth grant_presence grant_subkey_all '
        'grant_token_builder grant_token_categories grant_token_multi grant_token_multi_regex grant_token_regex '
        'grant_token_spaces_builder grant_token_spaces_multi grant_token_spaces_multi_regex grant_token_spaces_regex '
        'here_now_groups here_now_occupancy here_now_state history_basic history_end history_include_timetoken '
        'history_paging history_reverse history_start_reverse list_channels_builder list_channels_named '
        'list_files_builder list_push_channels_builder message_counts_builder message_counts_multiple_builder '
        'message_counts_multiple_named message_counts_named publish_builder publish_file_message_builder '
        'publish_named publish_store_post remove_channels_builder remove_channels_from_push_builder '
        'remove_channels_named remove_device_from_push_builder remove_message_action_builder '
        'remove_message_action_named revoke_token send_file_options set_state_builder set_state_groups_builder '
        'signal_message time_get where_now_other where_now_self').split():
    APPROVED_TEXT_CHANGES[('asyncio', _ident)] = _ENVELOPE_CHECK
for _docset, _idents in (
        ('sync', 'add_channels_to_push_builder add_channels_to_push_named list_push_channels_builder '
                 'list_push_channels_named remove_channels_from_push_builder remove_channels_from_push_named '
                 'remove_device_from_push_builder remove_device_from_push_named'),
        ('asyncio', 'add_channels_to_push_builder add_channels_to_push_kwargs list_push_channels_builder '
                    'remove_channels_from_push_builder remove_device_from_push_builder')):
    for _ident in _idents.split():
        _key = (_docset, _ident)
        APPROVED_TEXT_CHANGES[_key] = ' and '.join(filter(None, (APPROVED_TEXT_CHANGES.get(_key), _APNS_TOKEN)))
_SYNC_FILE = 'section 2 follow-up: the sync sample opens "sample.gif" and sets save_path itself'
for _ident in ('send_file_builder', 'send_file_custom_message_type', 'download_file_builder'):
    APPROVED_TEXT_CHANGES[('sync', _ident)] = _SYNC_FILE
for _ident in ('send_file_builder', 'send_file_options'):
    _key = ('asyncio', _ident)
    APPROVED_TEXT_CHANGES[_key] = ' and '.join(filter(None, (APPROVED_TEXT_CHANGES.get(_key), _SAMPLE_FILE)))
APPROVED_TEXT_CHANGES[('asyncio', 'subscribe_old_logging')] = _SHORT_WAIT
APPROVED_TEXT_CHANGES[('asyncio', 'download_file_builder')] += \
    ' and section 2 follow-up: the sample sets save_path itself'
_IMPORTS = 'section 2 follow-up: the sample imports the SDK classes it uses (added or no longer hidden)'
for _docset, _idents in (
        ('sync', 'add_channels_to_push_builder add_channels_to_push_named add_message_action_builder '
                 'add_message_action_named crypto_module_aes_cbc crypto_module_legacy crypto_module_partial '
                 'get_all_channel_metadata_builder get_all_channel_metadata_named get_all_uuid_metadata_builder '
                 'get_all_uuid_metadata_named get_channel_members_builder get_channel_members_named '
                 'get_memberships_builder get_memberships_named grant_token_multi_regex grant_token_named '
                 'grant_token_regex grant_token_spaces_multi grant_token_spaces_multi_regex grant_token_spaces_named '
                 'grant_token_spaces_regex list_push_channels_builder list_push_channels_named listeners_generic '
                 'listeners_status manage_channel_members_builder manage_channel_members_named '
                 'manage_memberships_builder manage_memberships_named pnchannelmembership_class pnuuid_class '
                 'remove_channel_members_builder remove_channel_members_named remove_channels_from_push_builder '
                 'remove_channels_from_push_named remove_device_from_push_builder remove_device_from_push_named '
                 'remove_memberships_builder remove_memberships_named set_channel_members_builder '
                 'set_channel_members_named set_memberships_builder set_memberships_named'),
        ('asyncio', 'add_channels_to_push_builder add_channels_to_push_kwargs add_message_action_builder '
                    'add_message_action_named configuration_full grant_token_multi_regex grant_token_regex '
                    'grant_token_spaces_multi grant_token_spaces_multi_regex grant_token_spaces_regex '
                    'list_push_channels_builder listeners_generic listeners_status remove_channels_from_push_builder '
                    'remove_device_from_push_builder')):
    for _ident in _idents.split():
        _key = (_docset, _ident)
        APPROVED_TEXT_CHANGES[_key] = ' and '.join(filter(None, (APPROVED_TEXT_CHANGES.get(_key), _IMPORTS)))

# Old compile-only steps that run live since 2026-11-23 (port-text-changes.md section 3), keyed by (docset, id).
APPROVED_MODE_CHANGES = {
    ('sync', 'reconnect_documented'): 'PR 242 added PubNub.reconnect(), the old reason (AttributeError) is gone',
    ('sync', 'subscribe_old_logging'): 'open keys on one hidden line, DEBUG output checked under caplog',
    ('asyncio', 'subscribe_old_logging'): 'open keys on one hidden line, DEBUG output checked under caplog',
}


def build(base=BASE):
    steps, texts = old_suite(base)
    _, new = snippet_scan.scan_tier()
    by_id = {}
    for s in new:
        by_id.setdefault((s.file.docset, s.id), []).append(s)
    problems, rows, owners = [], [], Counter()
    approved_texts, approved_modes = set(), set()
    old_ids = {(st['docset'], i) for st in steps for i in st['ids']}
    for key in sorted(set(by_id) - old_ids - ADDED_AFTER_PORT):
        problems.append(f'new id without an old step: {key[0]} {key[1]}')
    for st in steps:
        found = [by_id.get((st['docset'], i), []) for i in st['ids']]
        missing = [i for i, f in zip(st['ids'], found) if not f]
        if missing:
            problems.append(f'{st["old_file"]}::{st["old_test"]}: ids missing in the new tier: {", ".join(missing)}')
            continue
        funcs = {(f[0].file.rel, f[0].func.name) for f in found}
        if len(funcs) != 1:
            problems.append(f'{st["old_file"]}::{st["old_test"]}: ids are split over {sorted(funcs)}')
            continue
        snip = found[0][0]
        new_file, new_test = funcs.pop()
        owners[(new_file, new_test)] += 1
        mode = snip.mode
        mode_key = next((k for k in ((st['docset'], i) for i in st['ids']) if k in APPROVED_MODE_CHANGES), None)
        if mode != st['mode']:
            if mode_key:
                approved_modes.add(mode_key)
            else:
                problems.append(f'{st["old_file"]}::{st["old_test"]}: mode {st["mode"]} became {mode}')
        roles = snip.roles
        if mode == 'live' and st['role'] not in roles:
            problems.append(f'{st["old_file"]}::{st["old_test"]}: old role {st["role"]} not in new roles {roles}')
        for ident, f in zip(st['ids'], found):
            old_text = snippets.docs_extract(texts[st['old_file']], [ident])
            new_text = snippets.docs_extract(f[0].file.text, [ident])
            if old_text != new_text:
                if (st['docset'], ident) in APPROVED_TEXT_CHANGES:
                    approved_texts.add((st['docset'], ident))
                else:
                    problems.append(f'{st["old_file"]} {ident}: the docs text differs in {f[0].file.rel}')
        rows.append({'docset': st['docset'], 'old_file': st['old_file'], 'old_test': st['old_test'],
                     'new_file': new_file, 'new_test': new_test, 'ids': st['ids'], 'mode': mode,
                     'old_mode': st['mode'], 'old_role': st['role'], 'new_roles': roles})
    for key, n in owners.items():
        if n > 1:
            problems.append(f'{key[0]}::{key[1]} holds {n} old steps')
    for key in sorted(set(APPROVED_TEXT_CHANGES) - approved_texts):
        problems.append(f'approved text change {key[0]} {key[1]}: the docs text no longer differs (remove the entry)')
    for key in sorted(set(APPROVED_MODE_CHANGES) - approved_modes):
        problems.append(f'approved mode change {key[0]} {key[1]}: the mode no longer differs (remove the entry)')
    # Counts of the old suite (the loss proof). An approved mode change keeps the old count.
    counts = {'ids': len(old_ids), 'live_steps': sum(r['old_mode'] == 'live' for r in rows),
              'compile_only': sum(r['old_mode'] == 'compile-only' for r in rows),
              'approved_text_changes': len(approved_texts), 'approved_mode_changes': len(approved_modes)}
    for name, want in EXPECTED.items():
        if counts[name] != want:
            problems.append(f'count {name}: {counts[name]}, expected {want}')
    data = {'$comment': f'GENERATED by python -u tests/live/cli.py port-map from git {base} and tests/live. '
                        'One row per old step.', 'base': base, 'counts': counts,
            'steps': sorted(rows, key=lambda r: (r['docset'], r['old_file'], r['old_test']))}
    return data, problems


def main(argv=()):
    argv = list(argv)
    base = argv[argv.index('--base') + 1] if '--base' in argv else BASE
    data, problems = build(base)
    text = json.dumps(data, indent=1) + '\n'
    for p in problems:
        print('port-map:', p)
    c = data['counts']
    print(f'port-map: {c["ids"]} old ids, {c["live_steps"]} live steps, {c["compile_only"]} compile-only, '
          f'{c["approved_text_changes"]} approved text changes, {c["approved_mode_changes"]} approved mode changes, '
          f'{len(problems)} problems (base {base})')
    if '--check' in argv:
        if not MAP_FILE.exists() or MAP_FILE.read_text() != text:
            print('port-map: port-map.json is stale. Run: python -u tests/live/cli.py port-map')
            return 1
        return 1 if problems else 0
    MAP_FILE.write_text(text)
    print('port-map: wrote port-map.json')
    return 1 if problems else 0
