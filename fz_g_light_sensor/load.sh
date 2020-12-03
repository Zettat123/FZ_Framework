#!/bin/bash

L_UID=$(id -u)

if [ "$L_UID" -ne "0" ]; then
    echo "You must be uid=0"
    exit 1
fi

module_name="fz_g_light_sensor"

make
insmod ./${module_name}.ko pin=22
chmod 766 /dev/${module_name}
make clean
