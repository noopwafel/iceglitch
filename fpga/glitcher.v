`default_nettype none

`include "counter_pipelined.v"

module glitcher(
    input clk,
    input ddr_clk,
    input trigger,
    input slow_armed,
    output reg armed_ack,
    output reg done,
    input slow_done_ack,
    input [31:0] delay_in,
    input [31:0] length_in,
    output digital_glitch,
    input terminate_slow,
    output reg [3:0] clk_delay,
    input [3:0] clk_delay_target
    );

parameter COUNTER_BITS = 32;

reg setDelay,setLength;
wire delayIsZero,lengthIsZero;

counter delayCounter(clk,delay_in[COUNTER_BITS-1:1],setDelay,delayIsZero);
counter glitchCounter(clk,length_in[COUNTER_BITS-1:2],setLength,lengthIsZero);

parameter GLITCH_OFF = 0;
parameter GLITCH_TRIG_LOW = 1;
parameter GLITCH_WAIT = 2;
parameter GLITCH_GLITCH = 3;
parameter GLITCH_TRIG_HIGH = 4;

reg [2:0] state;

reg [3:0] clk_delay_tmp;
reg [3:0] clk_delay_tmp2;
reg [3:0] clk_delay_tmp3;

reg trigger_ff;

reg armed, armed_tmp;
reg done_ack, done_ack_tmp;
reg terminate,terminate_tmp;
reg done_tmp;

`ifndef SIM
// ddr details: http://www.latticesemi.com/view_document?document_id=47960
defparam differential_output_b.PIN_TYPE = 6'b010000; // PIN_OUTPUT_DDR, PIN_INPUT_REGISTER
defparam differential_output_b.IO_STANDARD = "SB_LVCMOS" ;
SB_IO differential_output_b (
    .PACKAGE_PIN(digital_glitch),
    .LATCH_INPUT_VALUE (1'b1),
    .CLOCK_ENABLE (1'b1),
    .INPUT_CLK (ddr_clk),
    .OUTPUT_CLK (ddr_clk),
    .OUTPUT_ENABLE (1'b1),
    .D_OUT_0 (glitch_out_0_out), // Non-inverted
    .D_OUT_1 (glitch_out_1_out), // Non-inverted
); /* synthesis DRIVE_STRENGTH= x2 */
`endif

reg glitch_out_0;
reg glitch_out_1;
reg glitch_out_0_out;
reg glitch_out_1_out;

always @(posedge clk) begin
	trigger_ff <= trigger;
	{armed_ack, armed, armed_tmp} <= {armed, armed_tmp, slow_armed};
	{terminate,terminate_tmp} <= {terminate_tmp,terminate_slow};
	{done_ack, done_ack_tmp} <= {done_ack_tmp, slow_done_ack};
	{done} <= {done_tmp};


`ifndef SIM
	glitch_out_0_out <= glitch_out_0;
	glitch_out_1_out <= glitch_out_1;
`endif

    clk_delay <= clk_delay_tmp3;
    clk_delay_tmp3 <= clk_delay_tmp2;
    clk_delay_tmp2 <= clk_delay_tmp;

	if (done_ack)
		done_tmp <= 0;

	glitch_out_0 <= 0;//Default glitch is off
	glitch_out_1 <= 0;

	setDelay <= 1;
	setLength <= 1;
	case (state)
	GLITCH_OFF:
	begin
        clk_delay_tmp <=4'h0;
		if (armed) begin
			state <= GLITCH_TRIG_LOW;
		end
	end
	GLITCH_TRIG_LOW:
	begin
		if (trigger_ff==0) begin
			state <= GLITCH_TRIG_HIGH;
		end

		if (terminate) begin
			state <= GLITCH_OFF;
			done_tmp <= 1;
		end
	end
	GLITCH_TRIG_HIGH:
	begin
		if (trigger_ff==1) begin
			setDelay <= 0;
			state <= GLITCH_WAIT;
		end 

		if (terminate) begin
			state <= GLITCH_OFF;
			done_tmp <= 1;
		end
	end
	GLITCH_WAIT:
	begin
		setDelay <= 0;
		if (delayIsZero ) begin
			glitch_out_0 <= delay_in[0];
			setLength <= 0;

			state <= GLITCH_GLITCH;
            clk_delay_tmp <= clk_delay_target;
		end
	end
	GLITCH_GLITCH:
	begin
		setLength <= 0;
		glitch_out_1 <= 1;//Set normal glitch high
		glitch_out_0 <= 1;
		if (lengthIsZero) begin
			glitch_out_0 <= length_in[1]; //DDR glitch
			glitch_out_1 <= length_in[0]; //DDR glitch, should be one normally unless phase inverted
			state <= GLITCH_OFF;
			done_tmp <= 1;
		end
	end
	endcase
end

endmodule
