`resetall
`timescale 1ns / 1ps
`default_nettype none

/*
 * AXI4-Stream register
 */
module rle #
(
    // Width of AXI stream interfaces in bits
    parameter AXIS_DATA_WIDTH = 8,
    // Propagate tkeep signal
    parameter AXIS_KEEP_ENABLE = (AXIS_DATA_WIDTH>8),
    // tkeep signal width (words per cycle)
    parameter AXIS_KEEP_WIDTH = ((AXIS_DATA_WIDTH+7)/8),
    // Propagate tlast signal
    parameter AXIS_LAST_ENABLE = 1,
    // Propagate tid signal
    parameter AXIS_ID_ENABLE = 1,
    // tid signal width
    parameter AXIS_ID_WIDTH = 8,
    // Propagate tdest signal
    parameter AXIS_DEST_ENABLE = 1,
    // tdest signal width
    parameter AXIS_DEST_WIDTH = 8,
    // Propagate tuser signal
    parameter AXIS_USER_ENABLE = 1,
    // tuser signal width
    parameter AXIS_USER_WIDTH = 1
) (
    input  wire                   clk_i,
    input  wire                   rst_i,

    /*
     * AXI Stream input
     */
    input  wire [AXIS_DATA_WIDTH-1:0]  s_axis_tdata,
    input  wire [AXIS_KEEP_WIDTH-1:0]  s_axis_tkeep,
    input  wire                        s_axis_tvalid,
    output wire                        s_axis_tready,
    input  wire                        s_axis_tlast,
    input  wire [AXIS_ID_WIDTH-1:0]    s_axis_tid,
    input  wire [AXIS_DEST_WIDTH-1:0]  s_axis_tdest,
    input  wire [AXIS_USER_WIDTH-1:0]  s_axis_tuser,

    /*
     * AXI Stream output
     */
    output wire [AXIS_DATA_WIDTH-1:0]  m_axis_tdata,
    output wire [AXIS_KEEP_WIDTH-1:0]  m_axis_tkeep,
    output wire                        m_axis_tvalid,
    input  wire                        m_axis_tready,
    output wire                        m_axis_tlast,
    output wire [AXIS_ID_WIDTH-1:0]    m_axis_tid,
    output wire [AXIS_DEST_WIDTH-1:0]  m_axis_tdest,
    output wire [AXIS_USER_WIDTH-1:0]  m_axis_tuser
);

    assign m_axis_tdata  = s_axis_tdata;
    assign m_axis_tkeep  = AXIS_KEEP_ENABLE ? s_axis_tkeep : {AXIS_KEEP_WIDTH{1'b1}};
    assign m_axis_tvalid = s_axis_tvalid;
    assign m_axis_tlast  = AXIS_LAST_ENABLE ? s_axis_tlast : 1'b1;
    assign m_axis_tid    = AXIS_ID_ENABLE   ? s_axis_tid   : {AXIS_ID_WIDTH{1'b0}};
    assign m_axis_tdest  = AXIS_DEST_ENABLE ? s_axis_tdest : {AXIS_DEST_WIDTH{1'b0}};
    assign m_axis_tuser  = AXIS_USER_ENABLE ? s_axis_tuser : {AXIS_USER_WIDTH{1'b0}};

    assign s_axis_tready = m_axis_tready;

endmodule