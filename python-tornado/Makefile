include ../Makefile.inc


.PHONY: all
all: build

.PHONY: build
build:
	cat ../common/LICENSE_HEADER > ./Pubnub.py
	echo "\n" >> ./Pubnub.py
	cat ../common/PubnubCrypto.py >> ./Pubnub.py
	echo "\n" >> ./Pubnub.py
	cat ../common/PubnubBase.py >> ./Pubnub.py
	echo "\n" >> ./Pubnub.py
	cat ../common/PubnubCoreAsync.py >> ./Pubnub.py
	echo "\n" >> ./Pubnub.py
	cat ./unassembled/Platform.py >> ./Pubnub.py
	find -name "Pubnub*py" | xargs sed -i "s/PubNub\ [0-9]\.[0-9]\.[0-9]/PubNub\ $(VERSION)/g"


.PHONY: clean
clean:
	rm -f Pubnub.py*

.PHONY: test
test:
	python tests/unit-tests.py

