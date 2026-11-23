# Sample text changes of the port

The port from `docs-snippets/` keeps every published region byte for byte (proof: `python -u tests/live/cli.py port-map --check`, check 4). This file lists the text changes the port found worth making. Each one needed approval (plan question Q6) before the docs repoint. An approved change is made in the test file and in this list together, and its (docset, id) goes into `APPROVED_TEXT_CHANGES` or `APPROVED_MODE_CHANGES` of `support/port_map.py`, so check 4 stays strict for every other id.

Proposed 2026-11-20. Sections 1, 2, 3 and 5 were approved on 2026-11-23 ("if all need fixing, fix all") and are applied.

## 1. asyncio samples read the envelope without checking it

`await endpoint.future()` returns a `PubNubAsyncioException` on error and does not raise (`pubnub/pubnub_asyncio.py`, `request_future`). A reader who copies these samples gets an `AttributeError` or wrong output instead of the error. The tests already check each envelope outside the markers (lint rule P1), so the tests are honest. The question is only what readers see.

Change: after the call, add the two lines the docs use elsewhere:

```python
if envelope.is_error():
    print(f"Error: {envelope.status.error_data}")
```

| File | Ids | Snippet ids |
| :--- | ---: | :--- |
| `asyncio/api_reference/test_access_manager.py` | 6 | `grant_token_builder`, `revoke_token`, `grant_token_categories`, `grant_token_multi`, `grant_token_regex`, `grant_token_multi_regex` |
| `asyncio/api_reference/test_access_manager_legacy.py` | 4 | `grant_token_spaces_builder`, `grant_token_spaces_multi`, `grant_token_spaces_regex`, `grant_token_spaces_multi_regex` |
| `asyncio/api_reference/test_access_manager_v2.py` | 5 | `grant_channel_all_users`, `grant_channel_ro_auth`, `grant_presence`, `grant_categories`, `grant_subkey_all` |
| `asyncio/api_reference/test_channel_groups.py` | 7 | `add_channels_builder`, `add_channels_named`, `list_channels_builder`, `list_channels_named`, `remove_channels_builder`, `remove_channels_named`, `delete_channel_group_builder` |
| `asyncio/api_reference/test_file_sharing.py` | 6 | `send_file_options`, `list_files_builder`, `get_file_url_builder`, `download_file_builder`, `delete_file_builder`, `publish_file_message_builder` |
| `asyncio/api_reference/test_message_actions.py` | 6 | `add_message_action_builder`, `add_message_action_named`, `get_message_actions_builder`, `get_message_actions_named`, `remove_message_action_builder`, `remove_message_action_named` |
| `asyncio/api_reference/test_message_persistence.py` | 12 | `fetch_history_builder`, `fetch_history_named`, `fetch_history_range`, `fetch_history_multiple`, `message_counts_builder`, `message_counts_named`, `message_counts_multiple_builder`, `message_counts_multiple_named`, `delete_messages_builder`, `delete_messages_named`, `delete_message_single_builder`, `delete_message_single_named` |
| `asyncio/api_reference/test_message_persistence_legacy.py` | 6 | `history_basic`, `history_reverse`, `history_start_reverse`, `history_end`, `history_include_timetoken`, `history_paging` |
| `asyncio/api_reference/test_misc.py` | 1 | `time_get` |
| `asyncio/api_reference/test_mobile_push.py` | 4 | `add_channels_to_push_kwargs`, `list_push_channels_builder`, `remove_channels_from_push_builder`, `remove_device_from_push_builder` |
| `asyncio/api_reference/test_presence.py` | 8 | `here_now_state`, `here_now_occupancy`, `here_now_groups`, `where_now_self`, `where_now_other`, `set_state_builder`, `get_state_builder`, `set_state_groups_builder` |
| `asyncio/api_reference/test_publish.py` | 6 | `publish_builder`, `publish_named`, `signal_message`, `fire_message`, `publish_store_post`, `fire_post` |
| `asyncio/api_reference/test_subscribe_legacy.py` | 1 | `subscribe_old_state` |

Total: 72 ids.

Status: applied, 2026-11-23, to 71 ids. A sample that binds two envelopes (`list_files_builder`, `publish_store_post` and the four asyncio push samples with an FCM and an APNs call) checks each of them. Exceptions:

* `subscribe_old_state` binds no envelope: the `set_state()` future runs inside `asyncio.ensure_future()` in the status callback. Unchanged.
* `history_paging` has the check and a `return` inside its recursive function. It stays in the lint allow-list `P1_PENDING`, because the envelope is a local of that function and no assertion after the end line can read it. The test compares the printed pages with an independent read, so an error (empty output) fails the test.

Follow-up, applied 2026-11-23: where lines after the check read the result, they now sit in an `else:` branch, so a reader's copy does not crash after it prints the error. 18 samples: `grant_token_categories`, `grant_token_spaces_builder`, `grant_categories`, `list_channels_builder`, `list_files_builder` (the second page call), `download_file_builder`, `add_message_action_builder`, `add_message_action_named`, `get_message_actions_builder`, `fetch_history_builder`, `fetch_history_named`, `fetch_history_multiple`, `message_counts_builder`, `message_counts_multiple_builder`, `time_get`, `list_push_channels_builder` (both envelopes), `fire_post`, plus the `return` in `history_paging`.

## 2. Samples that use a name defined outside the region

Readers see a name the sample never defines. The old suite defined it at module level, the port moved it to `shared/<page>.py`. The lint allows UPPER_CASE data constants of a shared module in a sample (rule M6), so this is not an error today.

