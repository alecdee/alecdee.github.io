/*
unileqtest.c - v1.01

Copyright (C) 2020 by Alec Dee - alecdee.github.io - akdee144@gmail.com

Permission is hereby granted, free of charge, to any person obtaining a copy of
this software and associated documentation files (the "Software"), to deal in
the Software without restriction, including without limitation the rights to
use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies
of the Software, and to permit persons to whom the Software is furnished to do
so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS
FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR
COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER
IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN
CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

--------------------------------------------------------------------------------
Testing

We have a list of test cases which include

     Unileq source code
     Expected std output
     Expected state value
     Expected state message

Tests make sure that the interpreter catches expected syntax errors, reports
errors correctly, and processes the unileq program correctly.

--------------------------------------------------------------------------------
Compiling

This needs to be compiled from the same directory as unileq.c.

rm unileqtest; gcc -fsanitize=address -fsanitize=undefined unileqtest.c -o unileqtest; ./unileqtest

Can also run "unileqtest file.unl".
*/

#if defined(__GNUC__)
	#pragma GCC diagnostic error "-Wall"
	#pragma GCC diagnostic error "-Wextra"
	#pragma GCC diagnostic error "-Wpedantic"
	#pragma GCC diagnostic error "-Wformat=1"
	#pragma GCC diagnostic error "-Wconversion"
	#pragma GCC diagnostic error "-Wshadow"
	#pragma GCC diagnostic error "-Wundef"
	#pragma GCC diagnostic error "-Winit-self"
#elif defined(_MSC_VER)
	#pragma warning(push,4)
	//MSVC considers fopen to be unsafe.
	#pragma warning(disable:4996)
#endif

//Replace putchar() with unlputchar() to capture stdout.
//Replace main() with unlmain() to avoid having two main's.
#include <stdio.h>
#include <time.h>
void unlputchar(char c);
#define putchar unlputchar
#define main unlmain
#include "unileq.c"
#undef main

//--------------------------------------------------------------------------------
//Test Cases

typedef struct unltest {
	const char *code;
	const char* out;
	u32 state;
	const char* statestr;
} unltest;

