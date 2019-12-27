#!/usr/bin/python3
'''
Simple script to play around with the PWM channels on the IceGlitcher.
There are 2 running modes, saw-tooth and set
    set example:
        ./test-pwm.py 3.3
    saw-tooth example:
        ./test-pwm.py
'''

import os
import sys
import time
import serial
from Drivers import FindSerial, IceGlitcher


glitcher = IceGlitcher(FindSerial().get_path({'PRODUCT':'403/6010/700', 'DEVPATH':'1\.1$'}))

if len(sys.argv) > 1:
    value = int(sys.argv[1])
    print("Setting gpios to", value)
    glitcher.set_gpio(value)
    sys.exit(0)

while True:
     for i in range(0,16,1):
         glitcher.set_clk_delay(i)
