#!/usr/bin/python3

'''
# FindSerial: class to make management of /dev/ttyUSB* devices easier.
# the names in /dev/ttyUSB* change depending on the order they were plugged in.
# Give FindSerial a UNIQUE descriptor and it will give you the right path.
# While the goal is to make this independent of where you plug in the device,
# this isn't always possible: If you have 2 of exactly the same device,
# however you can then use the DEVPATH.. :(


# NOTE: Run this file without arguments to see what devices are available:


# EXAMPLE in python code
#    ser = serial.Serial(port=FindSerial().get_path({'PRODUCT':'403/6010/700', 'DEVPATH': '1.1$'}),
#                baudrate=9600
#                )

'''
from os import path, listdir
import sys
import re
import pyudev
def _print_device(device):
    ttys = [path.join('/dev', f) for f in listdir(device.sys_path) if f.startswith('tty')]
    print('#'*60)
    if len(ttys) > 0:
        print(ttys[0])
    keys = ['ID_VENDOR_FROM_DATABASE',
            'ID_VENDOR_ID',
            'ID_PRODUCT_ID',
            'ID_REVISION',
            'ID_SERIAL',
            'ID_SERIAL_SHORT',
            'ID_USB_DRIVER',
            'ID_INSTANCE',
            'ID_MODEL_ID',
            'PRODUCT',
            'MODALIAS'
           ]
    for key in keys:
        val = device.get(key, None)
        if val:
            print(key, '\t', val)

def _match_constraints(constraints, device, tty):
    '''
    Match everything against parent device, except DEVPATH!!
    Given this is a regexp, mostly wont be able to tell the difference
    '''
    for key in constraints.keys():
        if key == 'DEVPATH':
            if not re.search(constraints[key], tty[key]):
                return False
        elif not re.search(constraints[key], device.get(key, 'unknown')):
            return False
    return True

def _is_parent(child, parent):
    if child.startswith(parent) and parent != child and '/' not in child[len(parent)+1:-1]:
        return True
    return False


class FindSerial:
    ''' See module Description '''
    def __init__(self):
        self.context = pyudev.Context()

    def get_path(self, constraints):
        '''
        Returns a path to the device uniquely identified by constraints.
        if a device is not uniquely identified throw an exception
        '''
        ret = []
        for tty in self._get_tty_devs():
            for device in self.context.list_devices(subsystem='usb'):

                # The driver we're looking for has a kid which has a /dev/tty* address
                if not _is_parent(tty['DEVPATH'], device.get('DEVPATH', 'UNKNOWN')):
                    continue

                if not _match_constraints(constraints, device, tty):
                    continue

                if len(tty) > 0:
                    print("found tty within constraints: ", constraints)
                    print("tty", tty['tty'])
                    ret.append(tty['tty'])

        if len(ret) == 1:
            return ret[0]

        self.print_serial_devices()
        if len(ret) > 1:
            message = "Constraints match multiple dev. Constraints: "
            message += str(constraints)+" devices: "+str(ret)
            raise Exception(message)
        raise Exception("Constraint don't match any device: "+str(constraints))

    def print_serial_devices(self):
        '''Print the serial devices and properties which can be used to create constraints.'''
        for tty in self._get_tty_devs():
            for device in self.context.list_devices(subsystem='usb'):
                if not _is_parent(tty['DEVPATH'], device.get('DEVPATH', 'UNKNOWN')):
                    continue
                if len(tty) > 0:
                    _print_device(device)
                    print("TTY", tty)

    def print_all_devices(self):
        ''' Print all USB devices and properties which can be used to create constraints'''
        for device in self.context.list_devices(subsystem='usb'):
            _print_device(device)

    def _get_tty_devs(self):
        ret = []
        for dev in self.context.list_devices(subsystem='usb'):
            ttys = [path.join('/dev', f) for f in listdir(dev.sys_path) if f.startswith('tty')]
            if len(ttys) == 0:
                continue
            #self._print_device(device)
            ret.append({'tty' : ttys[0], 'DEVPATH':dev.get('DEVPATH', None)})
        return ret



if __name__ == '__main__':
    if len(sys.argv) > 1:
        FindSerial().print_all_devices()
    else:
        FindSerial().print_serial_devices()

#    print(FindSerial().get_path({'PRODUCT':'403/6010/700', 'DEVPATH': '1.1$'}))
