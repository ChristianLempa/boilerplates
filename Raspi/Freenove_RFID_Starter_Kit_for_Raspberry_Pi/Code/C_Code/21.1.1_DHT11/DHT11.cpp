
/**********************************************************************
* Filename    : DHT11.cpp
* Description : Read the temperature and humidity data of DHT11
* Author      : www.freenove.com
* modification: 2020/10/16
**********************************************************************/
#include <wiringPi.h>
#include <stdio.h>
#include <stdint.h>
#include "DHT.hpp"

#define DHT11_Pin  0		//define the pin of sensor

int main(){
    DHT dht;			//create a DHT class object
    int chk, counts;		//chk:read the return value of sensor; sumCnt:times of reading sensor

    printf("Program is starting ...\n");

    while (1){
        counts++; //counting number of reading times
        printf("Measurement counts : %d \n", counts);
        for (int i = 0; i < 15; i++){
            chk = dht.readDHT11(DHT11_Pin);	//read DHT11 and get a return value. Then determine whether data read is normal according to the return value.
            if(chk == DHTLIB_OK){
                printf("DHT11,OK! \n");
                break;
            }
            delay(100);
        }
        printf("Humidity is %.2f %%, \t Temperature is %.2f *C\n\n",dht.humidity, dht.temperature);
        delay(2000);
    }
    return 1;
}
