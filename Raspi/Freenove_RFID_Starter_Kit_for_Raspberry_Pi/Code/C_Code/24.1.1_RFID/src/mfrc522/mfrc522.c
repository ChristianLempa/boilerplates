/**	
 * |----------------------------------------------------------------------
 * | Copyright (C) Tilen Majerle, 2014
 * | 
 * | This program is free software: you can redistribute it and/or modify
 * | it under the terms of the GNU General Public License as published by
 * | the Free Software Foundation, either version 3 of the License, or
 * | any later version.
 * |  
 * | This program is distributed in the hope that it will be useful,
 * | but WITHOUT ANY WARRANTY; without even the implied warranty of
 * | MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * | GNU General Public License for more details.
 * | 
 * | You should have received a copy of the GNU General Public License
 * | along with this program.  If not, see <http://www.gnu.org/licenses/>.
 * |----------------------------------------------------------------------
 */
#include "mfrc522.h"
#include <stdint.h>
#include <wiringPi.h>
/* HAL prototypes*/
void MFRC522_HAL_init(void);
void MFRC522_HAL_write(unsigned char addr, unsigned char val);
unsigned char MFRC522_HAL_read(unsigned char addr);
void MFRC522_HAL_Delay(unsigned int ms);

/* HAL prototypes end */
static int Checking_Card = 0;

int MFRC522_Setup(char Type){
	wiringPiSetup();
	pinMode(6,OUTPUT);
	digitalWrite(6,HIGH);
	MFRC522_Reset();
	MFRC522_HAL_Delay(200);

	MFRC522_WriteRegister(MFRC522_REG_T_PRESCALER, 0x3E);
//#define NOTEST
#ifndef NOTEST
	{
		/* test read and write reg functions */
		volatile char test;
		test = MFRC522_ReadRegister(MFRC522_REG_T_PRESCALER);
		if (test != 0x3E) {
			return -1;
		}
	}
#endif
	MFRC522_WriteRegister(MFRC522_REG_T_MODE, 0x8D);
	MFRC522_WriteRegister(MFRC522_REG_T_PRESCALER, 0x3E);
	MFRC522_WriteRegister(MFRC522_REG_T_RELOAD_L, 30);
	MFRC522_WriteRegister(MFRC522_REG_T_RELOAD_H, 0);
	MFRC522_WriteRegister(MFRC522_REG_TX_AUTO, 0x40);
	MFRC522_WriteRegister(MFRC522_REG_MODE, 0x3D);
	
	if (Type == 'A') {
		MFRC522_ClearBitMask(MFRC522_REG_STATUS2, 0x08);
		MFRC522_WriteRegister(MFRC522_REG_MODE, 0x3D);
		MFRC522_WriteRegister(MFRC522_REG_RX_SELL, 0x86);
		MFRC522_WriteRegister(MFRC522_REG_RF_CFG, 0x7F);
		MFRC522_WriteRegister(MFRC522_REG_T_RELOAD_L, 30);
		MFRC522_WriteRegister(MFRC522_REG_T_RELOAD_H, 0);
		MFRC522_WriteRegister(MFRC522_REG_T_MODE, 0x8D);
		MFRC522_WriteRegister(MFRC522_REG_T_PRESCALER, 0x3E);
	}
	MFRC522_AntennaOn();		//Open the antenna
	return 0;
}
int MFRC522_Init(char Type) {

	MFRC522_HAL_init();

	return MFRC522_Setup(Type);
}

MFRC522_Status_t MFRC522_Check(uint8_t* id) {
	MFRC522_Status_t status;
	/* Must Clear Bit MFCrypto1On in Status2 reg in order to return to the card detect mode*/
	MFRC522_ClearBitMask(MFRC522_REG_STATUS2,(1<<3));
	Checking_Card = 1;
	//Find cards, return card type
	status = MFRC522_Request(PICC_CMD_WUPA, id);
	Checking_Card = 0;
	if (status == MI_OK) {
		//Card detected
		//Anti-collision, return card serial number 4 bytes
		status = MFRC522_Anticoll(id);
	}
	return status;
}

MFRC522_Status_t MFRC522_Compare(uint8_t* CardID, uint8_t* CompareID) {
	uint8_t i;
	for (i = 0; i < 5; i++) {
		if (CardID[i] != CompareID[i]) {
			return MI_ERR;
		}
	}
	return MI_OK;
}

void MFRC522_WriteRegister(uint8_t addr, uint8_t val) {
	MFRC522_HAL_write(addr, val);
}

