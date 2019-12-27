#!/usr/bin/python3 
''' A script to run a glitching setup'''
import os
import time
import binascii
import traceback
from collections import OrderedDict
from random import randint, uniform
import serial
from Drivers import FindSerial, IceGlitcher
from Utils import FiCsvWriter, hex_ascii 

#
##  Glitch parameters
#

def get_params():
    '''parameter generator for glitching'''
    for run in range(9**9):
        yield OrderedDict([
            ('attempt', run),
            ('length', uniform(1, 400)), # in nano seconds
            ('delay', uniform(0.0001,0.00630)), # in seconds
            ('volts', uniform(0.0, 3.3)),
        ])

normal_voltage = 3.3
MAX_MUTES_IN_A_ROW = 1 # If we get a lot of mutes in a row we need to reset the target hard

NORMAL_PWM = 0
GLITCH_PWM = 1

TARGET_TIMEOUT_NORMAL = 0.030
TARGET_TIMEOUT_RESET = 0.090

#
## End Glitch parameters
#

database = FiCsvWriter("log-nano.csv")
table_name = None

target_path = FindSerial().get_path({'PRODUCT':'403/6001/600'}) # FTDI cable
#target_path = FindSerial().get_path({'PRODUCT':'67b/2303/300'}) # Serial 2 USB PCB
os.system("setserial %s low_latency"%target_path)
target = serial.Serial(target_path,
                       baudrate=19200,
                       timeout=TARGET_TIMEOUT_NORMAL)
glitcher = IceGlitcher(FindSerial().get_path({'PRODUCT':'403/6010/700', 'DEVPATH':'1\.1$'}))

mutes_in_a_row = 2

def _test_target(device):
    print("Testing device")
    _reset_target(device)
    for i in range(20):
        print(".", end=' ')
        device.write(b't')
        if device.read(100) == b'T\r\n':
            break

def _reset_target(device):
    glitcher.set_pwm(NORMAL_PWM, 0.0)
    time.sleep(0.001)
    glitcher.set_pwm(NORMAL_PWM, 3.3)
    time.sleep(0.001)

    device.timeout = TARGET_TIMEOUT_RESET
    resp = device.read(100)
    device.timeout = TARGET_TIMEOUT_NORMAL
    if b'Arduino' in resp:
        print("Target came back up: ", hex_ascii(resp))
    else:
        print("[T] Target failed to come back up", hex_ascii(resp), binascii.hexlify(resp))

_test_target(target)

# First, perform an operation without glitching for comparison later
target.write(b'recipe\na\n')
expected_response = target.read(100)
print('Expected response: ', binascii.hexlify(expected_response),
      'ascii:', hex_ascii(expected_response))

for attempt in get_params():
    try:
        if mutes_in_a_row >= MAX_MUTES_IN_A_ROW:
            print("\nToo many mutes in row resetting: ", end='')
            mutes_in_a_row = 0
            _reset_target(target)
    
        # send most of the message
        target.write(b'recipe\na')

        # Send parameters to glitcher
        glitcher.set_params(attempt['length'] , attempt['delay'], normal_voltage, attempt['volts'])
        time.sleep(0.014)
        response = target.read(51)

        glitcher.arm() # Tell the glitcher to get ready

        target.write(b'\n') # send last byte and trigger the glitcher

        glitcherTimeout = glitcher.wait_for_glitcher()
        response = target.read(100) # Get response data, a glitched target can send more data

        color = 'k' # default to black
        mutes_in_a_row += 1 # Unless it's good it was bad ;)

        if glitcherTimeout:
            print('[G] The glitcher timed out')
        elif b'Incorrect' in response:
            print("Correct response!")
            mutes_in_a_row = 0
            color = 'g'
        elif b'Ardu' in response: # short for Arduino
            color = 'y' # should really be orange
        elif len(response) < len("Incorrect\r\n") or b'know about, nano' in response:
            color = 'y'
        elif b'rice' in response:
            print("Glitch i guess")
            response += target.read(100)
            color = 'r'
        else:
            print("TARGET RESPONDED:")
            color = 'm'

        # The measurement data to the attempt
        attempt['data'] = response
        attempt['color'] = color

        database.write(attempt)

    except Exception:
        traceback.print_exc()
        _test_target(target)
