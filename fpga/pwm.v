`default_nettype none

module pwm(
	input clk,
	input[9:0] duty_cycle,
	output pin
	);

parameter COUNTER_BITS = 10;

`ifndef SIM
defparam differential_output_b.PIN_TYPE = 6'b010000; // PIN_OUTPUT_DDR, PIN_INPUT_REGISTER
defparam differential_output_b.IO_STANDARD = "SB_LVCMOS" ;
SB_IO differential_output_b (
    .PACKAGE_PIN(pin),
    .LATCH_INPUT_VALUE (1'b1),
    .CLOCK_ENABLE (1'b1),
    .INPUT_CLK (clk),
    .OUTPUT_CLK (clk),
    .OUTPUT_ENABLE (1'b1),
    .D_OUT_0 (pwm_0_out), // Non-inverted
    .D_OUT_1 (pwm_1_out), // Non-inverted
);
`endif
reg pwm_0_out;
reg pwm_1_out;

reg pwm_0;
reg pwm_1;

reg [3:0] top;
reg [3:0] bottom;
reg carry;
reg bottom_e;
reg bottom_lt;
reg bottom_e1;
reg bottom_lt1;

reg top_e;
reg top_lt;

always @(posedge clk) begin
	pwm_0 <= 0;
	pwm_1 <= 0;
	pwm_0_out <= pwm_0;
	pwm_1_out <= pwm_1;

    {carry, bottom} <= {1'b0,bottom} - 1;

    top <= top - carry;
    bottom_e = bottom == duty_cycle[5:2];
    bottom_lt = bottom < duty_cycle[5:2];

    {bottom_e1, bottom_lt1} <= {bottom_e, bottom_lt};
    top_e = top == duty_cycle[9:6];
    top_lt = top < duty_cycle[9:6];

	if (top_lt || ( top_e && bottom_lt1 ))
	begin
		pwm_0 <= 1;
		pwm_1 <= 1;
	end 

	if (top_e && bottom_e1)
    begin
		pwm_0 <= duty_cycle[1];
	end 

end

endmodule
