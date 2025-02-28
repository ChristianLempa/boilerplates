/**********************************************************************
* Filename    : MatrixKeypad.cpp
* Description : Obtain the key code of 4x4 Matrix Keypad
* Author      : www.freenove.com
* modification: 2019/12/27
**********************************************************************/
#include "Keypad.hpp"
#include <stdio.h>
const byte ROWS = 4; //four rows
const byte COLS = 4; //four columns
char keys[ROWS][COLS] = {  //key code
  {'1','2','3','A'},
  {'4','5','6','B'},
  {'7','8','9','C'},
  {'*','0','#','D'}
};
byte rowPins[ROWS] = {1, 4, 5, 6 }; //define the row pins for the keypad
byte colPins[COLS] = {12,3, 2, 0 }; //define the column pins for the keypad
//create Keypad object
Keypad keypad = Keypad( makeKeymap(keys), rowPins, colPins, ROWS, COLS );

int main(){
    printf("Program is starting ... \n");
    
    wiringPiSetup();
    
	char key = 0;
	keypad.setDebounceTime(50);
    while(1){
        key = keypad.getKey();  //get the state of keys
        if (key){       //if a key is pressed, print out its key code
            printf("You Pressed key :  %c \n",key);
        }
    }
    return 1;
}

