SHELL := /bin/bash
.DEFAULT_GOAL := help

.PHONY: help
help:
		@mh -f $(MAKEFILE_LIST) $(target) || echo "Please install mh from https://github.com/oz123/mh/releases/latest"
ifndef target
	@(which mh > /dev/null 2>&1 && echo -e "\nUse \`make help target=foo\` to learn more about foo.")
endif

	
.PHONY: build-sdist
build-sdist:  ## Build source distribution
	python3 -m build -s

.PHONY: build-wheel
build-wheel:  ## Build wheel distribution (and source distribution)
	python3 -m build -w

build-clean:  ## Clean build artifacts
	rm -rf dist

