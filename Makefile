
MAKEFILE_PATH := $(abspath $(lastword $(MAKEFILE_LIST)))
CURRENT_DIR := $(patsubst %/,%,$(dir $(MAKEFILE_PATH)))

RTL_DIR := $(CURRENT_DIR)/rtl
MAKE ?= make
SIM ?= verilator 

.PHONY: rle
rle:
	$(MAKE) -C sim rle RTL_DIR=$(RTL_DIR) SIM=$(SIM)

.PHONY: clean
clean:
	$(MAKE) -C sim clean