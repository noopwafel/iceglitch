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
    value = float(sys.argv[1])
    print("Setting pwm channels to",value)
    glitcher.set_pwm(0,value)
    glitcher.set_pwm(1,value)
    sys.exit(0)

while True:
    for i in range(1023):
#        time.sleep(1.0)
        i = (3.3 / (1023)) * i
        print(i)
        glitcher.set_pwm(0,i)
        glitcher.set_pwm(1,i)
