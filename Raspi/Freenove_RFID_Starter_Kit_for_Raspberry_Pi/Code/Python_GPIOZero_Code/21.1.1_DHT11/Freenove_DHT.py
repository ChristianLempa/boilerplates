#!/usr/bin/env python3
#############################################################################
# Filename    : Freenove_DHT.py
# Description : DHT Temperature & Humidity Sensor library for Freenove
# Author      : freenove
# modification: 2024/07/29
########################################################################
import ctypes  
import time

lib_name = '/usr/lib/libdht.so'  # Linux  
lib = ctypes.CDLL(lib_name)  
lib.setDHT11Pin.argtypes = [ctypes.c_int]  
lib.readSensor.argtypes = [ctypes.c_int, ctypes.c_int]  
lib.readSensor.restype = ctypes.c_int  
lib.readDHT11.restype = ctypes.c_int  
lib.getHumidity.restype = ctypes.c_double  
lib.getTemperature.restype = ctypes.c_double  

class DHT(object):
    def __init__(self,pin):
        lib.setDHT11Pin(pin) 
        
    #Read DHT sensor, store the original data in bits[] 
    def readSensor(self,pin,wakeupDelay):
        return lib.readSensor(pin, wakeupDelay)
        
    #Read DHT sensor, analyze the data of temperature and humidity
    def readDHT11(self):
        return lib.readDHT11()
     
    def getHumidity(self):
        return lib.getHumidity()
    
    def getTemperature(self):
        return lib.getTemperature()
        
        
def loop():
    dht = DHT(17)
    time.sleep(1) 
    sumCnt = 0
    okCnt = 0
    while(True):
        sumCnt += 1
        chk = dht.readDHT11()   
        if (chk == 0):
            okCnt += 1      
        okRate = 100.0*okCnt/sumCnt;
        print("sumCnt : %d, \t okRate : %.2f%% "%(sumCnt,okRate))
        print("chk : %d, \t Humidity : %.2f, \t Temperature : %.2f "%(chk,dht.getHumidity(),dht.getTemperature()))
        time.sleep(3)       
        
if __name__ == '__main__':
    print ('Program is starting ... ')
    try:
        loop()
    except KeyboardInterrupt:
        pass
        exit()      
        
        
