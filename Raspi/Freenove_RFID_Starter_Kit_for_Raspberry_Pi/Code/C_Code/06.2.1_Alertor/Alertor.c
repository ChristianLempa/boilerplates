/**********************************************************************
* Filename    : Alertor.c
* Description : Make Alertor with buzzer and button.
* Author      : www.freenove.com
* modification: 2019/12/27
**********************************************************************/
#include <wiringPi.h>
#include <stdio.h>
#include <softTone.h>
#include <math.h>

#define buzzerPin    0  	//define the buzzerPin
#define buttonPin 	 1		//define the buttonPin

void alertor(int pin){
	int x;
	double sinVal, toneVal;
	for(x=0;x<360;x++){ // frequency of the alertor is consistent with the sine wave 
		sinVal = sin(x * (M_PI / 180));		//Calculate the sine value
		toneVal = 2000 + sinVal * 500;		//Add the resonant frequency and weighted sine value 
		softToneWrite(pin,toneVal);			//output corresponding PWM
		delay(1);
	}
}
void stopAlertor(int pin){
	softToneWrite(pin,0);
}
int main(void)
{
	printf("Program is starting ... \n");
	
	wiringPiSetup();
	
	pinMode(buzzerPin, OUTPUT); 
	pinMode(buttonPin, INPUT);
	softToneCreate(buzzerPin); //set buzzerPin
	pullUpDnControl(buttonPin, PUD_UP);  //pull up to HIGH level
	while(1){	
		if(digitalRead(buttonPin) == LOW){ //button is pressed
			alertor(buzzerPin);   // turn on buzzer
			printf("alertor turned on >>> \n");
		}
		else {				//button is released 
			stopAlertor(buzzerPin);   // turn off buzzer
			printf("alertor turned off <<< \n");
		}
	}
	return 0;
}

