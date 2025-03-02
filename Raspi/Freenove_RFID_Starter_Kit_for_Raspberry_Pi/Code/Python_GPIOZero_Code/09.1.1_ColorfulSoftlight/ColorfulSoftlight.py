#!/usr/bin/env python3
#############################################################################
# Filename    : Softlight.py
# Description : Control RGBLED with Potentiometer 
# Author      : www.freenove.com
# modification: 2023/05/11
########################################################################
from gpiozero import RGBLED
import time
from ADCDevice import *

led = RGBLED(red=22, green=27, blue=17, active_high=False) # define the pins for R:GPIO22,G:GPIO27,B:GPIO17
#led = RGBLED(red="J8:15", green="J8:13", blue="J8:11") # according to BOARD Numbering define the pins for R:11,G:12,B:13 
adc = ADCDevice() # Define an ADCDevice class object

def setup():
    global adc
    if(adc.detectI2C(0x48)): # Detect the pcf8591.
        adc = PCF8591()
    elif(adc.detectI2C(0x4b)): # Detect the ads7830
        adc = ADS7830()
    else:
        print("No correct I2C address found, \n"
        "Please use command 'i2cdetect -y 1' to check the I2C address! \n"
        "Program Exit. \n");
        exit(-1)
    
def loop():
    while True:     
        value_Red = adc.analogRead(0)       # read ADC value of 3 potentiometers
        value_Green = adc.analogRead(1)
        value_Blue = adc.analogRead(2)
        led.red   =value_Red/255  # map the read value of potentiometers into PWM value and output it 
        led.green =value_Green/255
        led.blue  =value_Blue/255
        # print read ADC value
        print ('ADC Value value_Red: %d ,\tvlue_Green: %d ,\tvalue_Blue: %d'%(value_Red,value_Green,value_Blue))
        time.sleep(0.01)

def destroy():
    adc.close()
    led.close()
    
if __name__ == '__main__': # Program entrance
    print ('Program is starting ... ')
    setup()
    try:
        loop()
    except KeyboardInterrupt: # Press ctrl-c to end the program.
        destroy()
        print("Ending program")
