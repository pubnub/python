#!/usr/bin/env python
# Don't run tests from the root repo dir.
# We want to ensure we're importing from the installed
# binary package not from the CWD.

import os
import sys
from subprocess import check_call

_dname = os.path.dirname

REPO_ROOT = _dname(_dname(os.path.abspath(__file__)))
os.chdir(os.path.join(REPO_ROOT))

try:
    version = str(sys.version_info.major) + "." + str(sys.version_info.minor)
except:
    version = str(sys.version_info[0]) + "." + str(sys.version_info[1])

tcmn = 'py.test tests --cov-report=xml --cov=./pubnub --ignore=tests/manual/ '
fcmn = 'flake8 --exclude=scripts/,src/,.cache,.git,.idea,.tox,._trial_temp/'


print("Version is", version)


def run(command):
    return check_call(command, shell=True)

if version.startswith('2.7') or version.startswith('anaconda2'):
    run("%s,*asyncio*,*python_v35*,examples/" % fcmn)
    run('%s --ignore=tests/integrational/asyncio/ --ignore=tests/integrational/twisted/ --ignore=tests/integrational/python_v35/' % tcmn)
elif version.startswith('3.4'):
    run("%s,*python_v35*,examples" % fcmn)
    run('%s--ignore=tests/integrational/python_v35/ --ignore=tests/integrational/twisted/' % tcmn)
elif version.startswith('3.5'):
    run(fcmn)
    run('%s--ignore=tests/integrational/twisted/' % tcmn)
elif version.startswith('3.6') or version == 'nightly':
    run(fcmn)
    run('%s--ignore=tests/integrational/twisted/' % tcmn)
elif version.startswith('pypy'):
    run("%s,*asyncio*,*python_v35*,examples" % fcmn)
    run('%s--ignore=tests/integrational/asyncio/ --ignore=tests/integrational/twisted/ --ignore=tests/integrational/python_v35/' % tcmn)
else:
    raise Exception("Version %s is not supported by this script runner" % version)
