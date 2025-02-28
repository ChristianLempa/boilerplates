#!/bin/sh

current_file=$0
cd "$(dirname "$current_file")"

g++ -fPIC -c ADCDevice.cpp -o ADCDevice.o
g++ -shared -fPIC -o libADCDevice.so ADCDevice.o
sudo cp ADCDevice.hpp /usr/include/
sudo cp libADCDevice.so /usr/lib
sudo ldconfig

echo "build completed!"
