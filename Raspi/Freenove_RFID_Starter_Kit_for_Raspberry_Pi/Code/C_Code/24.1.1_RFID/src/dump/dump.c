/*
 * dump.c
 *
 *  Created on: 2014/9/7
 *      Author: gitetsu
 */
#include <string.h>
#include <ctype.h>
#include "dump.h"
#ifndef MAX_WIDTH
#define MAX_WIDTH   (16)
#endif

int (*__def_printf)(const char *__restrict, ...);
size_t __def_width = MAX_WIDTH;
int dump_config(size_t width, int (*__printf)(const char *__restrict, ...)) {
	if (width < 0 || width >= MAX_WIDTH) {
		return -1;
	}
	if (__printf == NULL) {
		return -2;
	}
	return 0;
}
const void * __dump(const void *addr, size_t bytes, size_t width,
		int (*__printf)(const char *__restrict, ...)) {
	const unsigned char *p = addr;
	char text[MAX_WIDTH + 1];
	unsigned i = 0;

	while (i < bytes) {
		if ((i % width) == 0) {
			__printf("%6d: ", i);

			memset(text, '\0', sizeof(text));
		}

		__printf("%02x ", *p);

		text[i % width] = isprint(*p) ? *p : '.';

		p++;
		i++;

		if ((i % width) == 0) {
			__printf(": %s\n", text);
		}
	}

	if ((i % width) != 0) {
		__printf("%*s: %s\n", (width - (i % width)) * 3, " ", text);
	}

	return addr;
}

int def_dump(const void *addr, size_t bytes) {
	if (__def_printf == NULL) {
		return -1;
	} else {
		__dump(addr, bytes, __def_width, __def_printf);
		return 0;
	}
}

