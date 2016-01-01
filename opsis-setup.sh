#!/bin/bash

set -e

sudo apt-get install realpath

CALLED=$_
[[ "${BASH_SOURCE[0]}" != "${0}" ]] && SOURCED=1 || SOURCED=0

SETUP_SRC=$(realpath ${BASH_SOURCE[0]})
SETUP_DIR=$(dirname $SETUP_SRC)
TOP_DIR=$(realpath $SETUP_DIR)

if [ $SOURCED = 1 ]; then
        echo "You must run this script, rather then try to source it."
        echo "$SETUP_SRC"
        return
fi

echo "             This script is: $SETUP_SRC"
echo "        Top level directory: $TOP_DIR"

unset PYTHONPATH

CONDA_DIR=$TOP_DIR/conda
if [ -d $CONDA_DIR ]; then
	rm -rf $CONDA_DIR
fi
export PATH=$CONDA_DIR/bin:$PATH

sudo apt-get install git mercurial
sudo cp 52-opsis.rules /etc/udev/rules.d/
sudo chmod 644 /etc/udev/rules.d/
sudo udevadm control --reload-rules

wget -c https://repo.continuum.io/miniconda/Miniconda3-latest-Linux-x86_64.sh
chmod a+x Miniconda3-latest-Linux-x86_64.sh
./Miniconda3-latest-Linux-x86_64.sh -p $CONDA_DIR -b

which conda
which pip
which python

conda config --set always_yes yes --set changeps1 no
conda update -q conda
conda config --add channels timvideos

conda install openocd
sudo apt-get install libftdi-dev

sudo apt-get install libusb-dev
pip install pyusb

pip install crcmod

sudo apt-get install libjpeg-dev
pip install pillow

pip install hg+https://bitbucket.org/whitie/python-barcode
pip install git+https://github.com/mithro/hexfile.git

conda install -c https://conda.anaconda.org/m-labs flterm

sudo apt-get install build-essential gcc
UBH=$TOP_DIR/bin/unbind-helper
gcc -std=c11 unbind-helper.c -o $UBH
sudo chmod 755 $UBH
sudo chown root:root $UBH
sudo chmod u+s $UBH
ls -l $UBH

sudo apt-get install inkscape

sudo apt-get install fxload

python opsis_eeprom.py

echo
echo
echo
echo
echo "Setting up Opsis programming tools successful!!!"
echo "\\o/ \\o/"
echo
echo "Before running any more commands, do the following;"
echo "----"
echo "export PATH=$CONDA_DIR/bin:$TOP_DIR/bin:\$PATH"
echo "----"
