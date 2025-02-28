#!/usr/bin/env python3
########################################################################
# Filename    : ColorfulLED.py
# Description : Random color change ColorfulLED
# Author      : www.freenove.com
# modification: 2023/05/11
########################################################################
from gpiozero import RGBLED
import time
import random

#led = RGBLED(red="J8:11", green="J8:12", blue="J8:13", active_high=False) # define the pins for R:11,G:12,B:13
led = RGBLED(red=17, green=18, blue=27, active_high=False) # define the pins for R:GPIO17,G:GPIO18,B:GPIO27 
# If your RGBLED is a common cathode LED, set active_high to True

def setColor(r_val,g_val,b_val):      # change duty cycle for three pins to r_val,g_val,b_val
    led.red=r_val/100                 # change pwmRed duty cycle to r_val
    led.green = g_val/100             # change pwmRed duty cycle to r_val
    led.blue = b_val/100              # change pwmRed duty cycle to r_val

def loop():
    while True :
        r=random.randint(0,100)  #get a random in (0,100)
        g=random.randint(0,100)
        b=random.randint(0,100)
        setColor(r,g,b)          #set random as a duty cycle value 
        print ('r=%d, g=%d, b=%d ' %(r ,g, b))
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