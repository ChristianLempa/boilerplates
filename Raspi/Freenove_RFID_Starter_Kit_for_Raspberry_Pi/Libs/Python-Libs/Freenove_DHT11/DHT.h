/**********************************************************************
* Filename    : DHT.h
* Description : DHT Temperature & Humidity Sensor library for Raspberry.
                Used for Raspberry Pi.
*				Program transplantation by Freenove.
* Author      : Zhentao Lin
* modification: 2024/7/27
* Reference   : https://github.com/RobTillaart/Arduino/tree/master/libraries/DHTlib
**********************************************************************/
// DHT.h 
#ifndef DHT_H 
#define DHT_H  

#include <wiringPi.h>
#include <stdio.h>
#include <stdint.h>

#define DHTLIB_OK               0
#define DHTLIB_ERROR_CHECKSUM   -1
#define DHTLIB_ERROR_TIMEOUT    -2
#define DHTLIB_INVALID_VALUE    -999
#define DHTLIB_DHT11_WAKEUP     18
#define DHTLIB_DHT_WAKEUP       1
#define DHTLIB_TIMEOUT          100

void setDHT11Pin(int pin);
int readSensor(int pin, int wakeupDelay); 
int readDHT11(void);  
double getHumidity(void);  
double getTemperature(void);  
  



  
#endif