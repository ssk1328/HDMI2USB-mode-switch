#!/usr/bin/env python
# vim: set ts=4 sw=4 et sts=4 ai:

import sys
import subprocess
import time
import os

from modeswitch import call
import modeswitch

def start(a):
    print(a, "...", sep="", end=" ")
    sys.stdout.flush()

def cleanup():
    for f in ["qrcode_mac.png", "qrcode_dna.png", "dna.txt", "mac.txt"]:
        if os.path.exists(f):
            os.unlink(f)
cleanup()

start("Getting MAC address")
modeswitch.switch("eeprom")
call("python opsis_eeprom_prog.py")
mac = open("mac.txt", "r").read().strip()
smac = mac.replace(":","-")
print(mac)

start("Getting Device DNA.")
modeswitch.switch("jtag")
call("python openocd_readdna.py numato_opsis")
dna = open("dna.txt", "r").read().strip()
print(dna)

tmpfile = "label_%s_%s.svg" % (smac, dna)
outfile = "label_%s_%s.png" % (smac, dna)

d = open("label.svg").read()
d = d.replace("0x000000000000000", dna)
d = d.replace("00:00:00:00:00:00", mac)
open(tmpfile, "w").write(d)

call("inkscape -C -f %s -w 812 -h 1218 -e %s --export-background=white" % (tmpfile, outfile))
os.unlink(tmpfile)

print("Image generated in %s" % outfile)

print("Printing %s" % outfile)
call("lpr -o ppi=203 -o Resolution=203dpi -o PageSize=w288h432 %s" % outfile)
cleanup()