unltest unltests[]={
	//Make sure that the tester won't run forever.
	{"","",UNL_RUNNING,""},
	{0,"",UNL_RUNNING,""},
	//Numbers
	{"0 0x8000 18446744073709551615","",UNL_COMPLETE,""},
	{"0 8000 0xffffffffffffffff","",UNL_COMPLETE,""},
	//Arithmetic
	{"0 0 0-1","",UNL_COMPLETE,""},
	{"1+2 0 0-1","",UNL_COMPLETE,""},
	{"+","",UNL_ERROR_PARSER,"Parser: Leading operator\nline 1:\n\t'+'\n\t'^'\n"},
	{"+1","",UNL_ERROR_PARSER,"Parser: Leading operator\nline 1:\n\t'+1'\n\t'^ '\n"},
	{"1+","",UNL_ERROR_PARSER,"Parser: Trailing operator\nline 1:\n\t'1+'\n\t' ^'\n"},
	//Labels
	{"lbl","",UNL_ERROR_PARSER,"Parser: Unable to find label\nline 1:\n\t'lbl'\n\t'^^^'\n"},
	{"lbl: 0 0 0-1","",UNL_COMPLETE,""},
	{"lbl:lbl2: 0 0 0-1","",UNL_COMPLETE,""},
	{"lbl: 1 0 lbl-1","",UNL_COMPLETE,""},
	{":","",UNL_ERROR_PARSER,"Parser: Unexpected token\nline 1:\n\t':'\n\t'^'\n"},
	{"0+lbl:0","",UNL_ERROR_PARSER,"Parser: Operating on declaration\nline 1:\n\t'0+lbl:0'\n\t'  ^^^^ '\n"},
	{"0 lbl:+0","",UNL_ERROR_PARSER,"Parser: Operating on declaration\nline 1:\n\t'0 lbl:+0'\n\t'      ^ '\n"},
	{"0 ? ?-3","",UNL_COMPLETE,""},
	{"0 ? 0-3+?","",UNL_COMPLETE,""},
	{"0?","",UNL_ERROR_PARSER,"Parser: Unseparated tokens\nline 1:\n\t'0?'\n\t'^ '\n"},
	{"?0","",UNL_ERROR_PARSER,"Parser: Unseparated tokens\nline 1:\n\t'?0'\n\t'^ '\n"},
	{"lbl?","",UNL_ERROR_PARSER,"Parser: Unseparated tokens\nline 1:\n\t'lbl?'\n\t'^^^ '\n"},
	{"?lbl","",UNL_ERROR_PARSER,"Parser: Unseparated tokens\nline 1:\n\t'?lbl'\n\t'^   '\n"},
	{"?:","",UNL_ERROR_PARSER,"Parser: Unexpected token\nline 1:\n\t'?:'\n\t' ^'\n"},
	{"lbl: :","",UNL_ERROR_PARSER,"Parser: Unexpected token\nline 1:\n\t'lbl: :'\n\t'     ^'\n"},
	{"zero:0 one:0 zero-one","",UNL_COMPLETE,""},
	//Sublabels
	{".x","",UNL_ERROR_PARSER,"Parser: Unable to find label\nline 1:\n\t'.x'\n\t'^^'\n"},
	{".","",UNL_ERROR_PARSER,"Parser: Unable to find label\nline 1:\n\t'.'\n\t'^'\n"},
	{"lbl: .","",UNL_ERROR_PARSER,"Parser: Unable to find label\nline 1:\n\t'lbl: .'\n\t'     ^'\n"},
	{"lbl: .: 0 0 0-1","",UNL_COMPLETE,""},
	{"lbl: ..: 0 0 0-1","",UNL_COMPLETE,""},
	{"lbl:..x: 0 0 0-1","",UNL_COMPLETE,""},
	{"lbl:...x: 0 0 0-1","",UNL_COMPLETE,""},
	{".: 0 0 0-1","",UNL_COMPLETE,""},
	{"..: 0 0 0-1","",UNL_COMPLETE,""},
	{"lbl.x:0 0 0-1","",UNL_COMPLETE,""},
	{"lbl: .1:0 lbl.1 0-1","",UNL_COMPLETE,""},
	{"lbl: .x lbl.x:0 0-1","",UNL_COMPLETE,""},
	{"lbl: .x:0 lbl.x:0 0-1","",UNL_ERROR_PARSER,"Parser: Duplicate label declaration\nline 1:\n\t'lbl: .x:0 lbl.x:0 0-1'\n\t'          ^^^^^^     '\n"},
	{"lbl.x:0 lbl: .x:0 0-1","",UNL_ERROR_PARSER,"Parser: Duplicate label declaration\nline 1:\n\t'lbl.x:0 lbl: .x:0 0-1'\n\t'             ^^^     '\n"},
	{"lbl0: .x:0 lbl1: .y:0 0-1","",UNL_COMPLETE,""},
	{"lbl: .x:0 ..y:0 .x.y-2 lbl.x.y","",UNL_COMPLETE,""},
	//Comments
	{"#Hello\n0 0 0-1","",UNL_COMPLETE,""},
	{"#||#0 0 0-1","",UNL_COMPLETE,""},
	{"##|\n0 0 0-1","",UNL_COMPLETE,""},
	{"#|\ncomment\n|#\n0 0 0-1","",UNL_COMPLETE,""},
	{"#|","",UNL_ERROR_PARSER,"Parser: Unterminated block quote\nline 1:\n\t'#|'\n\t'^^'\n"},
	//Self modification tests. Make sure that we can modify A, B, and C as expected.
	//Tests if an instruction can modify its jump parameter without affecting its
	//jump. Also tests if writing to -1 will jump.
	{
		"?+2 neg+0  ?+1\n"
		"0-1 char+0 ?+1\n"
		"?+2 neg+1  ?+1\n"
		"0-1 char+1 ?+1\n"
		"?+2 neg+2  ?+1\n"
		"0-1 char+2 ?+1\n"
		"?+2 neg+3  ?+1\n"
		"0-1 char+3 0-1\n"
		" neg:4 10 16 22\n"
		"char:65 66 67 10",
		"ABC\n",UNL_COMPLETE,""
	},
	//Prints "Hello, World!". Also tests UTF-8 support.
	{
		"z:z z måin\n"
		"neg:0-1 one:1\n"
		"måin:\n"
		"       .len  one   0-1   #if len=0, goto -1\n"
		"       0-1   .data ?+1   #print a letter ¯\\_(ツ)_/¯\n"
		"       0-2+? neg   måin  #increment pointer and loop\n"
		".data: 72 101 108 108 111 44 0x20  #Hello,\n"
		"       87 111 114 108 100 33 10    #World!\n"
		"måin.len: måin.len-måin.data+1"
		,"Hello, World!\n",UNL_COMPLETE,""
	},
	//Memory
	//Write 0 to a high memory cell.
	{"0-16 val 0-1 val:0","",UNL_COMPLETE,""},
	//The memory allocation in unileq.c should safely fail if we write to a high
	//address.
	{"0-16 val 0-1 val:1","",UNL_ERROR_MEMORY,"Failed to allocate memory.\nIndex: 18446744073709551600\n"}
};

