#!/bin/bash

L_UID=$(id -u)

if [ "$L_UID" -ne "0" ]; then
    echo "You must be uid=0"
    exit 1
fi

module_name="fz_g_remote_dev"

if [ ! -e "/dev/$module_name" ]; then
  echo "No module: $module_name"
else
  rmmod ${module_name}
  echo "Module: $module_name has been removed"
fi

make
insmod ./${module_name}.ko device_number=3
chmod 766 /dev/${module_name}
make clean