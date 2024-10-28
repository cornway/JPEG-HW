`resetall
`timescale 1ns / 1ps
`default_nettype none

/*
 * AXI4-Stream register
 */
module rle #
(
    // Width of AXI stream interfaces in bits
    parameter int unsigned AXIS_DATA_WIDTH = 8,
    // Propagate tkeep signal
    parameter int unsigned AXIS_KEEP_ENABLE = (AXIS_DATA_WIDTH>8),
    // tkeep signal width (words per cycle)
    parameter int unsigned AXIS_KEEP_WIDTH = ((AXIS_DATA_WIDTH+7)/8),
    // Propagate tlast signal
    parameter int unsigned AXIS_LAST_ENABLE = 1,
    // Propagate tid signal
    parameter int unsigned AXIS_ID_ENABLE = 0,
    // tid signal width
    parameter int unsigned AXIS_ID_WIDTH = 8,
    // Propagate tdest signal
    parameter int unsigned AXIS_DEST_ENABLE = 0,
    // tdest signal width
    parameter int unsigned AXIS_DEST_WIDTH = 8,
    // Propagate tuser signal
    parameter int unsigned AXIS_USER_ENABLE = 1,
    // tuser signal width
    parameter int unsigned AXIS_USER_WIDTH = 1
) (
    input  logic                   clk_i,
    input  logic                   rst_i,

    /*
     * AXI Stream input
     */
    input  logic [AXIS_DATA_WIDTH-1:0]  s_axis_tdata,
    input  logic [AXIS_KEEP_WIDTH-1:0]  s_axis_tkeep,
    input  logic                        s_axis_tvalid,
    output logic                        s_axis_tready,
    input  logic                        s_axis_tlast,
    input  logic [AXIS_ID_WIDTH-1:0]    s_axis_tid,
    input  logic [AXIS_DEST_WIDTH-1:0]  s_axis_tdest,
    input  logic [AXIS_USER_WIDTH-1:0]  s_axis_tuser,

    /*
     * AXI Stream output
     */
    output logic [AXIS_DATA_WIDTH-1:0]  m_axis_tdata,
    output logic [AXIS_KEEP_WIDTH-1:0]  m_axis_tkeep,
    output logic                        m_axis_tvalid,
    input  logic                        m_axis_tready,
    output logic                        m_axis_tlast,
    output logic [AXIS_ID_WIDTH-1:0]    m_axis_tid,
    output logic [AXIS_DEST_WIDTH-1:0]  m_axis_tdest,
    output logic [AXIS_USER_WIDTH-1:0]  m_axis_tuser
);

    assign m_axis_tdata  = s_axis_tdata;
    assign m_axis_tkeep  = AXIS_KEEP_ENABLE ? s_axis_tkeep : {AXIS_KEEP_WIDTH{1'b1}};
    assign m_axis_tvalid = s_axis_tvalid;
    assign m_axis_tlast  = AXIS_LAST_ENABLE ? s_axis_tlast : 1'b1;
    assign m_axis_tid    = AXIS_ID_ENABLE   ? s_axis_tid   : {AXIS_ID_WIDTH{1'b0}};
    assign m_axis_tdest  = AXIS_DEST_ENABLE ? s_axis_tdest : {AXIS_DEST_WIDTH{1'b0}};
    assign m_axis_tuser  = AXIS_USER_ENABLE ? s_axis_tuser : {AXIS_USER_WIDTH{1'b0}};

    assign s_axis_tready = m_axis_tready;

    initial begin
        $dumpfile("dump.vcd");
        $dumpvars();
    end

endmodule