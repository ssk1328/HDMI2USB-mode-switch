#!/usr/bin/env python
# vim: set ts=4 sw=4 et sts=4 ai:

import sys
import subprocess
import time
import os

def start(a):
    print(a, "...", sep="", end="")
    sys.stdout.flush()
def finish():
    print("Done")

def call(a):
    subprocess.check_output(a, shell=True, stderr=subprocess.STDOUT)

if os.path.exists("barcode_mac.svg"):
    os.unlink("barcode_mac.svg")
if os.path.exists("barcode_dna.svg"):
    os.unlink("barcode_dna.svg")

start("Getting MAC address")
exp = None
for i in range(0, 3):
    try:
        call("python hdmi2usb-mode-switch.py --mode eeprom")
        break
    except Exception as e:
        exp = e
        time.sleep(1)
else:
    raise exp
call("python opsis_eeprom_prog.py")
finish()

start("Getting Device DNA")
call("python hdmi2usb-mode-switch.py --mode jtag")
call("python openocd_readdna.py numato_opsis")
finish()

def get_barcode(a):
    lines = []
    for line in a.splitlines():
        if not line.startswith("        "):
            continue
        lines.append(line)

    return lines[1:]

mac = get_barcode(open("barcode_mac.svg").read())
dna = get_barcode(open("barcode_dna.svg").read())

template = open("label.svg").read()

template = template.replace("<!-- mac address -->", "\n        ".join(mac))
template = template.replace("<!-- dna address -->", "\n        ".join(dna))

f = open("label-out.svg", "w")
f.write(template)
f.close()

outfile = "label-%s.png" % time.time()

call("inkscape -C -f label-out.svg -w 1200 -h 1800 -e %s --export-background=white" % outfile)

os.unlink("label-out.svg")
os.unlink("barcode_mac.svg")
os.unlink("barcode_dna.svg")

print("Image generated in %s" % outfile)
