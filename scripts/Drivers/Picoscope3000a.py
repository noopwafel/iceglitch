import ctypes
from picosdk.ps3000a import ps3000a as ps
import numpy as np
import matplotlib.pyplot as plt
from picosdk.functions import adc2mV, assert_pico_ok

class Picoscope3000a:
    def __init__(self):
        # Create chandle and status ready for use
        self.status = {}
        self.chandle = ctypes.c_int16()

        # Opens the device/s
        self.status["openunit"] = ps.ps3000aOpenUnit(ctypes.byref(self.chandle), None)



        try:
            assert_pico_ok(self.status["openunit"])
        except:

            # powerstate becomes the status number of openunit
            powerstate = self.status["openunit"]

            # If powerstate is the same as 282 then it will run this if statement
            if powerstate == 282:
                # Changes the power input to "PICO_POWER_SUPPLY_NOT_CONNECTED"
                self.status["ChangePowerSource"] = ps.ps3000aChangePowerSource(self.chandle, 282)
                # If the powerstate is the same as 286 then it will run this if statement
            elif powerstate == 286:
                # Changes the power input to "PICO_USB3_0_DEVICE_NON_USB3_0_PORT"
                self.status["ChangePowerSource"] = ps.ps3000aChangePowerSource(self.chandle, 286)
            else:
                raise

            assert_pico_ok(self.status["ChangePowerSource"])

    # Channel : A=0,B=1,C=2,D=3,EXT=4?
    # enabled : False=0,True=1
    # Coupling: AC=0,DC=1
    # Range = 50mV=1 100mV=2 200mV=3 500mV=4 1V=5 2V=6 5V=7 10V=8 20V=9
    # Analogue_offset = TODO, looks really nice though

    def setChannel(self,channel,enabled=1,coupling_type=1,Range = 8,analogue_offset=0):
        # Set up channel A
        # handle = chandle
        # channel = PS3000A_CHANNEL_A = 0
        # enabled = 1
        # coupling type = PS3000A_DC = 1
        # range = PS3000A_10V = 8
        # analogue offset = 0 V
        self.chARange = Range
        self.status["setChA"] = ps.ps3000aSetChannel(self.chandle, channel, enabled, coupling_type, Range, analogue_offset)
        assert_pico_ok(self.status["setChA"])

    # source: B = 0 ?
    # enable: 

    def setTrigger(self,channel,enable=1,threshold=1024,direction=3,delay=0,autoTrigger_ms=5000):
        # Sets up single trigger
        # Handle = Chandle
        # Source = ps3000A_channel_B = 0
        # Enable = 0
        # Threshold = 1024 ADC counts
        # Direction = ps3000A_Falling = 3
        # Delay = 0
        # autoTrigger_ms = 1000
        self.status["trigger"] = ps.ps3000aSetSimpleTrigger(self.chandle,channel,enable,threshold,direction,delay, autoTrigger_ms)
        assert_pico_ok(self.status["trigger"])

    def setTimebase(self,postTriggerSamples=0,preTriggerSamples=0, timebase=2):
        # Gets timebase innfomation
        # Handle = chandle
        # Timebase = 2 = timebase
        # Nosample = maxsamples
        # TimeIntervalNanoseconds = ctypes.byref(timeIntervalns)
        # MaxSamples = ctypes.byref(returnedMaxSamples)
        # Segement index = 0
        self.timebase = timebase
        self.preTriggerSamples=int(preTriggerSamples)
        self.postTriggerSamples=int(postTriggerSamples)
        self.maxsamples=preTriggerSamples+postTriggerSamples
        self.timeIntervalns = ctypes.c_float()
        self.returnedMaxSamples = ctypes.c_int16()
        segment_index=0
        self.status["GetTimebase"] = ps.ps3000aGetTimebase2(self.chandle, timebase, self.maxsamples, ctypes.byref(self.timeIntervalns), 1, ctypes.byref(self.returnedMaxSamples), segment_index)
        assert_pico_ok(self.status["GetTimebase"])


    def arm(self):
        # Creates a overlow location for data
        self.overflow = ctypes.c_int16()
        # Creates converted types maxsamples
        self.cmaxSamples = ctypes.c_int32(self.maxsamples)

        # Starts the block capture
        # Handle = chandle
        # Number of prTriggerSamples
        # Number of postTriggerSamples
        # Timebase = 2 = 4ns (see Programmer's guide for more information on timebases)
        # time indisposed ms = None (This is not needed within the example)
        # Segment index = 0
        # LpRead = None
        # pParameter = None
        self.status["runblock"] = ps.ps3000aRunBlock(self.chandle, self.preTriggerSamples, self.postTriggerSamples, self.timebase, 1, None, 0, None, None)
        assert_pico_ok(self.status["runblock"])

        # Create buffers ready for assigning pointers for data collection
        self.bufferAMax = (ctypes.c_int16 * self.maxsamples)()
        self.bufferAMin = (ctypes.c_int16 * self.maxsamples)() # used for downsampling which isn't in the scope of this example

        # Setting the data buffer location for data collection from channel A
        # Handle = Chandle
        # source = ps3000A_channel_A = 0
        # Buffer max = ctypes.byref(bufferAMax)
        # Buffer min = ctypes.byref(bufferAMin)
        # Buffer length = maxsamples
        # Segment index = 0
        # Ratio mode = ps3000A_Ratio_Mode_None = 0
        self.status["SetDataBuffers"] = ps.ps3000aSetDataBuffers(self.chandle, 0, ctypes.byref(self.bufferAMax), ctypes.byref(self.bufferAMin), self.maxsamples, 0, 0)
        assert_pico_ok(self.status["SetDataBuffers"])

        # Creates a overlow location for data
        self.overflow = (ctypes.c_int16 * 10)()
        # Creates converted types maxsamples
        self.cmaxSamples = ctypes.c_int32(self.maxsamples)


    def get_samples(self):
        # Checks data collection to finish the capture
        ready = ctypes.c_int16(0)
        check = ctypes.c_int16(0)
        while ready.value == check.value: # Note: we assume that the AUTOTRIGGER function is used here
            self.status["isReady"] = ps.ps3000aIsReady(self.chandle, ctypes.byref(ready))

        # Handle = chandle
        # start index = 0
        # noOfSamples = ctypes.byref(cmaxSamples)
        # DownSampleRatio = 0
        # DownSampleRatioMode = 0
        # SegmentIndex = 0
        # Overflow = ctypes.byref(overflow)

        self.status["GetValues"] = ps.ps3000aGetValues(self.chandle, 0, ctypes.byref(self.cmaxSamples), 0, 0, 0, ctypes.byref(self.overflow))
        assert_pico_ok(self.status["GetValues"])

        # Finds the max ADC count
        # Handle = chandle
        # Value = ctype.byref(maxADC)
        maxADC = ctypes.c_int16()
        self.status["maximumValue"] = ps.ps3000aMaximumValue(self.chandle, ctypes.byref(maxADC))
        assert_pico_ok(self.status["maximumValue"])

        # Converts ADC from channel A to mV
        adc2mVChAMax =  adc2mV(self.bufferAMax, self.chARange, maxADC)

        # Creates the time data
        #time = np.linspace(0, (self.cmaxSamples.value) * timeIntervalns.value, self.cmaxSamples.value)
        #print self.bufferAMax
        #return np.array(self.bufferAMax,dtype='int16')
        return np.array(adc2mVChAMax)


    def close(self):
        self.status["stop"] = ps.ps3000aStop(self.chandle)
        assert_pico_ok(self.status["stop"])

        # Closes the unit
        # Handle = chandle
        self.status["close"] = ps.ps3000aCloseUnit(self.chandle)
        assert_pico_ok(self.status["close"])
