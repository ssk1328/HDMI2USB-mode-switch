#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# vim: set ts=4 sw=4 et sts=4 ai:

import subprocess
import time

def call(a):
    subprocess.check_output(a, shell=True, stderr=subprocess.STDOUT)

def switch(mode):
    for i in range(0, 3):
        try:
            call("python hdmi2usb-mode-switch.py --mode "+mode)
            break
        except Exception as e:
            exp = e
            time.sleep(1)
    else:
        raise exp

