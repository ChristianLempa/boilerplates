/**********************************************************************
* Filename    : Softlight.cpp
* Description : Use potentiometer to control LED
* Author      : www.freenove.com
* modification: 2020/03/07
**********************************************************************/
#include <wiringPi.h>
#include <stdio.h>
#include <softPwm.h>
#include <ADCDevice.hpp>

#define ledRedPin 3         //define 3 pins for RGBLED
#define ledGreenPin 2
#define ledBluePin 0

ADCDevice *adc;  // Define an ADC Device class object

int main(void){
    adc = new ADCDevice();
    printf("Program is starting ... \n");

    if(adc->detectI2C(0x48)){    // Detect the pcf8591.
        delete adc;                // Free previously pointed memory
        adc = new PCF8591();    // If detected, create an instance of PCF8591.
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
    softPwmCreate(ledRedPin,0,100);     //creat 3 PMW output pins for RGBLED
    softPwmCreate(ledGreenPin,0,100);
    softPwmCreate(ledBluePin,0,100);
    while(1){
        int val_Red = adc->analogRead(0);  //read analog value of 3 potentiometers
        int val_Green = adc->analogRead(1);
        int val_Blue = adc->analogRead(2);
        softPwmWrite(ledRedPin,val_Red*100/255);    //map the read value of potentiometers into PWM value and output it
        softPwmWrite(ledGreenPin,val_Green*100/255);
        softPwmWrite(ledBluePin,val_Blue*100/255);
        //print out the read ADC value
        printf("ADC value val_Red: %d  ,\tval_Green: %d  ,\tval_Blue: %d \n",val_Red,val_Green,val_Blue);
        delay(100);
    }
    return 0;
}
