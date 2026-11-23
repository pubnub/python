import os

import pytest

# The live tier (tests/live/) has its own pytest.ini and needs keys and the real service. The root run never collects
# it (scripts/run-tests.py also passes --ignore=tests/live/).
collect_ignore = ["live"]

# Offline guard (live tier plan, Phase 1). PN_OFFLINE_GUARD=1 refuses every connection that is not to the loopback
# address, through pytest-socket (requirements-dev.txt). A test that reaches the real network then fails with
# SocketConnectBlockedError. It is opt-in until the tests that need the network move to the endpoint tier
# (plan Phase 7), then it becomes the default. Same effect: py.test tests --allow-hosts=127.0.0.1,::1
_OFFLINE = os.environ.get("PN_OFFLINE_GUARD") == "1"


def pytest_collection_modifyitems(config, items):
    if not _OFFLINE:
        return
    if not config.pluginmanager.hasplugin("socket"):
        raise pytest.UsageError("PN_OFFLINE_GUARD=1 needs pytest-socket (pip install -r requirements-dev.txt)")
    for item in items:
        item.add_marker(pytest.mark.allow_hosts(["127.0.0.1", "::1"]))


@pytest.fixture()
def file_upload_test_data():
    return {
        "UPLOADED_FILENAME": "king_arthur.txt",
        "FILE_CONTENT": "Knights who say Ni!"
    }


@pytest.fixture
def file_for_upload(tmpdir, file_upload_test_data):
    temp_file = tmpdir.mkdir("fixutre").join(file_upload_test_data["UPLOADED_FILENAME"])
    temp_file.write(file_upload_test_data["FILE_CONTENT"])
    return temp_file


@pytest.fixture
def file_for_upload_10mb_size(tmpdir):
    temp_file = tmpdir.mkdir("fixutre").join("file_5mb")
    temp_file.write('0' * 10 * 1024 * 1024)
    return temp_file
