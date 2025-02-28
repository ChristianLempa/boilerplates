/**********************************************************************
* Filename    : Nightlamp.cpp
* Description : Photoresistor control LED
* Author      : www.freenove.com
* modification: 2020/03/09
**********************************************************************/
#include <wiringPi.h>
#include <stdio.h>
#include <softPwm.h>
#include <ADCDevice.hpp>

#define ledPin 0

ADCDevice *adc;  // Define an ADC Device class object

int main(void){
    adc = new ADCDevice();
    printf("Program is starting ... \n");
    
    if(adc->detectI2C(0x48)){    // Detect the pcf8591.
        delete adc;              // Free previously pointed memory
        adc = new PCF8591();     // If detected, create an instance of PCF8591.
    }
    else if(adc->detectI2C(0x4b)){// Detect the ads7830
        delete adc;               // Free previously pointed memory
        adc = new ADS7830();      // If detected, create an instance of ADS7830.
    }
    else{
        printf("No correct I2C address found, \n"
        "Please use command 'i2cdetect -y 1' to check the I2C address! \n"
        "Program Exit. \n");
        return -1;
    } 
    wiringPiSetup();    
    softPwmCreate(ledPin,0,100);    
    while(1){
        int value = adc->analogRead(0);  //read analog value of A0 pin
        softPwmWrite(ledPin,value*100/255);
        float voltage = (float)value / 255.0 * 3.3;  // calculate voltage
        printf("ADC value : %d  ,\tVoltage : %.2fV\n",value,voltage);
        delay(100);
    }
    return 0;
}
