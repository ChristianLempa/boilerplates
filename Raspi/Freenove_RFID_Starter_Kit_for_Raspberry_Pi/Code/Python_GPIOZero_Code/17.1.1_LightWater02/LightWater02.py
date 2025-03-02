#!/usr/bin/env python3
#############################################################################
# Filename    : LightWater02.py
# Description : Control LED with 74HC595
# Author      : www.freenove.com
# modification: 2023/05/12
########################################################################
from gpiozero import OutputDevice
import time
# Defines the data bit that is transmitted preferentially in the shiftOut function.
LSBFIRST = 1
MSBFIRST = 2
# define the pins for 74HC595
dataPin   = OutputDevice(17)      # DS Pin of 74HC595(Pin14)
latchPin  = OutputDevice(27)      # ST_CP Pin of 74HC595(Pin12)
clockPin  = OutputDevice(22)      # CH_CP Pin of 74HC595(Pin11)
   
# shiftOut function, use bit serial transmission. 
def shiftOut(order,val):      
    for i in range(0,8):
        clockPin.off()
        if(order == LSBFIRST):
            dataPin.on() if (0x01&(val>>i)==0x01) else dataPin.off()
        elif(order == MSBFIRST):
            dataPin.on() if (0x80&(val<<i)==0x80) else dataPin.off()
        clockPin.on()

def loop():
    while True:
        x=0x01
        for i in range(0,8):
            latchPin.off()# Output low level to latchPin
            shiftOut(LSBFIRST,x) # Send serial data to 74HC595
            latchPin.on()   # Output high level to latchPin, and 74HC595 will update the data to the parallel output port.
            x<<=1 # make the variable move one bit to left once, then the bright LED move one step to the left once.
            time.sleep(0.1)
        x=0x80
        for i in range(0,8):
            latchPin.off()
            shiftOut(LSBFIRST,x)
            latchPin.on()
            x>>=1
            time.sleep(0.1)

def destroy():   
    dataPin.close()
    latchPin.close()
    clockPin.close() 

if __name__ == '__main__': # Program entrance
    print ('Program is starting...' )
    try:
        loop()  
    except KeyboardInterrupt:  # Press ctrl-c to end the program.
        destroy()
        print("Ending program")
