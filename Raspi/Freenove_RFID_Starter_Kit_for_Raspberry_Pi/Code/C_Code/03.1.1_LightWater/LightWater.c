/**********************************************************************
* Filename    : LightWater.c
* Description : Use LEDBar Graph(10 LED) 
* Author      : www.freenove.com
* modification: 2019/12/27
**********************************************************************/
#include <wiringPi.h>
#include <stdio.h>

#define ledCounts 10
int pins[ledCounts] = {0,1,2,3,4,5,6,8,9,10};

void main(void)
{
	int i;
	printf("Program is starting ... \n");
	
	wiringPiSetup(); //Initialize wiringPi.
	
	for(i=0;i<ledCounts;i++){       //Set pinMode for all led pins to output
		pinMode(pins[i], OUTPUT);		
	}
	while(1){
		for(i=0;i<ledCounts;i++){   // move led(on) from left to right
			digitalWrite(pins[i],LOW);
			delay(100);
			digitalWrite(pins[i],HIGH);
		}
		for(i=ledCounts-1;i>-1;i--){   // move led(on) from right to left
			digitalWrite(pins[i],LOW);
			delay(100);
			digitalWrite(pins[i],HIGH);
		}
	}
}

