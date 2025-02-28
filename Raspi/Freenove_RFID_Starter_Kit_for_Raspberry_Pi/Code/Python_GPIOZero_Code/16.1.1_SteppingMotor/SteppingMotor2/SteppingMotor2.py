#!/usr/bin/env python3
########################################################################
# Filename    : SteppingMotor.py
# Description : Drive SteppingMotor
# Author      : www.freenove.com
# modification: 2023/05/12
########################################################################
import sys
from time import sleep
from gpiostepper import Stepper

#motorPins = ("J8:12", "J8:16", "J8:18", "J8:22") # define pins connected to four phase ABCD of stepper motor
motorPins = (18, 23, 24, 25) # define pins connected to four phase ABCD of stepper motor
number_of_steps = 32
step_motor = Stepper(motorPins, number_of_steps = number_of_steps)   
speed = 600
amount_of_gear_reduction = 64
number_of_steps_per_revolution_geared_output = number_of_steps * amount_of_gear_reduction
step_motor.set_speed(speed)
def loop():
    while True:
        step_motor.step(number_of_steps_per_revolution_geared_output) # rotating 360 deg clockwise
        sleep(0.5)
        step_motor.step(-number_of_steps_per_revolution_geared_output)# rotating 360 deg anticlockwise
        sleep(0.5)

if __name__ == "__main__":
    print ('Program is starting...')
    try:
        loop()
    except KeyboardInterrupt:  # Press ctrl-c to end the program.
        print("Ending program")
        