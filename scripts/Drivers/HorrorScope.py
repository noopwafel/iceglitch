import serial
import numpy as np

class HorrorScope:
    def __init__(self,
            port='/dev/ttyACM0',
            timeout=2.5,
            numSamples = 3500, 
            sampleSpeed=2, # 1=4msps,2=2 msps,3=1 msps (from 0-7 )
            bits12=True, # 12 bit mode?
            bias = 0x444,
            gain = 0, # Value from 0-7 -> 1,2,4,8,16,32,64,1/2
            delay = 0, # wait before sampling (in a non-defined-made-up-unit)
        ):

        self.port = port
        self.timeout=timeout

        self.serial = None

        self.numSamples = numSamples
        self.clockDivider = sampleSpeed
        self.bits12 = bits12
        self.bias = bias
        self.gain = gain
        self.delay = delay

        self.reconnect()

    def reconnect(self):

        while True:
            if self.serial != None:
                self.serial.close()

            self.serial = serial.Serial(port=self.port,baudrate=115200,timeout=self.timeout)
            if self._testScope():
                break

        self.setSamples(self.numSamples)
        self.setSampleSpeed(self.clockDivider)
        self.set12Bits(self.bits12)
        self.setBias(self.bias)
        self.setGain(self.gain)
        self.setDelay(self.delay)

    # This routine is to check if the scope behaves as it should. Cheap trick to find non-responsive boards, half finished commands etc.
    def _testScope(self):
        print("Testing Scope: if you're getting a lot of dots, reset the scope board. Maybe board is waiting for trigger?")

        oldTimeout = self.serial.timeout
        self.serial.timeout = 0.2

        self.serial.write(b't')
        val =  self.serial.read(10)
        ret = False
        if val == b'T':
            ret = True
        elif val == 'T\r\n':
            print("Switched target and scope serial ports")

        self.serial.timeout = oldTimeout

        return ret


    def _checkResponse(self):
        response = self.serial.read(1)
        if response != b'd':
            raise Exception("Incorrect response:"+response.hex()+" extra: "+ self.serial.read(100).hex() )

    def setSamples(self,numSamples):
        self.numSamples = numSamples
        assert numSamples <= 0xffff # in reality this should be even lower
        self.serial.write(b'n' + bytes([numSamples >> 8, numSamples & 0xff] ) )
        self._checkResponse()

    def set12Bits(self,bits12):
        self.bits12 = bits12
        if self.bits12:
            self.serial.write(b'8\x01')
        else:
            self.serial.write(b'8\x00')
        self._checkResponse()


    def setBias(self,bias):
        assert bias <= 0xffff
        self.bias = bias
        self.serial.write(bytes([ord('b'), bias >> 8, bias & 0xff]))
        self._checkResponse()

    def setDelay(self,delay):
        assert delay <= 0xffff
        self.delay = delay
        self.serial.write(bytes([ord('w'), delay >> 8, delay & 0xff]))
        self._checkResponse()

    def setSampleSpeed(self,clockDivider):
        assert clockDivider <= 0xff
        self.clockDivider = clockDivider
        self.serial.write(b'c' + bytes([clockDivider]) )
        self._checkResponse()

    def setGain(self,gain):
        assert gain <= 0xff
        self.gain = gain
        self.serial.write(b'g'+bytes([gain]))
        self._checkResponse()

    def waitForCompletion(self):
        response = self.serial.read(1)
        if response == b'e':
            return False
        if response == b'd':
            return True
        raise Exception("incorrect response")

    def arm(self):
        self.serial.write(b'd')
        armed = self.serial.read(1)
        if armed != b'r':
            additional = self.serial.read(100)
            raise Exception("Scope hasn't armed!" + armed.hex() + "additional" + additional.hex() + '    ' )

    def getSamples(self):
        self.serial.write(b's')
        samples = self.serial.read(self.numSamples) 
        
        if len(samples) != self.numSamples:
            raise Exception("Scope didn't return enough samples("+str(self.numSamples)+"):" + str(len(samples)) )


        #This turns 2 bytes into a int16
        if self.bits12:
            return np.frombuffer(samples,'<i2').astype('float32')

        return np.frombuffer(samples,dtype=np.uint8)

    def close(self):
        if self.serial != None:
            self.serial.close()
            self.serial =None

    #
    ## Glitching methods
    #

    # Power on/off are used to implement hard resets of the target
    def powerOn(self): 
        self.serial.write(b'y')
        self._checkResponse()

    def powerOff(self):
        self.serial.write(b'x')
        self._checkResponse()

    # we haven't added this to the constructor, as it is assumed that the glitchLength will be reset at every attempt, maybe because I'm lazy
    def setGlitchLength(self,glitchLength):
        assert glitchLength < 0xFFff
        self.serial.write(b'l' + bytes([ glitchLength>>8, glitchLength & 0xff ]) )
        self._checkResponse()

    def setPulses(self,pulses):
        assert pulses < 0xff
        self.serial.write(b'p' + bytes([ pulses & 0xff ]) )
        self._checkResponse()

    # Note: the glitch command waits for a trigger. Making it a real possibility that this times out
    # Return: timed out?
    def glitchArm(self): # TODO: this should move to the 'h' command when implemented
        self.serial.write(b'h')
        response = self.serial.read(1)
        return response != b'r' # is it ready?

    def waitForGlitcher(self):
        response = self.serial.read(1)
        return response != b'd'

    def setDAC(self,value):
        #self.serial.write(b'D' + bytes([channel & 1, value>>8, value & 0xff ]) )
        self.serial.write(b'D' + bytes([ value>>8,value & 0xff ]) )
        self._checkResponse()
        

        
