#!/usr/bin/env bash

pip install -r requirements.txt
if [[ $TRAVIS_PYTHON_VERSION == 2.6 ]]; then pip install -r requirements26.txt; fi
if [[ $TRAVIS_PYTHON_VERSION == 2.7 ]]; then pip install twisted pyopenssl; fi