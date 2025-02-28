/**********************************************************************
* Filename    : ADCDevice.cpp
* Description : Freenove ADC Module library.
* Author      : www.freenove.com
* modification: 2020/03/06
**********************************************************************/
#include "ADCDevice.hpp"

ADCDevice::ADCDevice(){
    address = 0;
    wiringPiSetup(); //Initialize wiringPi.
}

int ADCDevice::detectI2C(int addr){
    _fd = wiringPiI2CSetup (addr);   
    if (_fd < 0){		
	printf("Error address : 0x%x \n",addr);
	return 0 ;
    } 
    else{	
	if(wiringPiI2CWrite(_fd,0) < 0){
	    printf("Not found device in address 0x%x \n",addr);
	    return 0;
	}
	else{
	    printf("Found device in address 0x%x \n",addr);
	    return 1 ;
	}
    }
}

int ADCDevice::analogRead(int chn){
    printf("Implemented in subclass! \n");
    return 0;
}


PCF8591::PCF8591(int addr)
{
    address = addr;
    cmd = 0x40;		//The default command for PCF8591 is 0x40.
    wiringPiSetup();
    detectI2C(address);
    printf("PCF8591 setup successful! \n");
}
int PCF8591::analogRead(int chn){
    wiringPiI2CWrite(_fd, cmd+chn);
    wiringPiI2CRead(_fd);
    wiringPiI2CWrite(_fd, cmd+chn);
    return wiringPiI2CRead(_fd);
}
int PCF8591::analogWrite(int value){
    return wiringPiI2CWriteReg8(_fd, cmd, value);
}

ADS7830::ADS7830(int addr)
{
    address = addr;
    cmd = 0x84;
    wiringPiSetup();
    detectI2C(address);
    printf("ADS7830 setup successful! \n");
}

int ADS7830::analogRead(int chn){
    wiringPiI2CWrite(_fd, cmd|(((chn<<2 | chn>>1)&0x07)<<4));
    return wiringPiI2CRead(_fd);
}
