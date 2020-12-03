#!/bin/bash

if [ "$L_UID" -ne "0" ]; then
    echo "You must be uid=0"
    exit 1
fi

module_name="fz_g_dht11"

make
insmod ./${module_name}.ko pin=17 threshold=50
chmod 766 /dev/${module_name}
make clean
