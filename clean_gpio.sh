#!/bin/bash

echo "Melepaskan semua pin GPIO (0-27)..."

for pin in {0..27}
do
    # ip = input (mode paling aman)
    # pn = pull none (mematikan pull-up/down internal)
    /usr/bin/pinctrl set $pin ip pn
done

echo "Selesai! Semua pin sekarang dalam kondisi High-Impedance (Input)."
pinctrl
