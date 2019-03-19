#!/usr/bin/env bash

pip install -r requirements-dev.txt
if [[ $TRAVIS_PYTHON_VERSION == 2.7* ]]; then pip install -r requirements27-dev.txt; fi
if [[ $TRAVIS_PYTHON_VERSION == 3.4* ]]; then pip install -r requirements34-dev.txt; fi
if [[ $TRAVIS_PYTHON_VERSION == 3.5* ]]; then pip install -r requirements35-dev.txt; fi
if [[ $TRAVIS_PYTHON_VERSION == 3.6* ]]; then pip install -r requirements36-dev.txt; fi
if [[ $TRAVIS_PYTHON_VERSION == "nightly" ]]; then pip install -r requirements36-dev.txt; fi
if [[ $TRAVIS_PYTHON_VERSION == "pypy" ]]; then pip install -r requirements-pypy-dev.txt; fi
