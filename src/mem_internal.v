// SPDX-FileCopyrightText: © 2021-2024 Uri Shaked <uri@wokwi.com>
// SPDX-License-Identifier: MIT

`default_nettype none

module spell_mem_internal (
    input wire rst_n,
    input wire clk,
    input wire select,
    input wire [7:0] addr,
    input wire [7:0] data_in,
    input wire memory_type_data,
    input wire write,
    output wire [7:0] data_out,
    output reg data_ready
);

  // Initialize code mem to 0xff, data mem to 0x00
  reg mem_initialized;
  reg [8:0] mem_init_addr;
  wire [7:0] mem_init_data = mem_init_addr < 9'd256 ? 8'hff : 8'h00;

  RM_IHPSG13_1P_1024x8_c2_bm_bist sram (
      .A_CLK(clk),
      .A_MEN(rst_n),
      .A_WEN((select && write) || (rst_n && ~mem_initialized)),
      .A_REN(select),
      .A_ADDR(mem_initialized ? {1'b0, memory_type_data, addr} : mem_init_addr),
      .A_DIN(mem_initialized ? data_in : mem_init_data),
      .A_DLY(1'b1),
      .A_DOUT(data_out),
      .A_BM(8'b11111111),
      .A_BIST_CLK(1'b0),
      .A_BIST_EN(1'b0),
      .A_BIST_MEN(1'b0),
      .A_BIST_WEN(1'b0),
      .A_BIST_REN(1'b0),
      .A_BIST_ADDR(10'b0),
      .A_BIST_DIN(8'b0),
      .A_BIST_BM(8'b0)
  );

  always @(posedge clk) begin
    if (~rst_n) begin
      data_ready <= 1'b0;
      mem_initialized <= 1'b0;
      mem_init_addr <= 9'd0;
    end else begin
      if (!mem_initialized) begin
        mem_init_addr <= mem_init_addr + 1;
        if (mem_init_addr == 9'd511) begin
          mem_initialized <= 1'b1;
        end
      end else begin
        data_ready <= select;
      end
    end
  end

endmodule
