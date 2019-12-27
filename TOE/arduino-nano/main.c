#define F_CPU 16000000UL
#define USART_BAUDRATE 19200
#define BAUD_PRESCALE  ((F_CPU /  (USART_BAUDRATE * 16UL)) -1 )

#include <avr/io.h>
#include <avr/interrupt.h>
#include <string.h>


static void usart_init(){
    UBRR0L = BAUD_PRESCALE & 0xff;
    UBRR0H = BAUD_PRESCALE >> 8;
    UCSR0B = (1<<TXEN0) | (1<<RXEN0);
}

static uint8_t usart_getchar(){
    while( (UCSR0A & (1<<RXC0)) == 0);
        return UDR0;
}

static void usart_gets(char* buf,int maxLen){
	for(int i=0;i<maxLen;i++){
		buf[i] = usart_getchar();
		if(buf[i] == 0 || buf[i] == '\r' || buf[i] == '\n'){
			buf[i] = 0;
			break;
		}
	}
	buf[maxLen-1] = 0;
}

static void usart_putchar(uint8_t val){
    while( (UCSR0A & (1<<UDRE0)) == 0);
        UDR0 = val;
}

static void usart_putshort(uint16_t val){
    usart_putchar(val >> 8);
    usart_putchar(val & 0xff);
}

static void usart_putstring(char* string){
    for(;*string;string++)
        usart_putchar((uint8_t)*string);
}
static void usart_getbuf(uint8_t* buf,uint8_t len){
    for(uint8_t i=0;i<len;i++)
        buf[i] = usart_getchar();
}


static const uint8_t pin[] = {'9','1','1','0'};
int main(void){
    usart_init();
    usart_putstring("Welcome to the Arduino, nano!\r\n");

    char command_buf[10] = {1};
    while(1){
	usart_gets(command_buf,sizeof(command_buf));
	if( 0 == strcmp(command_buf,"Glitching is fun!") ){
		usart_putstring("You never know whats going to fall out next!\r\n");
	}else if( 0 == strcmp(command_buf,"Look at all the weird things coming out!") ){
		usart_putstring("Maybe this is a memory dump!\r\n");
	}else if( 0 == strcmp(command_buf,"recipe")){
		usart_putstring("If you want the recipe, give the password, nano\r\n\r\n");
		usart_gets(command_buf,sizeof(command_buf));
		{
			volatile int i=0;
			volatile int j=10;
			for(;i<j;i++){
				j--;
			}
		}
		if( 0 == strcmp(command_buf,"oepsiedoepsiereallylooongoepstoolong")){
		{
			volatile int i=0;
			volatile int j=10;
			for(;i<j;i++){
				j--;
			}
		}
			usart_putstring("If you were doing the workshop, the rice would be here!\r\n");
		}else{
			usart_putstring("Incorrect\r\n");
		}
	}else if( 0 == strcmp(command_buf,"home") ){
		usart_putstring("It's beautiful, nano!\r\n");
	}else if( 0 == strcmp(command_buf,"Getting closer!") ){
		usart_putstring("almost there!\r\n");
	}else if( 0 == strcmp(command_buf,"We are slackers") ){
		usart_putstring("Wow theres a lot random stuff in here\r\n");
	}else{
		usart_putstring("Oh i don't know about that\r\n\r\n");
		usart_putstring("What would you like to know about, nano?:\r\n\r\n");
		usart_putstring("home  --- talk about home\r\n");
		usart_putstring("recipe  --- Secret recipe\r\n");
        }
    }
}
