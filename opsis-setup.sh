#!/bin/bash

CALLED=$_
[[ "${BASH_SOURCE[0]}" != "${0}" ]] && SOURCED=1 || SOURCED=0

SETUP_SRC=$(realpath ${BASH_SOURCE[0]})
SETUP_DIR=$(dirname $SETUP_SRC)
TOP_DIR=$(realpath $SETUP_DIR)

set -e

if [ $SOURCED = 1 ]; then
        echo "You must run this script, rather then try to source it."
        echo "$SETUP_SRC"
        return
fi

echo "             This script is: $SETUP_SRC"
echo "        Top level directory: $TOP_DIR"

unset PYTHONPATH

# Check the build dir
if [ ! -d $BUILD_DIR ]; then
        mkdir -p $BUILD_DIR
fi

CONDA_DIR=$TOP_DIR/conda
if [ -d $CONDA_DIR ]; then
	rm -rf $CONDA_DIR
fi
export PATH=$CONDA_DIR/bin:$PATH

sudo apt-get install libusb-dev

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
pip install pyusb
pip install code128
pip install crcmod

python opsis_eeprom.py

echo "Run"
echo "----"
echo "export PATH=$CONDA_DIR/bin:\$PATH"
echo "----"
