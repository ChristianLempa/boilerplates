/**********************************************************************
* Filename    : SevenSegmentDisplay.c
* Description : Control SevenSegmentDisplay by 74HC595
* Author      : www.freenove.com
* modification: 2019/12/27
**********************************************************************/
#include <wiringPi.h>
#include <stdio.h>
#include <wiringShift.h>

#define   dataPin   0   //DS Pin of 74HC595(Pin14)
#define   latchPin  2   //ST_CP Pin of 74HC595(Pin12)
#define   clockPin 3    //CH_CP Pin of 74HC595(Pin11)
//encoding for character 0-F of common anode SevenSegmentDisplay. 
unsigned char num[]={0xc0,0xf9,0xa4,0xb0,0x99,0x92,0x82,0xf8,0x80,0x90,0x88,0x83,0xc6,0xa1,0x86,0x8e};

void _shiftOut(int dPin,int cPin,int order,int val){   
	int i;  
    for(i = 0; i < 8; i++){
        digitalWrite(cPin,LOW);
        if(order == LSBFIRST){
            digitalWrite(dPin,((0x01&(val>>i)) == 0x01) ? HIGH : LOW);
            delayMicroseconds(10);
		}
        else {//if(order == MSBFIRST){
            digitalWrite(dPin,((0x80&(val<<i)) == 0x80) ? HIGH : LOW);
            delayMicroseconds(10);
		}
        digitalWrite(cPin,HIGH);
        delayMicroseconds(10);
	}
}

int main(void)
{
	int i;
	
	printf("Program is starting ...\n");
	
	wiringPiSetup();
	
	pinMode(dataPin,OUTPUT);
	pinMode(latchPin,OUTPUT);
	pinMode(clockPin,OUTPUT);
	while(1){
		for(i=0;i<sizeof(num);i++){
			digitalWrite(latchPin,LOW);
			_shiftOut(dataPin,clockPin,MSBFIRST,num[i]);//Output the figures and the highest level is transfered preferentially. 
			digitalWrite(latchPin,HIGH);
			delay(500);
		}
		for(i=0;i<sizeof(num);i++){
			digitalWrite(latchPin,LOW);
			_shiftOut(dataPin,clockPin,MSBFIRST,num[i] & 0x7f);//Use the "&0x7f" to display the decimal point.
			digitalWrite(latchPin,HIGH);
			delay(500);
		}
	}
	return 0;
}

