/*
 * main.c
 *	Origin: 
 * 		From:	https://github.com/weiche/RC522 * 	
 * This:
 * 		Project			: RFID-MFRC522
 * 		Description		: Use MFRC522 Read and Write Mifare Card.
 * 		Author			: www.freenove.com
 * 		Date			: 2021/1/1
 */

#include <stdio.h>
#include <stdint.h>
#include <unistd.h>
#include <string.h>
#include <getopt.h>
#include <stdlib.h>
#include "mfrc522.h"
#define DISP_COMMANDLINE()	printf("RC522>")

int scan_loop(uint8_t *CardID);
int tag_select(uint8_t *CardID);

int main(int argc, char **argv) {
	MFRC522_Status_t ret;
	//Recognized card ID
	uint8_t CardID[5] = { 0x00, };
	uint8_t tagType[16] = {0x00,};
	static char command_buffer[1024];

	ret = MFRC522_Init('B');
	if (ret < 0) {
		printf("Failed to initialize.\r\nProgram exit.\r\n");
		exit(-1);
	}

	printf("User Space RC522 Application\r\n");

	while (1) {
		/*Main Loop Start*/
		DISP_COMMANDLINE();

		scanf("%s", command_buffer);
		if (strcmp(command_buffer, "scan") == 0) {
			puts("Scanning ... ");
			while (1) {
				ret = MFRC522_Request(PICC_REQIDL, tagType);
				if (ret == MI_OK) {
					printf("Card detected!\r\n");	
					ret = MFRC522_Anticoll(CardID);	
					if(ret == MI_OK){
						ret = tag_select(CardID);
						if (ret == MI_OK) {
							ret = scan_loop(CardID);
							if (ret < 0) {
								printf("Card error...\r\n");
								break;
							} else if (ret == 1) {
								puts("Halt...\r\n");
								break;
							}
						}
					}
					else{
						printf("Get Card ID failed!\r\n");
					}								
				}
				MFRC522_Halt();
			}
			MFRC522_Halt();
			MFRC522_Init('B');
		} else if (strcmp(command_buffer, "quit") == 0
				|| strcmp(command_buffer, "exit") == 0) {
			return 0;
		} else {
			puts("Unknown command");
			puts("scan:scan card and dump");
			puts("quit:exit program");
		}
		/*Main Loop End*/
	}
}
int scan_loop(uint8_t *CardID) {

	while (1) {

		char input[32];
		int block_start;
		DISP_COMMANDLINE();
		printf("%02X%02X%02X%02X>", CardID[0], CardID[1], CardID[2], CardID[3]);
		scanf("%s", input);
		puts((char*)input);
		if (strcmp(input, "halt") == 0) {
			MFRC522_Halt();
			return 1;
		} else if (strcmp(input, "dump") == 0) {
			if (MFRC522_Debug_CardDump(CardID) < 0)
				return -1;
		} else if (strcmp(input, "read") == 0) {
			scanf("%d", &block_start);
			if (MFRC522_Debug_DumpSector(CardID, block_start) < 0) {
				return -1;
			}
		} else if(strcmp(input, "clean") == 0){
			char c;
			scanf("%d", &block_start);
			while ((c = getchar()) != '\n' && c != EOF)
				;
			if (MFRC522_Debug_Clean(CardID, block_start)) {
				return -1;
			}
			
		} else if (strcmp(input, "write") == 0) {
			char write_buffer[256];
			size_t len = 0;
			scanf("%d", &block_start);
			scanf("%s",write_buffer);
			if (len >= 0) {
				if (MFRC522_Debug_Write(CardID, block_start, write_buffer,
						strlen(write_buffer)) < 0) {
					return -1;
				}
			}
		} else {

			printf(
					"Usage:\r\n" "\tread <blockstart>\r\n" "\tdump\r\n" "\thalt\r\n" 
						"\tclean <blockaddr>\r\n" "\twrite <blockaddr> <data>\r\n");
			//return 0;
		}
	}
	return 0;

}
int tag_select(uint8_t *CardID) {
	int ret_int;
	printf(
			"Card UID: 0x%02X 0x%02X 0x%02X 0x%02X, Check Sum = 0x%02X\r\n",
			CardID[0], CardID[1], CardID[2], CardID[3], CardID[4]);
	ret_int = MFRC522_SelectTag(CardID);
	if (ret_int == 0) {
		printf("Card Select Failed\r\n");
		return -1;
	} else {
		printf("Card Selected, Type:%s\r\n",
				MFRC522_TypeToString(MFRC522_ParseType(ret_int)));
	}
	ret_int = 0;
	return ret_int;
}
