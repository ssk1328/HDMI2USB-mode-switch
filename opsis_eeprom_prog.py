#!/usr/bin/env python
# vim: set ts=4 sw=4 et sts=4 ai:

import array
import usb.core
import usb.util


VC_EEPROM=0xB1
READ_EEPROM=0xC0
WRITE_EEPROM=0x40

def get_eeprom(dev, addr, amount):
    data = array.array('B')
    while len(data) < amount:
        transfer_size = min(64, amount-len(data))

        result = dev.ctrl_transfer(READ_EEPROM, VC_EEPROM, addr+len(data), 0, transfer_size)
        assert len(result) == transfer_size, "len(result) %i == %i" % (len(result), transfer_size)

        data += result

    return data

def set_eeprom(dev, addr, data):
    offset = 0
    while offset < len(data):
        transfer_size = min(32, len(data)-offset)
        result = dev.ctrl_transfer(WRITE_EEPROM, VC_EEPROM, addr+offset, 0, data[offset:offset+transfer_size])
        assert result == transfer_size, "result %i == %i" % (result, transfer_size)
        offset += transfer_size

def get_dev():
    # find our device
    dev = usb.core.find(idVendor=0x2A19, idProduct=0x5441)

    # was it found?
    if dev is None:
        raise ValueError('Device not found')

    dev.set_configuration()
    return dev


import sys
import argparse
import time
import opsis_eeprom

import modeswitch
try:
    dev = get_dev()
except ValueError:
    modeswitch.switch("eeprom")
    dev = get_dev()

current_eeprom_data = get_eeprom(dev, 0, opsis_eeprom.OpsisEEPROM.size())
old_eeprom_data = bytes(current_eeprom_data)

s = opsis_eeprom.OpsisEEPROM.from_buffer(current_eeprom_data)

if len(sys.argv) > 1:
    s.populate()
    print("Data to be programmed...")
    print("-"*40)
    print(repr(s))
    print("-"*40)
    print()

    new_eeprom_data = bytes(current_eeprom_data)

    print("Current contents:", repr(old_eeprom_data))
    print("    New contents:", repr(new_eeprom_data))

    print()
    print()
    print("Programming...", end="")
    sys.stdout.flush()
    if old_eeprom_data != new_eeprom_data:
        set_eeprom(dev, 0, new_eeprom_data)
    print("Done!")
    print()
    print("Run the tool again without --go to verify programming.")
else:
    print()
    print("Current contents:", repr(old_eeprom_data))
    print()
    try:
        print("Checking EEPROM contents!")
        s.check()
    except:
        print("Check failed!")
        print("Check failed!")
        print("Check failed!")
        print("Check failed!")
        print()
        print("Run this program with --go to program EEPROM.")
        del dev
        sys.exit(1)
    print()
    print("-"*40)
    print(repr(s))
    print("-"*40)
    print("Data verified successfully!")
    img = s.mac_qrcode().make_image()
    img.save("qrcode_mac.png")
    open("mac.txt", "w").write(s.mac())