//--------------------------------------------------------------------------------
//Testing

//A helper function used to capture stdout.
char unlbufstr[512]={0};
u32  unlbufpos=0;
void unlputchar(char c) {
	if (unlbufpos+1<sizeof(unlbufstr)) {
		unlbufstr[unlbufpos++]=c;
	}
}

void unlprint(const char* src) {
	//Print a string and show escaped characters.
	if (src==0) {return;}
	char esc[256];
	memset(esc,0,sizeof(esc));
	esc['\n']='n';
	esc['\r']='r';
	esc['\t']='t';
	esc['\b']='b';
	while (*src) {
		int c=*src++;
		if (c>=0 && c<32 && esc[c]) {
			printf("\\%c",esc[c]);
		} else {
			printf("%c",c);
		}
	}
}

u64 unlrand(void) {
	//Generate a random, uniformly distributed 64 bit integer. Uses Knuth's constants.
	static u64 state=0,init=0;
	if (init==0) {
		state=(u32)time(0);
		init=1;
		printf("PRNG seed: 0x%016llx\n",(unsigned long long)state);
	}
	state=state*6364136223846793005ULL+1442695040888963407ULL;
	return state;
}

int main(int argc,char** argv) {
	printf("Testing unileq\n");
	if (argc>1) {
		//Load a file and run it.
		printf("Loading '%s'\n",argv[1]);
		unlstate* unl=unlcreate();
		unlparsefile(unl,argv[1]);
		while (unl->state==UNL_RUNNING) {
			unlrun(unl,unlrand()&127);
		}
		unlbufstr[unlbufpos]=0;
		printf("%s",unlbufstr);
		unlbufpos=0;
		unlprintstate(unl);
		unlfree(unl);
	} else {
		//Run syntax tests.
		u32 tests=sizeof(unltests)/sizeof(unltest);
		printf("Tests: %u\n\n",tests);
		for (u32 i=0;i<tests;i++) {
			//Load our next test.
			unltest* test=unltests+i;
			printf("Test %u\nsource  : '",i);
			unlprint(test->code);
			printf("'\n");
			//Run the test code.
			unlstate* unl=unlcreate();
			unlparsestr(unl,test->code);
			unlrun(unl,1024);
			//Print what we expect.
			printf("expected: '");
			unlprint(test->out);
			printf("', %d, '",test->state);
			unlprint(test->statestr);
			printf("'\n");
			//Print what we actually got.
			printf("returned: '");
			unlbufstr[unlbufpos]=0;
			unlprint(unlbufstr);
			unlbufpos=0;
			printf("', %d, '",unl->state);
			unlprint(unl->statestr);
			printf("'\n\n");
			//Compare the two.
			if (strcmp(test->out,unlbufstr) || test->state!=unl->state || strcmp(test->statestr,unl->statestr)) {
				printf("Failed\n");
				printf("%s\n",unl->statestr);
				return 1;
			}
			unlfree(unl);
		}
	}
	printf("Passed\n");
	return 0;
}
