SIM ?= icarus
WAVES ?= 1
TOPLEVEL_LANG ?= verilog
RTL_DIR ?=
TOP := rle

VERILOG_SOURCES += $(RTL_DIR)/$(TOP).v

# TOPLEVEL is the name of the toplevel module in your Verilog or VHDL file
TOPLEVEL = $(TOP)

# MODULE is the basename of the Python test file
MODULE = $(TOP)

export PARAM_AXIS_DATA_WIDTH := 32
export PARAM_AXIS_KEEP_WIDTH := $(shell expr $(PARAM_AXIS_DATA_WIDTH) / 8 )
export PARAM_AXIS_ID_WIDTH := 8
export PARAM_AXIS_DEST_WIDTH := 8
export PARAM_AXIS_USER_WIDTH := 1

PLUSARGS += -fst

COMPILE_ARGS += $(foreach v,$(filter PARAM_%,$(.VARIABLES)),-P $(TOPLEVEL).$(subst PARAM_,,$(v))=$($(v)))

ifeq ($(WAVES),1)
	VERILOG_SOURCES += iverilog_dump.v
	COMPILE_ARGS += -s iverilog_dump
endif

# include cocotb's make rules to take care of the simulator setup
include $(shell cocotb-config --makefiles)/Makefile.sim

iverilog_dump.v:
	echo 'module iverilog_dump();' > $@
	echo 'initial begin' >> $@
	echo '    $$dumpfile("$(TOPLEVEL).fst");' >> $@
	echo '    $$dumpvars(0, $(TOPLEVEL));' >> $@
	echo 'end' >> $@
	echo 'endmodule' >> $@

clean::
	@rm -rf iverilog_dump.v
	@rm -rf dump.fst $(TOPLEVEL).fst