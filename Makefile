.PHONY: init test lint

init:
	pip install -r requirements.txt

test:
	py.test python/tests/test_cg.py python/tests/test_history.py -vv

lint:
	flake8 . --count --exit-zero
