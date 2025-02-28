#!/usr/bin/env python3
#############################################################################
# Filename    : Motor.py
# Description : Control Motor with L293D
# Author      : www.freenove.com
# modification: 2023/05/11
########################################################################
from gpiozero import DigitalOutputDevice,PWMOutputDevice
import time
from ADCDevice import *

# define the pins connected to L293D
motoRPin1 = DigitalOutputDevice(27)           # define L293D pin according to BCM Numbering
motoRPin2 = DigitalOutputDevice(17)           # define L293D pin according to BCM Numbering
enablePin = PWMOutputDevice(22,frequency=1000)
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
# mapNUM function: map the value from a range of mapping to another range.
def mapNUM(value,fromLow,fromHigh,toLow,toHigh):
    return (toHigh-toLow)*(value-fromLow) / (fromHigh-fromLow) + toLow

# motor function: determine the direction and speed of the motor according to the input ADC value input
def motor(ADC):
    value = ADC -128
    if (value > 0):  # make motor turn forward
        motoRPin1.on()        # motoRPin1 output HIHG level
        motoRPin2.off()       # motoRPin2 output LOW level
        print ('Turn Forward...')
    elif (value < 0): # make motor turn backward
        motoRPin1.off() 
        motoRPin2.on()
        print ('Turn Backward...')
    else :
        motoRPin1.off()
        motoRPin2.off()
        print ('Motor Stop...')
    b=mapNUM(abs(value),0,128,0,100)
    enablePin.value = b / 100.0     # set dc value as the duty cycle
    print ('The PWM duty cycle is %d%%\n'%(abs(value)*100/127))   # print PMW duty cycle.

def loop():
    while True:
        value = adc.analogRead(0) # read ADC value of channel 0
        print ('ADC Value : %d'%(value))
        motor(value)
        time.sleep(0.2)

def destroy():
    motoRPin1.close()          
    motoRPin2.close()        
    enablePin.close()
    adc.close()

if __name__ == '__main__':  # Program entrance
    print ('Program is starting ... ')
    setup()
    try:
        loop()
    except KeyboardInterrupt: # Press ctrl-c to end the program.
        destroy()
        print("Ending program")
