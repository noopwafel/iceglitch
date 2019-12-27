QUIET ?= -q
ECP5 ?= 0
ICE40 ?= 0
ifeq ($(ECP5), 1)
  FPGA_TYPE ?= um5g-85k
  LPF ?= ecp5evn.lpf
  NEXTPNR_FLAGS ?=
  YOSYS_FLAGS ?= -DECP5=1
else
  ifeq ($(ICE40), 1)
    FPGA_TYPE ?= hx8k
    PCF ?= ice40breakout.pcf
    NEXTPNR_FLAGS ?= --opt-timing -r
    YOSYS_FLAGS ?=
  else
    FPGA_TYPE ?= hx1k --package tq144
    PCF ?= icestick.pcf
    NEXTPNR_FLAGS ?= --opt-timing -r
    YOSYS_FLAGS ?=
  endif
endif

glitcher: upload-glitcher 

upload-glitcher: glitcher.bin
	sudo iceprog glitcher.bin

iverilog:
	iverilog -DSIM top.v -o iverilog.out

glitcher.bin: glitcher.txt
ifeq ($(ECP5), 1)
	ecppack --svf-rowsize 100000 --svf attosoc.svf glitcher.txt glitcher.bin
else
	icepack glitcher.txt glitcher.bin
endif

glitcher.rpt: glitcher.txt
	icetime -d $(FPGA_TYPE) -mtr glitcher.rpt glitcher.txt

glitcher.txt: glitcher.json
ifeq ($(ECP5), 1)
	nextpnr-ecp5 $(QUIET) $(NEXTPNR_FLAGS) --pre-pack ecp5_clock.py --$(FPGA_TYPE) --lpf $(LPF) --textcfg glitcher.txt --json glitcher.json --log nextpnr.log && grep --color -i freq nextpnr.log
else
	until nextpnr-ice40 $(QUIET) $(NEXTPNR_FLAGS) --pre-pack ice40_clock.py --$(FPGA_TYPE) --pcf $(PCF) --asc glitcher.txt --json glitcher.json --log nextpnr.log && grep --color -i freq nextpnr.log ; do rm glitcher.txt ; done
endif

glitcher.json: top.v
ifeq ($(ECP5), 1)
	yosys $(QUIET) -E top.deps -p "read_verilog $(YOSYS_FLAGS) top.v; synth_ecp5 -json glitcher.json" | tee yosys.log
else
	yosys $(QUIET) -E top.deps -p "read_verilog $(YOSYS_FLAGS) top.v; synth_ice40 -json glitcher.json" | tee yosys.log
endif

clean:
	rm -f glitcher.bin glitcher.json glitcher.txt glitcher.pcf top.deps yosys.log nextpnr.log iverilog.out glitcher.rpt

-include top.deps
