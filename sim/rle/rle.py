#!/usr/bin/env python
"""

Copyright (c) 2020 Alex Forencich
Update 2024 Roman Pustobaiev

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
THE SOFTWARE.

"""

import itertools
import logging
import os

import cocotb_test.simulator
import pytest

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge
from cocotb.regression import TestFactory

from cocotbext.axi import AxiStreamFrame, AxiStreamBus, AxiStreamSource, AxiStreamSink, AxiStreamMonitor


class TB:
    def __init__(self, dut):
        self.dut = dut

        self.log = logging.getLogger("cocotb.tb")
        self.log.setLevel(logging.DEBUG)

        cocotb.start_soon(Clock(dut.clk_i, 2, units="ns").start())

        self.source = AxiStreamSource(AxiStreamBus.from_prefix(dut, "s_axis"), dut.clk_i, dut.rst_i)
        self.sink = AxiStreamSink(AxiStreamBus.from_prefix(dut, "m_axis"), dut.clk_i, dut.rst_i)
        self.monitor = AxiStreamMonitor(AxiStreamBus.from_prefix(dut, "m_axis"), dut.clk_i, dut.rst_i)

    def set_idle_generator(self, generator=None):
        if generator:
            self.source.set_pause_generator(generator())

    def set_backpressure_generator(self, generator=None):
        if generator:
            self.sink.set_pause_generator(generator())

    async def reset(self):
        self.dut.rst_i.setimmediatevalue(0)
        await RisingEdge(self.dut.clk_i)
        await RisingEdge(self.dut.clk_i)
        self.dut.rst_i.value = 1
        await RisingEdge(self.dut.clk_i)
        await RisingEdge(self.dut.clk_i)
        self.dut.rst_i.value = 0
        await RisingEdge(self.dut.clk_i)
        await RisingEdge(self.dut.clk_i)


async def run_test(dut, payload_lengths=None, payload_data=None, idle_inserter=None, backpressure_inserter=None):

    tb = TB(dut)

    id_count = 2**len(tb.source.bus.tid)

    cur_id = 1

    await tb.reset()

    tb.set_idle_generator(idle_inserter)
    tb.set_backpressure_generator(backpressure_inserter)

    test_frames = []

    for test_data in [payload_data(x) for x in payload_lengths()]:
        test_frame = AxiStreamFrame(test_data)
        test_frame.tid = cur_id
        test_frame.tdest = cur_id
        await tb.source.send(test_frame)

        test_frames.append(test_frame)

        cur_id = (cur_id + 1) % id_count

    for test_frame in test_frames:
        rx_frame = await tb.sink.recv()

        assert rx_frame.tdata == test_frame.tdata
        assert rx_frame.tid == test_frame.tid
        assert rx_frame.tdest == test_frame.tdest
        assert not rx_frame.tuser

        mon_rx_frame = await tb.monitor.recv()

        assert mon_rx_frame.tdata == test_frame.tdata
        assert mon_rx_frame.tid == test_frame.tid
        assert mon_rx_frame.tdest == test_frame.tdest
        assert not mon_rx_frame.tuser

        assert rx_frame.sim_time_start == mon_rx_frame.sim_time_start
        assert rx_frame.sim_time_end == mon_rx_frame.sim_time_end

    assert tb.sink.empty()
    assert tb.monitor.empty()

    await RisingEdge(dut.clk_i)
    await RisingEdge(dut.clk_i)


def cycle_pause():
    return itertools.cycle([1, 1, 1, 0])


def size_list():
    data_width = len(cocotb.top.s_axis_tdata)
    byte_width = data_width // 8
    return list(range(1, byte_width*4+1)) + [512] + [1]*64


def incrementing_payload(length):
    return bytearray(itertools.islice(itertools.cycle(range(256)), length))


if cocotb.SIM_NAME:

    factory = TestFactory(run_test)
    factory.add_option("payload_lengths", [size_list])
    factory.add_option("payload_data", [incrementing_payload])
    factory.add_option("idle_inserter", [None, cycle_pause])
    factory.add_option("backpressure_inserter", [None, cycle_pause])
    factory.generate_tests()
