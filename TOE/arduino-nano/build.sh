#!/bin/sh
set -e

avr-gcc -Wall -Wpedantic -Wextra -g -O3 -mmcu=atmega328p --std=gnu99 -flto  -o main.bin *.c 
avr-size -C main.bin
avr-objcopy -j .text -j .data -O ihex main.bin main.hex

avrdude -p m328p -cavrispmkii  -U flash:w:main.hex:i -P usb
