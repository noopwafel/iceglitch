
'''
DPS5005 cheap tiny lab power supply driver wrapper to make it nicer for glitching tasks
'''


import sys
import time
import rdserial.device
import rdserial.dps.tool

class DPS5005():
    '''
    DPS5005 cheap tiny lab power supply wrapper class to make glitching nicer
    '''
    def __init__(self, serialPort, voltage=None, amps=None, on=True):
        powersock = rdserial.device.Serial(serialPort, 9600)
        powersock.connect()
        power = rdserial.dps.tool.Tool()
        power.socket = powersock
        power.modbus_client = rdserial.modbus.RTUClient(power.socket, 9600)

        self.prev_voltage = None
        self.prev_amps = None
        self.prev_on = None

        class Myobj:
            '''Helper for modbus'''
            all_groups = []
            group = None
            modbus_unit = 1
        power.args = Myobj()

        self.power = power

        # Setup the defaults
        self.set_voltage_amps(voltage, amps)

        self.turn_on(on)

    def set_voltage(self, voltage):
        self.power.args.set_volts = voltage
        self.power.send_commands()
        self.power.args.set_volts = None

    def turn_on(self, on=True):
        self.power.args.set_output_state = on
        self.power.send_commands()
        self.power.args.set_output_state = None

    def set_amps(self, amps):
        self.power.args.set_amps = amps
        self.power.send_commands()
        self.power.args.set_amps = None

    def set_voltage_amps(self, voltage, amps):
        change_volt = self.prev_voltage != voltage and voltage
        change_amps = self.prev_amps != amps and amps

        self.prev_voltage = voltage
        self.prev_amps = amps

        if change_volt and change_amps:
            self.power.args.set_amps = amps
            self.power.args.set_volts = voltage
            self.power.send_commands()
            self.power.args.set_amps = None
            self.power.args.set_volts = None
        elif change_volt:
            self.set_voltage(voltage)
        elif change_amps:
            self.set_amps(amps)

        if change_volt or change_amps:
            time.sleep(0.6)

    def close(self):
        self.power.powersock.close()

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("USAGE: %s <SERIALPORT>"%sys.argv[0])

    power_device = DPS5005(sys.argv[1])
    for i in range(0, 1000, 10):
        power_device.set_voltage(5.0)
        time.sleep(0.5)
        power_device.set_voltage(0)
        time.sleep(i/1000.)
        device_state = power_device.power.assemble_device_state()
        print(i, device_state.volts)
