#!/usr/bin/env python3
########################################################################
# Filename    : SteppingMotor.py
# Description : Drive SteppingMotor
# Author      : www.freenove.com
# modification: 2023/05/12
########################################################################
from gpiozero import OutputDevice
import time 

motorPins = (18, 23, 24, 25) # define pins connected to four phase ABCD of stepper motor
# motorPins = ("J8:12", "J8:16", "J8:18", "J8:22") # define pins connected to four phase ABCD of stepper motor
motors = list(map(lambda pin: OutputDevice(pin), motorPins))
CCWStep = (0x01,0x02,0x04,0x08) # define power supply order for rotating anticlockwise 
CWStep = (0x08,0x04,0x02,0x01)  # define power supply order for rotating clockwise
     
# as for four phase stepping motor, four steps is a cycle. the function is used to drive the stepping motor clockwise or anticlockwise to take four steps    
def moveOnePeriod(direction,ms):    
    for j in range(0,4,1):      # cycle for power supply order
        for i in range(0,4,1):  # assign to each pin
            if (direction == 1):# power supply order clockwise
                motors[i].on() if (CCWStep[j] == 1<<i) else motors[i].off()
            else :              # power supply order anticlockwise
                motors[i].on() if CWStep[j] == 1<<i else motors[i].off()
        if(ms<3):       # the delay can not be less than 3ms, otherwise it will exceed speed limit of the motor
            ms = 3
        time.sleep(ms*0.001)    
        
# continuous rotation function, the parameter steps specifies the rotation cycles, every four steps is a cycle
def moveSteps(direction, ms, steps):
    for i in range(steps):
        moveOnePeriod(direction, ms)
        
# function used to stop motor
def motorStop():
    for i in range(0,4,1):
        motors.off()    
           
def loop():
    while True:
        moveSteps(0,3,512)  # rotating 360 deg clockwise, a total of 2048 steps in a circle, 512 cycles
        time.sleep(0.5)
        moveSteps(1,3,512)  # rotating 360 deg anticlockwise
        time.sleep(0.5)
    
if __name__ == '__main__':     # Program entrance
    print ('Program is starting...')
    try:
        loop()
    except KeyboardInterrupt:  # Press ctrl-c to end the program.
        print("Ending program")
        