`default_nettype none
`include "uart.v"
`include "glitcher.v"
`include "pwm.v"

module top (
    input clk,
    input trigger_in,
    output switch_out,
    output reg gpio_0,
    output reg gpio_1,
    input RX,
    output TX,
    output LED1,
    output LED2,
    output LED3,
    output LED4,
    output LED5,
    output PWM1,
    output PWM2
);

wire [3:0] clk_delay;
reg [3:0] clk_delay_target = 4'hf;

wire clk_fast, clk_fast_faster;

`ifdef SIM
assign clk_fast = clk;
assign clk_fast_faster = clk;
`else
`ifndef INTERNAL_OSC
SB_PLL40_2F_CORE #(
		.FEEDBACK_PATH("SIMPLE"),
        .DELAY_ADJUSTMENT_MODE_RELATIVE("DYNAMIC"),
        .DELAY_ADJUSTMENT_MODE_FEEDBACK("DYNAMIC"), //Don't touch
		.DIVR(4'b0000),		// DIVR =  0
		.DIVF(7'b0111001),	// DIVF = 82
		.DIVQ(3'b010),		// DIVQ =  3
		.FILTER_RANGE(3'b001),	// FILTER_RANGE = 1
        .FDA_RELATIVE(4'hf), //Not needed
        .PLLOUT_SELECT_PORTA("GENCLK"),
        .PLLOUT_SELECT_PORTB("GENCLK"),
	) uut (
		.RESETB(1'b1),
		.BYPASS(1'b0),
		.REFERENCECLK(clk),
		.PLLOUTGLOBALA(clk_fast_faster),
		.PLLOUTGLOBALB(clk_fast),
        .DYNAMICDELAY({clk_delay,4'b0}),
		);

`endif
`endif

reg transmit;
reg[7:0] tx_byte;
wire received;
wire[7:0] rx_byte;
wire is_transmitting;
wire rx_error;
reg rx_tmp,rx;
uart myUART(clk, 1'b0, rx, TX, transmit, tx_byte, received, rx_byte, , is_transmitting,rx_error );

parameter COMM_IDLE = 0;
parameter COMM_SET_DELAY = 1;
parameter COMM_SET_LENGTH = 2;
parameter COMM_SET_PWM = 3;
parameter COMM_SET_GPIO = 4;
parameter COMM_SET_CLKD = 5;

// slow-side state
reg armed;
reg[2:0] state = COMM_IDLE;

parameter TIMEOUT = 2 * 12 * 1000 * 1000;
reg[31:0] timeoutCounter; //Timeout timer for the glitcher (on the slow side!)
reg gpio_0_tmp, gpio_1_tmp;

// slow-side temporary state
reg[1:0] setting_bits;

// shared glitcher setup
reg[31:0] delay;
reg[31:0] length;

reg armed_fast, armed_ack, armed_ack_tmp;
reg done, done_tmp, done_ack;
wire armed_ack_fast, done_fast ;
reg glitcherStop;

glitcher myGlitcher(clk_fast,clk_fast_faster, trigger_in, armed_fast, armed_ack_fast, done_fast, done_ack, delay, length, switch_out, glitcherStop, clk_delay, clk_delay_target);

//The PWM values, note: the setting of the PWM values will introduce glitches
//on the line. We hope that the LPF on the line filters this out.
reg pwm_channel_to_set;
reg[9:0] pwm_value1_high;
reg[9:0] pwm_value2_high;

pwm pwm1(clk_fast,pwm_value1_high,PWM1);
pwm pwm2(clk_fast,pwm_value2_high,PWM2);

always @(posedge clk) begin
	{gpio_1, gpio_0} <= {gpio_1_tmp, gpio_0_tmp};
    {rx,rx_tmp} <= {rx_tmp,RX};
	{armed_ack_tmp, armed_ack} <= {armed_ack_fast, armed_ack_tmp};
	if (armed_ack)
		armed_fast <= 0;
	{done_tmp, done} <= {done_fast, done_tmp};
	if (done) begin
		done_ack <= 1;
		armed <= 0;
	end
	else
		done_ack <= 0;

	transmit <= 0; //By default we're not transmitting
	case (state)
	COMM_IDLE:
	begin
		glitcherStop<= timeoutCounter == 0;
		if(timeoutCounter!=0) begin 
		    timeoutCounter<= timeoutCounter - 1;
		end
		if (rx_error) begin
			state <= COMM_IDLE;
			transmit <= 1;
			tx_byte <= "Z";
			end else
		if (received) begin
			// So don't allow setting any weird stuff when armed,
			// except maybe the PWM as albert decided he needed it
			// for boot attacks
			if (armed && ~(rx_byte == "S" || rx_byte == "P" || rx_byte == "G") ) begin
				state <= COMM_IDLE;
				transmit <= 1;
				tx_byte <= "E";
			end else
			case (rx_byte)
			"S":
			begin
				state <= COMM_IDLE;
				transmit <= 1;
				if (armed && glitcherStop)
					tx_byte <= "!"; // try again
				else if (armed)
					tx_byte <= "a";
				else if (glitcherStop)
					tx_byte <= "t";
				else
					tx_byte <= "i";
			end
			"D":
			begin
				// set delay
				setting_bits <= 0;
				state <= COMM_SET_DELAY;
			end
			"L":
			begin
				// set length
				setting_bits <= 0;
				state <= COMM_SET_LENGTH;
			end
			"P":
			begin 
				//set the PWM channel
				setting_bits <= 0;
				state <= COMM_SET_PWM;
			end
			"G":
			begin 
				//set the GPO pins
				state <= COMM_SET_GPIO;
			end
            "C":
            begin
                state <= COMM_SET_CLKD;
            end
			"A":
			begin
				// arm
				armed <= 1;
				armed_fast <= 1;
				state <= COMM_IDLE;
				transmit <= 1;
				tx_byte <= "d";
				glitcherStop <=0;
				timeoutCounter <= TIMEOUT;
			end
			default:
			begin
				state <= COMM_IDLE;
				transmit <= 1;
				tx_byte <= "e";
			end
			endcase
		end
	end
	COMM_SET_LENGTH:
	begin
		if (received) begin
			length[(setting_bits+1)*8-1 -:8] <= rx_byte;
			setting_bits <= setting_bits + 1;
			if (setting_bits == 3) begin
				state <= COMM_IDLE;
				transmit <= 1;
				tx_byte <= "d";
			end
		end
	end
	COMM_SET_DELAY:
	begin
		if (received) begin
			delay[(setting_bits+1)*8-1 -:8] <= rx_byte;
			setting_bits <= setting_bits + 1;
			if (setting_bits == 3) begin
				state <= COMM_IDLE;
				transmit <= 1;
				tx_byte <= "d";
			end
		end
	end
	COMM_SET_PWM:
	begin
		if (received) begin
			case (setting_bits)
				"0":
				begin
					pwm_channel_to_set <= rx_byte;
				end
				"1":
				begin
					if(pwm_channel_to_set == 0) begin
						pwm_value1_high[9:8] <= rx_byte;
					end
					else begin
						pwm_value2_high[9:8] <= rx_byte;
					end
				end
				"2":
				begin
					if(pwm_channel_to_set == 0) begin
						pwm_value1_high[7:0] <= rx_byte;
					end
					else begin
						pwm_value2_high[7:0] <= rx_byte;
					end
					state <= COMM_IDLE;
					transmit <= 1;
					tx_byte <= "d";
				end
			endcase 
			setting_bits <= setting_bits + 1;
		end
	end
	COMM_SET_GPIO:
	begin
		if (received) begin
			{gpio_1_tmp, gpio_0_tmp} <= rx_byte;
			state <= COMM_IDLE;
			transmit <= 1;
			tx_byte <= "d";
		end
	end
    COMM_SET_CLKD:
    begin
        if(received) begin
            clk_delay_target <= rx_byte;
            state <= COMM_IDLE;
            transmit <= 1;
            tx_byte <= "d";
        end
    end
	endcase
end

assign LED5 = 0;

assign LED1 = rx_error;
assign {LED2,LED3,LED4} = 0;

endmodule 