uint8_t MFRC522_ReadRegister(uint8_t addr) {
	return MFRC522_HAL_read(addr);
}

void MFRC522_SetBitMask(uint8_t reg, uint8_t mask) {
	MFRC522_WriteRegister(reg, MFRC522_ReadRegister(reg) | mask);
}

void MFRC522_ClearBitMask(uint8_t reg, uint8_t mask) {
	MFRC522_WriteRegister(reg, MFRC522_ReadRegister(reg) & (~mask));
}

void MFRC522_AntennaOn(void) {
	uint8_t temp;

	temp = MFRC522_ReadRegister(MFRC522_REG_TX_CONTROL);
	if (!(temp & 0x03)) {
		MFRC522_SetBitMask(MFRC522_REG_TX_CONTROL, 0x03);
	}
}

void MFRC522_AntennaOff(void) {
	MFRC522_ClearBitMask(MFRC522_REG_TX_CONTROL, 0x03);
}

void MFRC522_Reset(void) {
	MFRC522_WriteRegister(MFRC522_REG_COMMAND, PCD_RESETPHASE);
}

MFRC522_Status_t MFRC522_Request(uint8_t reqMode, uint8_t* TagType) {
	MFRC522_Status_t status;
	uint16_t backBits;			//The received data bits

	MFRC522_WriteRegister(MFRC522_REG_BIT_FRAMING, 0x07);//TxLastBists = BitFramingReg[2..0]	???

	TagType[0] = reqMode;
	
	status = MFRC522_ToCard(PCD_TRANSCEIVE, TagType, 1, TagType, &backBits);
	
	if ((status != MI_OK)) {
		return status;
	}
	if (backBits != 0x10) {
		return MI_ERR;
	}
	return MI_OK;
}

MFRC522_Status_t MFRC522_ToCard(uint8_t command, uint8_t* sendData,
		uint8_t sendLen, uint8_t* backData, uint16_t* backLen) {
	MFRC522_Status_t status = MI_ERR;
	uint8_t irqEn = 0x00;
	uint8_t waitIRq = 0x00;
	uint8_t lastBits;
	uint8_t n;
	uint16_t i;

	switch (command) {
	case PCD_AUTHENT: {
		irqEn = 0x12;
		waitIRq = 0x10;
		break;
	}
	case PCD_TRANSCEIVE: {
		irqEn = 0x77;
		waitIRq = 0x30;
		break;
	}
	default:
		break;
	}

	MFRC522_WriteRegister(MFRC522_REG_COMM_IE_N, irqEn | 0x80);
	MFRC522_ClearBitMask(MFRC522_REG_COMM_IRQ, 0x80);
	MFRC522_SetBitMask(MFRC522_REG_FIFO_LEVEL, 0x80);

	MFRC522_WriteRegister(MFRC522_REG_COMMAND, PCD_IDLE);

	//Writing data to the FIFO
	for (i = 0; i < sendLen; i++) {
		MFRC522_WriteRegister(MFRC522_REG_FIFO_DATA, sendData[i]);
	}

	//Execute the command
	MFRC522_WriteRegister(MFRC522_REG_COMMAND, command);
	if (command == PCD_TRANSCEIVE) {
		MFRC522_SetBitMask(MFRC522_REG_BIT_FRAMING, 0x80);//StartSend=1,transmission of data starts
	}

	//Waiting to receive data to complete
	i = 2000;//i according to the clock frequency adjustment, the operator M1 card maximum waiting time 25ms???
	do {
		//CommIrqReg[7..0]
		//Set1 TxIRq RxIRq IdleIRq HiAlerIRq LoAlertIRq ErrIRq TimerIRq
		if (Checking_Card) {
			MFRC522_HAL_Delay(16);
		} else {
			MFRC522_HAL_Delay(20);
		}
		n = MFRC522_ReadRegister(MFRC522_REG_COMM_IRQ);
		i--;
	} while ((i != 0) && !(n & 0x01) && !(n & waitIRq));

	MFRC522_ClearBitMask(MFRC522_REG_BIT_FRAMING, 0x80);		//StartSend=0
	
	if (i != 0) {
		if (!(MFRC522_ReadRegister(MFRC522_REG_ERROR) & 0x1B)) {

			if (n & irqEn & 0x01) {
				status = MI_NOTAGERR;
			} else {
				status = MI_OK;
			}

			if (command == PCD_TRANSCEIVE) {
				n = MFRC522_ReadRegister(MFRC522_REG_FIFO_LEVEL);
				lastBits = MFRC522_ReadRegister(MFRC522_REG_CONTROL) & 0x07;
				if (lastBits) {
					*backLen = (n - 1) * 8 + lastBits;
				} else {
					*backLen = n * 8;
				}

				if (n == 0) {
					n = 1;
				}
				if (n > MFRC522_MAX_LEN) {
					n = MFRC522_MAX_LEN;
				}

				//Reading the received data in FIFO
				for (i = 0; i < n; i++) {
					backData[i] = MFRC522_ReadRegister(MFRC522_REG_FIFO_DATA);
				}
			}
		} else {
			status = MI_ERR;
		}
	}

	return status;
}

