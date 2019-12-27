`default_nettype none

module fifo (
	input clk,
	input [7:0] in,
	output reg [7:0] out,
	output reg available,
	input add,
	input get,
);

reg [2:0] writeIdx;
reg [2:0] readIdx;

reg [7:0] buff [7:0];


always @(posedge clk) begin
	//Always write registers, to from the regs, whether they are valid is
	//decided by the read/write Idx's
	buff[writeIdx] <= in;
	out <= buff[readIdx];

	//
	available <= writeIdx != readIdx;

	writeIdx <= writeIdx + add;
	readIdx <= readIdx + get;
end

endmodule
