#!/bin/bash

set -x
set -e

BOARD=${1:-atlys}
VERSION=${1:-unstable}

SYMLINK="$(wget https://raw.githubusercontent.com/timvideos/HDMI2USB-firmware-prebuilt/master/${BOARD}/firmware/${VERSION} -O- -q)"

for F in ${BOARD}_hdmi2usb-hdmi2usbsoc-${BOARD}.bit hdmi2usb.hex sha254sum.txt; do
  rm $F || true
  wget https://github.com/timvideos/HDMI2USB-firmware-prebuilt/raw/master/${BOARD}/firmware/${SYMLINK}/${F}
done