MFRC522_Status_t MFRC522_Anticoll(uint8_t* serNum) {
	MFRC522_Status_t status;
	uint8_t i;
	uint8_t serNumCheck = 0;
	uint16_t unLen;

	MFRC522_WriteRegister(MFRC522_REG_BIT_FRAMING, 0x00);//TxLastBists = BitFramingReg[2..0]

	serNum[0] = PICC_ANTICOLL;
	serNum[1] = 0x20;
	status = MFRC522_ToCard(PCD_TRANSCEIVE, serNum, 2, serNum, &unLen);

	if (status == MI_OK) {
		//Check card serial number
		for (i = 0; i < 4; i++) {
			serNumCheck ^= serNum[i];
		}
		/* check sum with last byte*/
		if (serNumCheck != serNum[i]) {
			status = MI_ERR;
		}
	}
	return status;
}

void MFRC522_CalculateCRC(uint8_t* pIndata, uint8_t len, uint8_t* pOutData) {
	uint8_t i, n;

	MFRC522_ClearBitMask(MFRC522_REG_DIV_IRQ, 0x04);			//CRCIrq = 0
	MFRC522_SetBitMask(MFRC522_REG_FIFO_LEVEL, 0x80);	//Clear the FIFO pointer
	//Write_MFRC522(CommandReg, PCD_IDLE);

	//Writing data to the FIFO	
	for (i = 0; i < len; i++) {
		MFRC522_WriteRegister(MFRC522_REG_FIFO_DATA, *(pIndata + i));
	}
	MFRC522_WriteRegister(MFRC522_REG_COMMAND, PCD_CALCCRC);

	//Wait CRC calculation is complete
	i = 0xFF;
	do {
		n = MFRC522_ReadRegister(MFRC522_REG_DIV_IRQ);
		i--;
	} while ((i != 0) && !(n & 0x04));			//CRCIrq = 1

	//Read CRC calculation result
	pOutData[0] = MFRC522_ReadRegister(MFRC522_REG_CRC_RESULT_L);
	pOutData[1] = MFRC522_ReadRegister(MFRC522_REG_CRC_RESULT_M);
}

uint8_t MFRC522_SelectTag(uint8_t* serNum) {
	uint8_t i;
	MFRC522_Status_t status;
	uint8_t size;
	uint16_t recvBits;
	uint8_t buffer[32] = "";

	buffer[0] = PICC_SElECTTAG;
	buffer[1] = 0x70;
	for (i = 0; i < 5; i++) {
		buffer[i + 2] = *(serNum + i);
	}
	MFRC522_CalculateCRC(buffer, 7, &buffer[7]);	//Fill [7:8] with 2byte CRC
	status = MFRC522_ToCard(PCD_TRANSCEIVE, buffer, 9, buffer, &recvBits);

	if ((status == MI_OK) && (recvBits == 0x18)) {
		size = buffer[0];
	} else {
		size = 0;
	}

	return size;
}

MFRC522_Status_t MFRC522_Auth(uint8_t authMode, uint8_t BlockAddr,
		uint8_t* Sectorkey, uint8_t* serNum) {
	MFRC522_Status_t status;
	uint16_t recvBits;
	uint8_t i;
	uint8_t buff[12];

	//Verify the command block address + sector + password + card serial number
	buff[0] = authMode;
	buff[1] = BlockAddr;
	for (i = 0; i < 6; i++) {
		buff[i + 2] = *(Sectorkey + i);
	}
	for (i = 0; i < 4; i++) {
		buff[i + 8] = *(serNum + i);
	}
	status = MFRC522_ToCard(PCD_AUTHENT, buff, 12, buff, &recvBits);

	if ((status != MI_OK)
			|| (!(MFRC522_ReadRegister(MFRC522_REG_STATUS2) & 0x08))) {
		status = MI_ERR;
	}

	return status;
}

