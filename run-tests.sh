#!/bin/bash
set -ev

nosetests python/tests/test_cg.py
nosetests python/tests/test_grant.py
nosetests python/tests/test_history.py

if [[ $TRAVIS_PYTHON_VERSION == 2.7 ]]; then
  python python-twisted/tests/test_publish_async.py
  python python-twisted/tests/test_grant_async.py
  python python-tornado/tests/test_grant_async.py
  flake8 --ignore=E501,E265,E266,E712 python-twisted/
fi

flake8 --ignore=E501,E265,E266,E712 python/ python-tornado/ pubnub.py
