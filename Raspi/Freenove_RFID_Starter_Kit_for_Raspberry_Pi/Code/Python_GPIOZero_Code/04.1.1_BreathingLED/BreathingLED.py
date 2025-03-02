#!/usr/bin/env python3
########################################################################
# Filename    : BreathingLED.py
# Description : Breathing LED
# Author      : www.freenove.com
# modification: 2023/05/11
########################################################################
from gpiozero import PWMLED
import time

led = PWMLED(18 ,initial_value=0 ,frequency=1000)
def loop():
    while True:
        for b in range(0, 101, 1):    # make the led brighter
            led.value = b / 100.0     # set dc value as the duty cycle
            time.sleep(0.01)
        time.sleep(1)
        for b in range(100, -1, -1):  # make the led darker
            led.value = b / 100.0     # set dc value as the duty cycle
            time.sleep(0.01)
        time.sleep(1)
def destroy():
    led.close()
if __name__ == '__main__':     # Program entrance
    print ('Program is starting ... ')
    try:
        loop()
    except KeyboardInterrupt:  # Press ctrl-c to end the program.
        destroy()
        print("Ending program")
