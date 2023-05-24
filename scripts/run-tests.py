#!/usr/bin/env python
# Don't run tests from the root repo dir.
# We want to ensure we're importing from the installed
# binary package not from the CWD.

import os
from subprocess import check_call

_dname = os.path.dirname

REPO_ROOT = _dname(_dname(os.path.abspath(__file__)))
os.chdir(os.path.join(REPO_ROOT))

tcmn = 'py.test tests --cov=pubnub --ignore=tests/manual/'
fcmn = 'flake8 --exclude=scripts/,src/,.cache,.git,.idea,.tox,._trial_temp/,venv/ --ignore F811,E402'


def run(command):
    return check_call(command, shell=True)


run(tcmn)
# moved to separate action
# run(fcmn)
