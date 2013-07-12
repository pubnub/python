SUBDIRS = common python python-twisted python-tornado

.PHONY: all test
all test: $(SUBDIRS)

all: TARG=all
test: TARG=test

$(SUBDIRS): force
	@ $(MAKE) -C $@ $(TARG)

.PHONY: force
force :;
