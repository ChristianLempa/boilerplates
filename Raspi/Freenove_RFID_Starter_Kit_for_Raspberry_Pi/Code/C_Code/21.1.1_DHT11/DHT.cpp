/**********************************************************************
* Filename    : DHT.hpp
* Description : DHT Temperature & Humidity Sensor library for Raspberry.
                Used for Raspberry Pi.
*				Program transplantation by Freenove.
* Author      : freenove
* modification: 2020/10/16
* Reference   : https://github.com/RobTillaart/Arduino/tree/master/libraries/DHTlib
**********************************************************************/
#include "DHT.hpp"

DHT::DHT(){
    wiringPiSetup();
}
//Function: Read DHT sensor, store the original data in bits[]
// return values:DHTLIB_OK   DHTLIB_ERROR_CHECKSUM  DHTLIB_ERROR_TIMEOUT
int DHT::readSensor(int pin,int wakeupDelay){
	int mask = 0x80;
	int idx = 0;
	int i ;
	int32_t t;
	for (i=0;i<5;i++){
		bits[i] = 0;
	}
	// Clear sda
	pinMode(pin,OUTPUT);
	digitalWrite(pin,HIGH);
	delay(500);
	// Start signal
	digitalWrite(pin,LOW);
	delay(wakeupDelay);
	digitalWrite(pin,HIGH);
	// delayMicroseconds(40);
	pinMode(pin,INPUT);
	
	int32_t loopCnt = DHTLIB_TIMEOUT;
	t = micros();
	// Waiting echo
	while(1){
		if(digitalRead(pin)==LOW){
			break;
		}
		if((micros() - t) > loopCnt){
			return DHTLIB_ERROR_TIMEOUT;
		}
	}
	
	loopCnt = DHTLIB_TIMEOUT;
	t = micros();
	// Waiting echo low level end
	while(digitalRead(pin)==LOW){
		if((micros() - t) > loopCnt){
			return DHTLIB_ERROR_TIMEOUT;
		}
	}
	
	loopCnt = DHTLIB_TIMEOUT;
	t = micros();
	// Waiting echo high level end
	while(digitalRead(pin)==HIGH){
		if((micros() - t) > loopCnt){
			return DHTLIB_ERROR_TIMEOUT;
		}
	}
	for (i = 0; i<40;i++){
		loopCnt = DHTLIB_TIMEOUT;
		t = micros();
		while(digitalRead(pin)==LOW){
			if((micros() - t) > loopCnt)
				return DHTLIB_ERROR_TIMEOUT;
		}
		t = micros();
		loopCnt = DHTLIB_TIMEOUT;
		while(digitalRead(pin)==HIGH){
			if((micros() - t) > loopCnt){
				return DHTLIB_ERROR_TIMEOUT;
			}
		}
		if((micros() - t ) > 60){
			bits[idx] |= mask;
		}
		mask >>= 1;
		if(mask == 0){
			mask = 0x80;
			idx++;
		}
	}
	pinMode(pin,OUTPUT);
	digitalWrite(pin,HIGH);
	//printf("bits:\t%d,\t%d,\t%d,\t%d,\t%d\n",bits[0],bits[1],bits[2],bits[3],bits[4]);
	return DHTLIB_OK;
}
//Function：Read DHT sensor, analyze the data of temperature and humidity
//return：DHTLIB_OK   DHTLIB_ERROR_CHECKSUM  DHTLIB_ERROR_TIMEOUT
int DHT::readDHT11Once(int pin){
	int rv ; 
	uint8_t sum;
	rv = readSensor(pin,DHTLIB_DHT11_WAKEUP);
	if(rv != DHTLIB_OK){
		humidity = DHTLIB_INVALID_VALUE;
		temperature = DHTLIB_INVALID_VALUE;
		return rv;
	}
	humidity = bits[0];
	temperature = bits[2] + bits[3] * 0.1;
	sum = bits[0] + bits[1] + bits[2] + bits[3];
	if(bits[4] != sum)
		return DHTLIB_ERROR_CHECKSUM;
	return DHTLIB_OK;
}

int DHT::readDHT11(int pin){
	int chk = DHTLIB_INVALID_VALUE;
	for (int i = 0; i < 15; i++){
		chk = readDHT11Once(pin);	//read DHT11 and get a return value. Then determine whether data read is normal according to the return value.
		if(chk == DHTLIB_OK){
			return DHTLIB_OK;
		}
		delay(100);
	}
	return chk;
}



