#!/usr/bin/env python
# vim: set ts=4 sw=4 et sts=4 ai:

import sys
import subprocess
import time
import os

from modeswitch import call
import modeswitch

def start(a):
    print(a, "...", sep="", end="")
    sys.stdout.flush()
def finish():
    print("Done")

def cleanup():
    for f in ["barcode_mac_small.png", "barcode_mac_large.png", "barcode_dna_small.png", "barcode_dna_large.png"]:
        if os.path.exists(f):
            os.unlink(f)
cleanup()

start("Getting MAC address")
modeswitch.switch("eeprom")
call("python opsis_eeprom_prog.py")
finish()

start("Getting Device DNA")
modeswitch.switch("jtag")
call("python openocd_readdna.py numato_opsis")
finish()

outfile = "label-%s.png" % time.time()

call("inkscape -C -f label.svg -w 1200 -h 1800 -e %s --export-background=white" % outfile)

print("Image generated in %s" % outfile)
cleanup()
