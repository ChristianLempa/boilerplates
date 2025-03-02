/*
 * dump.h
 *
 *  Created on: 2014/9/7
 *      Author: gitetsu
 */

#ifndef DUMP_H_
#define DUMP_H_

#define dump_16_stdout(addr,bytes)	__dump(addr,bytes,16,printf)
#define dump	dump_16_stdout
/*
 * Set default dump output function and width
 *
 *
 */
int dump_config(size_t width, int (*__printf)(const char *__restrict, ...));
/*
 * dump main function
 */
const void * __dump(const void *addr, size_t bytes, size_t width,
		int (*__printf)(const char *__restrict, ...));
/*
 * dump function with default output function and default width
 */
int def_dump(const void *addr, size_t bytes);

#endif /* DUMP_H_ */
