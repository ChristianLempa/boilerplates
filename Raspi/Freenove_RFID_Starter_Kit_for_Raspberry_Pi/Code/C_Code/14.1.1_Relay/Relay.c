/**********************************************************************
* Filename    : Relay.c
* Description : Control Motor with Button and Relay 
* Author      : www.freenove.com
* modification: 2019/12/27
**********************************************************************/
#include <wiringPi.h>
#include <stdio.h>

#define relayPin    0  	//define the relayPin
#define buttonPin 1		//define the buttonPin
int relayState=LOW;		//store the State of relay
int buttonState=HIGH;	//store the State of button
int lastbuttonState=HIGH;//store the lastState of button
long lastChangeTime;	//store the change time of button state
long captureTime=50;	//set the button state stable time
int reading;
int main(void)
{
	printf("Program is starting...\n");
	
	wiringPiSetup();	
	
	pinMode(relayPin, OUTPUT); 
	pinMode(buttonPin, INPUT);
	pullUpDnControl(buttonPin, PUD_UP);  //pull up to high level
	while(1){
		reading = digitalRead(buttonPin); //read the current state of button
		if( reading != lastbuttonState){  //if the button state changed ,record the time point
			lastChangeTime = millis();
		}
		//if changing-state of the button last beyond the time we set,we considered that 
		//the current button state is an effective change rather than a buffeting
		if(millis() - lastChangeTime > captureTime){
			//if button state is changed, update the data.
			if(reading != buttonState){
				buttonState = reading;
				//if the state is low, the action is pressing.
				if(buttonState == LOW){
					printf("Button is pressed!\n");
					relayState = !relayState;
					if(relayState){
						printf("turn on relay ...\n");
					}
					else {
						printf("turn off relay ...\n");
					}
				}
				//if the state is high, the action is releasing.
				else {
					printf("Button is released!\n");
				}
			}
		}
		digitalWrite(relayPin,relayState);
		lastbuttonState = reading;
	}

	return 0;
}

