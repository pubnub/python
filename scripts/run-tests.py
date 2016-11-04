#!/usr/bin/env python
# Don't run tests from the root repo dir.
# We want to ensure we're importing from the installed
# binary package not from the CWD.

import os
from subprocess import check_call

_dname = os.path.dirname

REPO_ROOT = _dname(_dname(os.path.abspath(__file__)))
os.chdir(os.path.join(REPO_ROOT))

pyenv_version = os.getenv('PYENV_VERSION', 0)
travis_version = os.getenv('TRAVIS_PYTHON_VERSION', 0)
version = str(travis_version or pyenv_version)
tcmn = 'py.test tests --cov-report=xml --cov=./pubnub '
fcmn = 'flake8 --exclude=src/,.cache,.git,.idea,.tox,._trial_temp/'


print("Version is", version)


def run(command):
    return check_call(command, shell=True)


if version.startswith('2.6'):
    run(
        '%s--ignore=tests/integrational/tornado/ --ignore=tests/integrational/twisted/ --ignore=tests/integrational/asyncio/ --ignore=tests/integrational/python_v35/' % tcmn)  # noqa: E501
elif version.startswith('2.7') or version.startswith('anaconda2'):
    run("%s,*asyncio*,*python_v35*,examples/" % fcmn)
    run('%s --ignore=tests/integrational/asyncio/ --ignore=tests/integrational/python_v35/' % tcmn)
elif version.startswith('3.3'):
    run("%s,*asyncio*,*python_v35*" % fcmn)
    run('%s--ignore=tests/integrational/asyncio/ --ignore=tests/integrational/python_v35/' % tcmn)
elif version.startswith('3.4'):
    run("%s,*python_v35*,examples" % fcmn)
    run('%s--ignore=tests/integrational/python_v35/ ' % tcmn)
elif version.startswith('3.5'):
    run(fcmn)
    run(tcmn)
elif version.startswith('3.6') or version == 'nightly':
    run(fcmn)
    run(tcmn)
elif version.startswith('pypy'):
    run("%s,*asyncio*,*python_v35*,examples" % fcmn)
    run('%s--ignore=tests/integrational/asyncio/ --ignore=tests/integrational/python_v35/' % tcmn)
else:
    raise Exception("Version %s is not supported by this script runner" % version)
