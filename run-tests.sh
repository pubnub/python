nosetests python/tests/test_cg.py
nosetests python/tests/test_grant.py
nosetests python/tests/test_history.py

if ! [[ $TRAVIS_PYTHON_VERSION == 2.6 ]]; then
  python python-twisted/tests/test_publish_async.py
  python python-twisted/tests/test_grant_async.py
fi

flake8 --ignore=E501,E265,E266,E712 python/ python-twisted/ python-tornado/ \
  pubnub.py