| File | Snippet ids | Name | Proposed change |
| :--- | :--- | :--- | :--- |
| `sync/api_reference/test_mobile_push.py` | `add_channels_to_push_builder`, `add_channels_to_push_named`, `list_push_channels_builder`, `list_push_channels_named`, `remove_channels_from_push_builder`, `remove_channels_from_push_named`, `remove_device_from_push_builder`, `remove_device_from_push_named` | `APNS2_DEVICE` (random per run) | Use a literal 64 character hex token in the sample, as the JavaScript tier does (`DEVICE_TOKEN_EXAMPLE`), and list it in `support/resources.py` |
| `asyncio/api_reference/test_mobile_push.py` | `add_channels_to_push_builder`, `add_channels_to_push_kwargs`, `list_push_channels_builder`, `remove_channels_from_push_builder`, `remove_device_from_push_builder` | `APNS2_DEVICE` | Same |
| `asyncio/api_reference/test_file_sharing.py` | `send_file_builder`, `send_file_options` | `FIXTURE` | Open the file inside the sample (`with open("sample.gif", "rb") as file:`), with the path set on one hidden line |

Status: applied, 2026-11-23.

* Push: the samples show `5646e7e88187c402636cf1a838175a1c3f5ccdff69d071e68630a73ab1a4955a`. It is `APNS2_DEVICE` in `support/resources.py` and part of `PUSH_DEVICES`, so the janitor removes it on every gateway. `shared/mobile_push.py` imports it from there. Three sync named samples (`list_push_channels_named`, `remove_channels_from_push_named`, `remove_device_from_push_named`) now put one argument per line, because the literal made the aligned lines longer than 120 characters.
* Files: the samples keep their own name `fd` (`with open("sample.gif", "rb") as fd:`), so `.file_object(fd)` stays as it is. The path needs no hidden line: the test changes the working directory to `fixtures/` with `monkeypatch.chdir` outside the markers.
* Follow-up, applied 2026-11-23: the sync `send_file_builder` and `send_file_custom_message_type` open `"sample.gif"` instead of `file_path` (the test changes the working directory to `fixtures/`), and the sync `download_file_builder` sets `save_path = file_data['name']` itself (the test changes the working directory to a temporary folder). The asyncio `download_file_builder` sets `save_path = uploaded.name` in its `else` branch the same way (applied 2026-11-23).
* Imports, applied 2026-11-23: every sample now imports the SDK classes it shows (one `from ... import` line per module, first in the region or after the region's own imports). 41 samples got the line, in 18 more an import block that was hidden became visible. The scan compiled each visible region on its own and looked for unbound class names, so context values from the prose (`file_data`, `token`, `message_timetoken`, `tokens`, `config`) are not counted. Samples with several modules (for example `grant_token_multi_regex`, the crypto module samples, the membership samples) have one line per module. The asyncio `listeners_status` imports `SubscribeListener` from `pubnub.pubnub_asyncio`, not from `pubnub.pubnub` as its formerly hidden line did. `listeners_old_remove` still uses `MySubscribeCallback`, the class the previous sample on the page defines.

## 3. Compile-only samples that can run

| File | Snippet id | Today | Proposed change |
| :--- | :--- | :--- | :--- |
| `sync/api_reference/test_misc.py` | `reconnect_documented` | compile-only, reason "pubnub.reconnect() raises AttributeError" | No text change. PR 242 fixed `reconnect()` (plan D9), so a Phase 6 test can run it live |
| `sync/api_reference/test_subscribe_legacy.py` | `subscribe_old_logging` | compile-only, demo keys | One hidden line with `use_open_keys(pnconfig)` after the key lines, then a live test under `caplog` (plan decision for `subscribe_old_logging`) |
| `asyncio/api_reference/test_subscribe_legacy.py` | `subscribe_old_logging` | compile-only, demo keys, `await asyncio.sleep(500)` | Same, and a hidden shorter wait, or a visible wait of a few seconds |

Status: applied, 2026-11-23. `test_reconnect_documented` disconnects outside the markers, runs `pubnub.reconnect()` and checks the catch-up. Both `test_subscribe_old_logging` tests set the open keys on one hidden line, check the DEBUG records under `caplog` and the output of the stream handler, which writes to a buffer in place of `sys.stderr`. The asyncio sample waits `await asyncio.sleep(5)` (visible), and its test is a plain function, because the sample calls `asyncio.run()` itself. The coverage manifest has no compile-only entry left.

## 4. Noted, no change proposed

* `configuration_full` (both docsets) falls back to `'demo'` keys through `os.getenv(..., 'demo')`. The test sets the env variables first, so the fallback never runs.

## 5. The cipher mode sample crashes on the current SDK (found 2026-11-23)

The docs configuration page embeds the whole file `examples/crypto.py`, pinned to commit `5802f8a3`. Its middle part builds a client with `cipher_mode=AES.MODE_CBC` and no fallback, reads history that holds GCM messages and catches `UnicodeDecodeError`. Run live against the current SDK this raises `PubNubException: decryption error` instead, because commit `a078a9e` (security fixes for decryption paths, #235) wraps the decode error in `PubNubException` (`pubnub/crypto.py` line 48). So the published sample crashes where it should print `Unable to decode - Exception has been thrown`.

Change (two lines): add `from pubnub.exceptions import PubNubException` to the imports and catch `PubNubException` instead of `UnicodeDecodeError`. The tier test `sync/api_reference/test_encryption.py::test_cipher_mode_experiment` (snippet id `cipher_mode_experiment`) contains the corrected text and passes live. The docs embed in `configuration.md` stays pinned to the old file until this is approved. After approval the embed is repointed to the tier file with `snippets={['cipher_mode_experiment']}`.

Status: applied, 2026-11-23. The docs configuration page embeds `tests/live/sync/api_reference/test_encryption.py` with `snippets={['cipher_mode_experiment']}`.
