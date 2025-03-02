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
debounceTime = 50

def loop():
    relayState = 0
    lastChangeTime = round(time.time()*1000)
    buttonState = 1
    lastButtonState = 1
    reading = 1
    while True:
        reading = not button.value  
        if reading != lastButtonState :
            lastChangeTime = round(time.time()*1000)
        if ((round(time.time()*1000) - lastChangeTime) > debounceTime):
            if reading != buttonState :
                buttonState = reading;
                if buttonState == 0:
                    print("Button is pressed!")
                    relayState = not relayState
                    if relayState:
                        print("Turn on relay ...")
                    else :
                        print("Turn off relay ... ")
                else :
                    print("Button is released!")
        relay.on() if (relayState==1) else relay.off() 
        lastButtonState = reading # lastButtonState store latest state
    
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
        