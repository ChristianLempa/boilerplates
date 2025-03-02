/**********************************************************************
* Filename    : Sweep.c
* Description : Servo sweep
* Author      : www.freenove.com
* modification: 2019/12/27
**********************************************************************/
#include <wiringPi.h>
#include <softPwm.h>
#include <stdio.h>
#define OFFSET_MS 3     //Define the unit of servo pulse offset: 0.1ms
#define SERVO_MIN_MS 5+OFFSET_MS        //define the pulse duration for minimum angle of servo
#define SERVO_MAX_MS 25+OFFSET_MS       //define the pulse duration for maximum angle of servo

#define servoPin    1       //define the GPIO number connected to servo
long map(long value,long fromLow,long fromHigh,long toLow,long toHigh){
    return (toHigh-toLow)*(value-fromLow) / (fromHigh-fromLow) + toLow;
}
void servoInit(int pin){        //initialization function for servo PMW pin
    softPwmCreate(pin,  0, 200);
}
void servoWrite(int pin, int angle){    //Specific a certain rotation angle (0-180) for the servo
    if(angle > 180)
        angle = 180;
    if(angle < 0)
        angle = 0;
    softPwmWrite(pin,map(angle,0,180,SERVO_MIN_MS,SERVO_MAX_MS));   
}
void servoWriteMS(int pin, int ms){     //specific the unit for pulse(5-25ms) with specific duration output by servo pin: 0.1ms
    if(ms > SERVO_MAX_MS)
        ms = SERVO_MAX_MS;
    if(ms < SERVO_MIN_MS)
        ms = SERVO_MIN_MS;
    softPwmWrite(pin,ms);
}

int main(void)
{
    int i;
    
    printf("Program is starting ...\n");
    
    wiringPiSetup();    
    servoInit(servoPin);        //initialize PMW pin of servo
    while(1){
        for(i=SERVO_MIN_MS;i<SERVO_MAX_MS;i++){  //make servo rotate from minimum angle to maximum angle
            servoWriteMS(servoPin,i);
            delay(10);
        }
        delay(500);
        for(i=SERVO_MAX_MS;i>SERVO_MIN_MS;i--){  //make servo rotate from maximum angle to minimum angle
            servoWriteMS(servoPin,i);
            delay(10);
        }
        delay(500);
    }
    return 0;
}

