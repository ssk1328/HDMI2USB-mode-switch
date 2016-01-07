#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# vim: set ts=4 sw=4 et sts=4 ai:

from modeswitch import call

while True:
    raw_input("Plug in Opsis board and hit enter...")
    call("make-label.py")
    print()
    
