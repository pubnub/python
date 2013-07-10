include ../Makefile.inc


.PHONY: all
all: build

.PHONY: build
build:
	find -name "Pubnub*py" | xargs sed -i "s/PubNub\ [0-9]\.[0-9]\.[0-9]/PubNub\ $(VERSION)/g"


.PHONY: clean
clean:

.PHONY: test
test:
	python tests/detailed-history-unit-test.py
	python tests/unit-test.py

