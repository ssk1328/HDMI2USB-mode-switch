#!/usr/bin/env python
# vim: set ts=4 sw=4 et sts=4 ai:

import subprocess
import re
import sys

output = subprocess.check_output("""\
openocd --file board/%s.cfg -c "init; xc6s_print_dna xc6s.tap; exit"
""" % sys.argv[1], shell=True, stderr=subprocess.STDOUT)

for line in output.splitlines():
    line = line.decode('utf-8')
    if not line.startswith('DNA = '):
       continue

    dna = re.match("DNA = ([10]*) \((0x[01-9a-f]*)\)", line)
    binv, hexv = dna.groups()
    binc = int(binv, 2)
    hexc = int(hexv, 16)
    assert binc == hexc


    import qrcode
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        border=1,
    )
    hexs = hex(hexc)
    print(hexs)
    open("dna.txt","w").write(hexs)
    qr.add_data(hexs)
    img = qr.make_image()
    img.save("qrcode_dna.png")
