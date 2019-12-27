`default_nettype none

module counter(
    input clk,
    input [31:0] counterValue,
    input setCounter,
    output reg isZero
);

parameter COUNTER_BITS = 4;

reg carry0, carry1, carry2, carry3, carry4, carry5, carry6;
reg [COUNTER_BITS-1:0] counter0;
reg [COUNTER_BITS-1:0] counter1;
reg [COUNTER_BITS-1:0] counter2;
reg [COUNTER_BITS-1:0] counter3;
reg [COUNTER_BITS-1:0] counter4;
reg [COUNTER_BITS-1:0] counter5;
reg [COUNTER_BITS-1:0] counter6;
reg [COUNTER_BITS-1:0] counter7;

//reg top3Zero,top2Zero,top1Zero;

always @(posedge clk) begin
    {carry0,counter0} <= {1'b0,counter0} -1;
    {carry1,counter1} <= {1'b0,counter1} - carry0;
    {carry2,counter2} <= {1'b0,counter2} - carry1;
    {carry3,counter3} <= {1'b0,counter3} - carry2;
    {carry4,counter4} <= {1'b0,counter4} - carry3;
    {carry5,counter5} <= {1'b0,counter5} - carry4;
    {carry6,counter6} <= {1'b0,counter6} - carry5;
    {       counter7} <= {1'b0,counter7} - carry6;

    // if the bottom counter is zero, all the carries should have propagated

    isZero <= {counter0, setCounter, counter1,counter2, counter3,counter4,counter5 ,counter6,counter7,carry0} == 0;
    //isZero <= ((counter0 | counter1) | (counter2 | counter3 )) | ((counter4 | counter5) | (counter6|counter7)) == 0 && carry0==0;
    if(setCounter)
    begin
        {counter7,counter6,counter5,counter4,counter3, counter2, counter1, counter0} <= {counterValue};
	{carry0,carry1,carry2,carry3,carry4,carry5,carry6} <=0;
    end

end

endmodule
