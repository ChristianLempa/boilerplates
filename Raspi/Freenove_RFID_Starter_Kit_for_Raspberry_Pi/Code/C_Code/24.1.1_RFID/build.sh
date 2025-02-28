#!/bin/sh

#sudo gcc src/dump/*.c src/AES_128/*.c src/mfrc522/*.c *.c -I include -o RFID
sudo gcc src/*/*.c *.c -I include -lwiringPi -o RFID

echo "Build finished!"