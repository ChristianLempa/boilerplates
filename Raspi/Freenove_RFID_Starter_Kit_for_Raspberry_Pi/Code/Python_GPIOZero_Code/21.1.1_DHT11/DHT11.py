#!/usr/bin/env python3
#############################################################################
# Filename    : DHT11.py
# Description :	read the temperature and humidity data of DHT11
# Author      : freenove
# modification: 2024/07/29
########################################################################
import time
from Freenove_DHT import DHT      

DHTPin = 17     #define the pin of DHT11

def loop():
    dht = DHT(DHTPin)
    time.sleep(1) 
    counts = 0     # Measurement counts
    while(True):
        counts += 1
        print("Measurement counts: ", counts)
        for i in range(0,15):            
            chk = dht.readDHT11()     #read DHT11 and get a return value. Then determine whether data read is normal according to the return value.
            if (chk == 0):      #read DHT11 and get a return value. Then determine whether data read is normal according to the return value.
                print("DHT11,OK!")
                break
            time.sleep(0.1)
           
        print("Humidity : %.2f, \t Temperature : %.2f \n"%(dht.getHumidity(),dht.getTemperature()))
        time.sleep(2)   
        
if __name__ == '__main__':
    print ('Program is starting ... ')
    try:
        loop()
    except KeyboardInterrupt:
        pass
        exit()   