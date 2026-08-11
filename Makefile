# by default install in the opt subdirectory of this one
ROOT := $(dir $(abspath $(lastword $(MAKEFILE_LIST))))
PREFIX ?= $(ROOT)opt

PROGRAMS := $(wildcard $(ROOT)/src/programs/*.py)
INSTALLED_PROGRAMS := $(patsubst $(ROOT)/src/programs/%.py,$(PREFIX)/bin/%,$(PROGRAMS))
INSTALLED_METADATA := $(patsubst $(ROOT)/src/programs/%.py,$(PREFIX)/ymmsl/ttb_example/programs/%.ymmsl,$(PROGRAMS))

MODELS := $(wildcard $(ROOT)/src/ymmsl/ttb_example/*.ymmsl)
INSTALLED_MODELS := $(subst $(ROOT)/src/ymmsl/ttb_example,$(PREFIX)/ymmsl/ttb_example,$(MODELS))


install_all: $(PREFIX)/venv $(INSTALLED_PROGRAMS) $(INSTALLED_METADATA) $(INSTALLED_MODELS) message


$(PREFIX)/venv:
	python3 -m venv $@
	. $@/bin/activate && python3 -m pip install -r $(ROOT)/requirements.txt


$(PREFIX)/ymmsl:
	mkdir -p $@/ttb_example/programs


$(PREFIX)/bin:
	mkdir -p $@


# install executables
$(PREFIX)/bin/%: $(ROOT)src/programs/%.py $(ROOT)src/programs/%.ymmsl.in | $(PREFIX)/bin
	cp $< $@


# install executable ymmsl metadata
$(PREFIX)/ymmsl/ttb_example/programs/%: $(ROOT)src/programs/%.in | $(PREFIX)/ymmsl
	sed -e 's^PREFIX^$(PREFIX)/bin^g' <$< >$@


# install models
$(PREFIX)/ymmsl/ttb_example/%.ymmsl: $(ROOT)src/ymmsl/ttb_example/%.ymmsl | $(PREFIX)/ymmsl
	cp $< $@


.PHONY: message
message:
	@echo
	@echo "Installed into $(PREFIX)"
	@echo
	@echo "Next:"
	@echo
	@echo "- activate the virtual environment:"
	@echo "    . $(PREFIX)/venv/bin/activate"
	@echo
	@echo "- set YMMSL_PATH:"
	@echo "    export YMMSL_PATH=$(PREFIX)/ymmsl"
	@echo
	@echo "and then create a configuration and run it as described in README.md"


.PHONY: clean
clean:
	rm -rf $(PREFIX)/venv $(PREFIX)/bin $(PREFIX)/ymmsl

