"""API groups of the live tier. DATA ONLY. One group is one job of the "Live tests" workflow
(.github/workflows/live-integration.yml) and one `LIVE_GROUP=<name>` run:

    cd tests/live && LIVE_GROUP=messaging python -u -m pytest

`roles`: a group run without -k needs exactly these keyset roles up front, and the preflight and the wait for a closed
Access Manager grant cover only these roles. The workflow builds its job matrix from this list
(python -u tests/live/cli.py groups --matrix).

Every test file of the tier belongs to exactly one group. An entry is a file path relative to tests/live/, or a
"<file>::<test>" node id that takes one test out of the group that lists its file. `cli.py groups --check` (run by
`cli.py lint`) fails on a test file in no group or in two groups, a listed file or test that does not exist, a role a
file uses that its group does not list, and a workflow `group` input whose options differ from these names.

Order is the order of the serial run in CI. access-manager-application-level runs last: its tests open the whole
pam keyset for a moment.
"""

GROUPS = [
    {
        'name': 'messaging',
        'tier': 'docs',
        'roles': ['open'],
        'files': [
            'sync/api_reference/test_publish.py',
            'asyncio/api_reference/test_publish.py',
            'sync/api_reference/test_subscribe.py',
            'asyncio/api_reference/test_subscribe.py',
            'sync/api_reference/test_subscribe_legacy.py',
            'asyncio/api_reference/test_subscribe_legacy.py',
            'sync/api_reference/test_presence.py',
            'asyncio/api_reference/test_presence.py',
            'sync/api_reference/test_channel_groups.py',
            'asyncio/api_reference/test_channel_groups.py',
            'sync/api_reference/test_message_persistence.py',
            'asyncio/api_reference/test_message_persistence.py',
            'sync/api_reference/test_message_persistence_legacy.py',
            'asyncio/api_reference/test_message_persistence_legacy.py',
            'sync/api_reference/test_message_actions.py',
            'asyncio/api_reference/test_message_actions.py',
            'sync/api_reference/test_file_sharing.py',
            'asyncio/api_reference/test_file_sharing.py',
            'sync/api_reference/test_mobile_push.py',
            'asyncio/api_reference/test_mobile_push.py',
        ],
    },
    {
        'name': 'getting-started',
        'tier': 'docs',
        'roles': ['open', 'pam'],
        'files': [
            'sync/api_reference/test_configuration.py',
            'asyncio/api_reference/test_configuration.py',
            'sync/api_reference/test_encryption.py',
            'sync/api_reference/test_misc.py',
            'asyncio/api_reference/test_misc.py',
        ],
    },
    {
        'name': 'app-context',
        'tier': 'docs',
        'roles': ['open'],
        'files': [
            'sync/api_reference/test_objects.py',
        ],
    },
    {
        'name': 'access-manager',
        'tier': 'docs',
        'roles': ['open', 'pam'],
        'files': [
            'sync/api_reference/test_access_manager.py',
            'asyncio/api_reference/test_access_manager.py',
            'sync/api_reference/test_access_manager_legacy.py',
            'asyncio/api_reference/test_access_manager_legacy.py',
            'sync/api_reference/test_access_manager_v2.py',
            'asyncio/api_reference/test_access_manager_v2.py',
        ],
    },
    {
        'name': 'access-manager-application-level',
        'tier': 'docs',
        'roles': ['pam'],
        'files': [
            'sync/api_reference/test_access_manager_v2.py::test_grant_subkey_all',
            'asyncio/api_reference/test_access_manager_v2.py::test_grant_subkey_all',
        ],
    },
]
