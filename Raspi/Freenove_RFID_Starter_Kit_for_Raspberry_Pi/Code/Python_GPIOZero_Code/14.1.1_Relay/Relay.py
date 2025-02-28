#!/usr/bin/env python3
########################################################################
# Filename    : Relay.py
# Description : Control Relay and Motor via Button 
# Author      : www.freenove.com
# modification: 2023/05/15
########################################################################
from gpiozero import DigitalOutputDevice, Button
import time

relayPin = 17     # define the relayPin
buttonPin = 18    # define the buttonPin
relay = DigitalOutputDevice(relayPin)     # define LED pin according to BCM Numbering
button = Button(buttonPin) # define Button pin according to BCM Numbering

def onButtonPressed():  # When button is pressed, this function will be executed
    relay.toggle()
    if relay.value :
        print("Turn on relay ...")
    else :
        print("Turn off relay ... ")    

def loop():
    button.when_pressed = onButtonPressed
    while True:
        time.sleep(1)
    
def destroy():
    relay.close()
    button.close()

if __name__ == '__main__':     # Program entrance
    print ('Program is starting...')
    try:
        loop()
    except KeyboardInterrupt:   # Press ctrl-c to end the program.
        destroy()
        print("Ending program")