MFRC522_Status_t MFRC522_Read(uint8_t blockAddr, uint8_t* recvData) {
	MFRC522_Status_t status;
	uint16_t unLen;

	recvData[0] = PICC_READ;
	recvData[1] = blockAddr;
	MFRC522_CalculateCRC(recvData, 2, &recvData[2]);
	status = MFRC522_ToCard(PCD_TRANSCEIVE, recvData, 4, recvData, &unLen);

	if ((status != MI_OK) || (unLen != 0x90)) {
		return MI_ERR;
	}

	return unLen;
}

MFRC522_Status_t MFRC522_Write(uint8_t blockAddr, uint8_t* writeData) {
	MFRC522_Status_t status;
	uint16_t recvBits;
	uint8_t i;
	uint8_t buff[18];

	buff[0] = PICC_WRITE;
	buff[1] = blockAddr;
	MFRC522_CalculateCRC(buff, 2, &buff[2]);
	status = MFRC522_ToCard(PCD_TRANSCEIVE, buff, 4, buff, &recvBits);

	if ((status != MI_OK) || (recvBits != 4) || ((buff[0] & 0x0F) != 0x0A)) {
		goto ERROR;
	}

	if (status == MI_OK) {
		//Data to the FIFO write 16Byte
		for (i = 0; i < 16; i++) {
			buff[i] = *(writeData + i);
		}
		MFRC522_CalculateCRC(buff, 16, &buff[16]);
		status = MFRC522_ToCard(PCD_TRANSCEIVE, buff, 18, buff, &recvBits);

		if ((status != MI_OK) || (recvBits != 4)
				|| ((buff[0] & 0x0F) != 0x0A)) {
				goto ERROR;

		}
	}
	return MI_OK;

	ERROR:
	if (recvBits == 4) {
		status = buff[0] & 0x0F;
	} else {
		status = MI_ERR;
	}
	return status;
}

void MFRC522_Halt(void) {
	uint16_t unLen;
	uint8_t buff[4];

	buff[0] = PICC_HALT;
	buff[1] = 0;
	MFRC522_CalculateCRC(buff, 2, &buff[2]);

	MFRC522_ToCard(PCD_TRANSCEIVE, buff, 4, buff, &unLen);

}
void MFRC522_WakeUp(void){
	uint16_t unLen;
	uint8_t buff[4];

	buff[0] = PICC_HALT;
	buff[1] = 0;
	MFRC522_CalculateCRC(buff, 2, &buff[2]);

	MFRC522_ToCard(PCD_TRANSCEIVE, buff, 4, buff, &unLen);
}
char *PICC_TYPE_STRING[] = { "PICC_TYPE_NOT_COMPLETE", "PICC_TYPE_MIFARE_MINI",
		"PICC_TYPE_MIFARE_1K", "PICC_TYPE_MIFARE_4K", "PICC_TYPE_MIFARE_UL",
		"PICC_TYPE_MIFARE_PLUS", "PICC_TYPE_TNP3XXX", "PICC_TYPE_ISO_14443_4",
		"PICC_TYPE_ISO_18092", "PICC_TYPE_UNKNOWN" };
char *MFRC522_TypeToString(PICC_TYPE_t type) {
	return PICC_TYPE_STRING[type];
}
int MFRC522_ParseType(uint8_t TagSelectRet) {
	if (TagSelectRet & 0x04) { // UID not complete
		return PICC_TYPE_NOT_COMPLETE;
	}

	switch (TagSelectRet) {
	case 0x09:
		return PICC_TYPE_MIFARE_MINI;
		break;
	case 0x08:
		return PICC_TYPE_MIFARE_1K;
		break;
	case 0x18:
		return PICC_TYPE_MIFARE_4K;
		break;
	case 0x00:
		return PICC_TYPE_MIFARE_UL;
		break;
	case 0x10:
	case 0x11:
		return PICC_TYPE_MIFARE_PLUS;
		break;
	case 0x01:
		return PICC_TYPE_TNP3XXX;
		break;
	default:
		break;
	}

	if (TagSelectRet & 0x20) {
		return PICC_TYPE_ISO_14443_4;
	}

	if (TagSelectRet & 0x40) {
		return PICC_TYPE_ISO_18092;
	}

	return PICC_TYPE_UNKNOWN;
}
