#!/usr/bin/env python3
########################################################################
# Filename    : Blink.py
# Description : Basic usage of GPIO. Let led blink.
# auther      : www.freenove.com
# modification: 2023/05/11
########################################################################
from gpiozero import LED
from time import sleep

led = LED(17)           # define LED pin according to BCM Numbering
#led = LED("J8:11")     # BOARD Numbering
'''
# pins numbering, the following lines are all equivalent
led = LED(17)           # BCM
led = LED("GPIO17")     # BCM
led = LED("BCM17")      # BCM
led = LED("BOARD11")    # BOARD
led = LED("WPI0")       # WiringPi
led = LED("J8:11")      # BOARD
'''
def loop():
    while True:
        led.on()    # turn on LED
        print ('led turned on >>>')  # print message on terminal
        sleep(1)    # wait 1 second
        led.off()   # turn off LED 
        print ('led turned off <<<') # print message on terminal
        sleep(1)    # wait 1 second

if __name__ == '__main__':    # Program entrance
    print ('Program is starting ... \n')
    try:
        loop()
    except KeyboardInterrupt:  # Press ctrl-c to end the program.
        print("Ending program")
