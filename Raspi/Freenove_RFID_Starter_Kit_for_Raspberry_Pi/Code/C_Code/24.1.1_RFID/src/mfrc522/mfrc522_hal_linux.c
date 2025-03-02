/*
 * mfrc522_hal.c
 *
 *  Created on: 2014��9��2��
 *      Author: Administrator
 */
#include <stdint.h>
#include <unistd.h>
#include <stdio.h>
#include <stdlib.h>
#include <getopt.h>
#include <fcntl.h>
#include <string.h>
#include <sys/ioctl.h>
#include <linux/types.h>
#include <linux/spi/spidev.h>

#define RFID_DEBUG(a)	puts(a)
#define RFID_DEBUGF		printf
#define SPI_DEV "/dev/spidev0.0"
#define RFID_DelayMs(s)	usleep(s*1000)
static int __spidev = 0;
static struct spi_ioc_transfer spixfr;

static uint32_t mode = SPI_MODE_0;
static uint8_t bits = 8;
static uint32_t speed = 100000;
static void pabort(const char *s)
{
	perror(s);
	abort();
}
void MFRC522_HAL_Delay(unsigned int ms){
	usleep(ms * 1000);
}
void MFRC522_HAL_init(void) {
	int ret;

	RFID_DEBUG("Try to open device "SPI_DEV);
	__spidev = open(SPI_DEV, O_RDWR);
	if (__spidev < 0) {
		pabort("Device Cannot open");
	} else {
		RFID_DEBUG("Device opened");
	}
	RFID_DEBUGF("Device Number:%d\r\n",__spidev);

	/*
	 * spi mode
	 */
	ret = ioctl(__spidev, SPI_IOC_WR_MODE, &mode);
	if (ret == -1)
		pabort("can't set spi mode");

	ret = ioctl(__spidev, SPI_IOC_RD_MODE, &mode);
	if (ret == -1)
		pabort("can't get spi mode");
	RFID_DEBUG("SPI mode [OK]");

	/*
	 * bits per word
	 */
	ret = ioctl(__spidev, SPI_IOC_WR_BITS_PER_WORD, &bits);
	if (ret == -1)
		pabort("can't set bits per word");

	ret = ioctl(__spidev, SPI_IOC_RD_BITS_PER_WORD, &bits);
	if (ret == -1)
		pabort("can't get bits per word");
	RFID_DEBUG("SPI word bits[OK]");

	/*
	 * max speed hz
	 */
	ret = ioctl(__spidev, SPI_IOC_WR_MAX_SPEED_HZ, &speed);
	if (ret == -1)
		pabort("can't set max speed hz");

	ret = ioctl(__spidev, SPI_IOC_RD_MAX_SPEED_HZ, &speed);
	if (ret == -1)
		pabort("can't get max speed hz");
	RFID_DEBUG("SPI max speed[OK]");

	spixfr.speed_hz = speed;
	spixfr.delay_usecs = 0;
	spixfr.bits_per_word = 8;
	spixfr.cs_change = 0;
	spixfr.pad = 0;

}

void MFRC522_HAL_write(unsigned char addr, unsigned char val) {
	int ret;
	char _dummytx[2];
	static char _devnull[2];
	_dummytx[0] = (addr << 1) & 0x7E;
	_dummytx[1] = val;

	spixfr.tx_buf = (unsigned long) _dummytx;
	spixfr.rx_buf = (unsigned long) _devnull;
	spixfr.len = 2;
	ret = ioctl(__spidev, SPI_IOC_MESSAGE(1), &spixfr);
	if (ret < 0) {
		RFID_DEBUG("SPI transfer failed");
		exit(-1);
	}
}

/*
 *  Read_MFRC522 Nombre de la funci�n: Read_MFRC522
 *  Descripci�n: Desde el MFRC522 leer un byte de un registro de datos
 *  Los par�metros de entrada: addr - la direcci�n de registro
 *  Valor de retorno: Devuelve un byte de datos de lectura
 */
unsigned char MFRC522_HAL_read(unsigned char addr) {
	int ret;
	char _dummytx[2];
	char _rxbuf[2];
	_dummytx[0] = ((addr << 1) & 0xFE)|0x80;
	_dummytx[1] = 0xFF;

	spixfr.tx_buf = (unsigned long) _dummytx;
	spixfr.rx_buf = (unsigned long) _rxbuf;
	spixfr.len = 2;
	ret = ioctl(__spidev, SPI_IOC_MESSAGE(1), &spixfr);
	if (ret < 0) {
		RFID_DEBUG("SPI transfer failed");
		exit(-1);
	}
	return _rxbuf[1];
}

