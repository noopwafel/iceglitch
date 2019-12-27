''' Module for: THE ICE GLITSER '''
import os
import sys
import struct
import serial
import binascii
from Utils import hex_ascii

def _pack32(val):
    return struct.pack("<I", val)

def _calc_time(sec):
    ''' TODO move into set_length_and_delay'''
    return int(sec * 348 * 1000 * 1000 + 0.5)

def _calc_nano_time(nsec):
    '''Calculate time in nano seconds
        nsec is a float, we will use the clk_delay trick to get as close to it as possible
    '''
    ticks = int(nsec * 348 / 1000) # floor it and then add clk_delay shifts
    delays = int((nsec - (ticks / (348 /1000))) / 0.150)

#    print("ticks",ticks,"delays",delays)
    delays = min(delays, 15)
    #delays = (delays + 8) % 16 # phase inv
    return ticks, delays

def get_pwm_val(volt):
    ''' Script helper function. Import with:
        from IceGlitcher import get_pwm_val
    Takes PWM voltage and returns the corresponding int for PWM configuration. '''
    
    pwm_unit = (3.3/512)
    pwm_val = int(volt / pwm_unit)

    # print("[get_pwm_val] pwm_val: %d" % pwm_val)

    return pwm_val

def get_pwm_volt(val):
    ''' Script helper function. Import with:
        from IceGlitcher import get_pwm_volt
    Takes PWM integer and returns the corresponding voltage '''

    pwm_unit = (3.3/512)
    pwm_volt = val * pwm_unit

    # print("[get_pwm_volt] pwm_volt: %.4f" % pwm_volt)

    return pwm_volt

def _prepare_pwm_cmd(channel, val, translate=True):
    ''' channel 1 or 2, val: voltage between 0 and 3.3v '''
    if translate:
        val = int(val / (3.3 / 1023) + 0.5)
        val = min(val, 1023)
        val = max(val, 0)
    else:
        # LSB is ignored at the FPGA interface. Practically shifts 1 bit right, dividing by 2
        # Here we compensate by multiplying the inout value by 2.
        val = val * 2 

    # print("[_prepare_pwm_cmd] pwm_val: %d" % val)

    return b'P' + bytes([channel, val >> 8, val & 0xff])

class IceGlitcher:
    ''' The Ice glitcher!'''
    def __init__(self, serial_path):
        os.system("setserial %s low_latency"%serial_path) # low latency!!!
        self.serial = serial.Serial(serial_path, baudrate=1e6, timeout=0.5)

        done = False
        for _ in range(100):
            self.serial.write(b'S')
            status = self.serial.read(1)
            #print(b"status %b" % status)
            if status == b'i':
                done = True
                break
            elif status == b't':
                done = True
                break

        if not done:
            raise Exception("IceGlitcher is stuck in arm")

    def _write_cmd(self, cmd, expected=b'd'):
    #    print(b"write %b" % cmd)
        self.serial.write(cmd)
        response = self.serial.read(1)
    #    print(b"got %b" % response)
        if response != expected:
            print("Bad response (expected %s): %s" % (hex_ascii(expected), hex_ascii(response)))
            raise Exception("Bad response (expected %x): %x" % (ord(expected), ord(response)))

    def _set_delay(self, val):
        ''' Use set_length_and_delay so that an off-by-one is prevented '''
        self._write_cmd(b'D' + _pack32(val))

    def _set_length(self, val):
        ''' Use set_length_and_delay so that an off-by-one is prevented'''
        self._write_cmd(b'L' + _pack32(val))

    def set_length_and_delay(self, length, delay):
        ''' Due to the implementation of the DDR glitch pin,
            we need to compensate when a DDR piece is used for the delay
            The glitch will appear to start half a clock cycle earlier

            length in nanoseconds and delay in seconds
        '''
        delay = _calc_time(delay)
        length, clk_delay = _calc_nano_time(length)
        if delay & 1 == 0:
            length = max(length-1,0)

        self._set_delay(delay)
        self._set_length(length)
        self.set_clk_delay(clk_delay)

    def set_pwm(self, channel, val):
        ''' channel 1 or 2, val: voltage between 0 and 3.3v '''
        self._write_cmd(_prepare_pwm_cmd(channel, val))

    def set_pwm_raw(self, channel, val):
        ''' channel 1 or 2, val: voltage between 0 and 3.3v '''
        cmd = b'P' + bytes([channel, val >> 8, val & 0xff])
        self._write_cmd(cmd)

    def set_gpio(self, bitmap):
        ''' Set the 2 GPIO pins in 1 go '''
        self._write_cmd(b'G' + bytes([bitmap & 0x3]))

    def set_clk_delay(self, bitmap):
        ''' Set the 2 GPIO pins in 1 go '''
        self._write_cmd(b'C' + bytes([bitmap & 0xf]))

    def arm(self):
        ''' Tell the IceGlitcher to get ready for the trigger'''
        self._write_cmd(b'A')


    def wait_for_glitcher(self):
        '''After the glitcher has been armed, wait for it to complete glitching'''
        while True:
            self.serial.write(b'S')
            status = self.serial.read(1)
            if status == b'i':
                return False # good
            elif status == b't':
                return True # timed out

    def set_params(self, length=None, delay=None, pwm1=None, pwm2=None, translate_pwm0=True, translate_pwm1=True):
        '''Set all the parameters in 1 go, this should get rid of the RTT overhead'''
        '''PWM goes first as it needs more settling time, however at 1e6...'''

        buf = b''
        sent_messages = 0
        if pwm1:
            buf += _prepare_pwm_cmd(0, pwm1, translate_pwm0)
            sent_messages += 1
        if pwm2:
            buf += _prepare_pwm_cmd(1, pwm2, translate_pwm1)
            sent_messages += 1
        if length:
            delay = _calc_time(delay)
            length, clk_delay = _calc_nano_time(length)
            if delay and delay % 2 == 1: # do we have DDR delay?
                length = max(length-1,0)
            if length & 1 == 1: # we have a DDR length
                clk_delay = (clk_delay + 9) & 0xf

                if clk_delay <= 8: # handle the phase inversion
                    length = ((length & 0xffFFffFe) << 1) + 1
                else:
                    length = ((length & 0xffFFffFe) << 1) + 2


            else:
                length = (length << 1) + 0
                clk_delay = (clk_delay + 9) & 0xf

            buf += b'L' + _pack32(length)
            buf += b'C' + bytes([clk_delay])
            sent_messages += 2

        if delay:
            buf += b'D' + _pack32(delay)
            sent_messages += 1

        self.serial.write(buf)
        recv = self.serial.read(sent_messages)

        if recv != b'd' * sent_messages:
            raise Exception("Received incorrect output for:"+str(recv)+" messages: "+str(sent_messages))
            sys.exit(-1)

    def status(self):
        ''' Is the glitcher ready to start glitching'''
        self.serial.write(b'S')
        return self.serial.read(1)
