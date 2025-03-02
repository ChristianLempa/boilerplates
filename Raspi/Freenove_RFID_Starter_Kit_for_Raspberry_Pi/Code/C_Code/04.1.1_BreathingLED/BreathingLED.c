/**********************************************************************
* Filename    : BreathingLED.c
* Description : Make breathing LED with PWM
* Author      : www.freenove.com
* modification: 2019/12/27
**********************************************************************/
#include <wiringPi.h>
#include <stdio.h>
#include <softPwm.h>

#define ledPin    1 

void main(void)
{
	int i;
	
	printf("Program is starting ... \n");
	
	wiringPiSetup();	//Initialize wiringPi.
	
	softPwmCreate(ledPin,  0, 100);//Creat SoftPWM pin
	
	while(1){
		for(i=0;i<100;i++){  //make the led brighter
			softPwmWrite(ledPin, i); 
			delay(20);
		}
		delay(300);
		for(i=100;i>=0;i--){  //make the led darker
			softPwmWrite(ledPin, i);
			delay(20);
		}
		delay(300);
	}
}

