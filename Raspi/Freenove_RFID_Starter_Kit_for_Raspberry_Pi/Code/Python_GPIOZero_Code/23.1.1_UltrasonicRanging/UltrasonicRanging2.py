#!/usr/bin/env python3
########################################################################
# Filename    : UltrasonicRanging.py
# Description : Get distance via UltrasonicRanging sensor
# auther      : www.freenove.com
# modification: 2023/05/13
########################################################################
import os
os.system("sudo pigpiod")
from gpiozero import DistanceSensor
from gpiozero.pins.pigpio import PiGPIOFactory
from time import sleep

trigPin = 23
echoPin = 24
my_factory = PiGPIOFactory() 
sensor = DistanceSensor(echo=echoPin, trigger=trigPin ,max_distance=3,pin_factory=my_factory)

def loop():
    while True:
        print('Distance: ', sensor.distance * 100,'cm')
        sleep(1)
        
if __name__ == '__main__':     # Program entrance
    print ('Program is starting...')
    try:
        loop()
    except KeyboardInterrupt:  # Press ctrl-c to end the program.
        sensor.close()
        os.system("sudo killall pigpiod")
        print("Ending program")
        
        