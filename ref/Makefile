MAKEFILE_PATH := $(abspath $(lastword $(MAKEFILE_LIST)))
CURRENT_DIR := $(patsubst %/,%,$(dir $(MAKEFILE_PATH)))
ASSETS_DIR := $(CURRENT_DIR)/../assets
PYTHON ?= python3

IMAGE += cat

.PHONY: all
all:
	$(PYTHON) $(CURRENT_DIR)/decoder.py $(ASSETS_DIR)/$(IMAGE).jpg $(IMAGE).bmp
	@diff $(IMAGE).bmp $(ASSETS_DIR)/$(IMAGE).ref.bmp
