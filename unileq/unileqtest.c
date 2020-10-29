/*
unileqtest.c - v1.08

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
     Expected console output
     Expected state value
     Expected state message

Tests make sure that the interpreter catches expected syntax errors, reports
errors correctly, and processes the unileq program correctly.

--------------------------------------------------------------------------------
Compiling

This needs to be compiled from the same directory as unileq.c.

rm unileqtest; gcc -fsanitize=address -fsanitize=undefined unileqtest.c -o unileqtest; ./unileqtest

Can run "./unileqtest" or "./unileqtest file.unl".
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
#endif

//Replace putchar() with unlputchar() to capture stdout.
//Replace main() with unlmain() to avoid having two main's.
#define _CRT_SECURE_NO_WARNINGS
#include <stdio.h>
#include <time.h>
void unlputchar(char c);
int  unlgetchar(void);
#define putchar unlputchar
#define getchar unlgetchar
#define main unlmain
#include "unileq.c"
#undef main
#undef getchar
#undef putchar

//--------------------------------------------------------------------------------
//Test Cases

typedef struct unltest {
	const char* code;
	const char* out;
	u32 state;
	const char* statestr;
} unltest;

unltest unltests[]={
	//Make sure that the tester won't run forever.
	{"","",UNL_RUNNING,""},
	{0,"",UNL_RUNNING,""},
	//Invalid character ranges.
	{"\x01","",UNL_ERROR_PARSER,"Parser: Unexpected token\nline 1:\n\t\"\"\n\t\"\"\n"},
	{"\x08","",UNL_ERROR_PARSER,"Parser: Unexpected token\nline 1:\n\t\"\"\n\t\"\"\n"},
	{"\x0b","",UNL_ERROR_PARSER,"Parser: Unexpected token\nline 1:\n\t\"\"\n\t\"\"\n"},
	{"\x0c","",UNL_ERROR_PARSER,"Parser: Unexpected token\nline 1:\n\t\"\"\n\t\"\"\n"},
	{"\x0e","",UNL_ERROR_PARSER,"Parser: Unexpected token\nline 1:\n\t\"\"\n\t\"\"\n"},
	{"\x1f","",UNL_ERROR_PARSER,"Parser: Unexpected token\nline 1:\n\t\"\"\n\t\"\"\n"},
	{"\x21","",UNL_ERROR_PARSER,"Parser: Unexpected token\nline 1:\n\t\"!\"\n\t\"^\"\n"},
	{"\x22","",UNL_ERROR_PARSER,"Parser: Unexpected token\nline 1:\n\t\"\"\"\n\t\"^\"\n"},
	{"\x24","",UNL_ERROR_PARSER,"Parser: Unexpected token\nline 1:\n\t\"$\"\n\t\"^\"\n"},
	{"\x2a","",UNL_ERROR_PARSER,"Parser: Unexpected token\nline 1:\n\t\"*\"\n\t\"^\"\n"},
	{"\x2c","",UNL_ERROR_PARSER,"Parser: Unexpected token\nline 1:\n\t\",\"\n\t\"^\"\n"},
	{"\x2f","",UNL_ERROR_PARSER,"Parser: Unexpected token\nline 1:\n\t\"/\"\n\t\"^\"\n"},
	{"\x3b","",UNL_ERROR_PARSER,"Parser: Unexpected token\nline 1:\n\t\";\"\n\t\"^\"\n"},
	{"\x3e","",UNL_ERROR_PARSER,"Parser: Unexpected token\nline 1:\n\t\">\"\n\t\"^\"\n"},
	{"\x40","",UNL_ERROR_PARSER,"Parser: Unexpected token\nline 1:\n\t\"@\"\n\t\"^\"\n"},
	{"\x5b","",UNL_ERROR_PARSER,"Parser: Unexpected token\nline 1:\n\t\"[\"\n\t\"^\"\n"},
	{"\x5e","",UNL_ERROR_PARSER,"Parser: Unexpected token\nline 1:\n\t\"^\"\n\t\"^\"\n"},
	{"\x60","",UNL_ERROR_PARSER,"Parser: Unexpected token\nline 1:\n\t\"`\"\n\t\"^\"\n"},
	{"\x7b","",UNL_ERROR_PARSER,"Parser: Unexpected token\nline 1:\n\t\"{\"\n\t\"^\"\n"},
	{"\x7f","",UNL_ERROR_PARSER,"Parser: Unexpected token\nline 1:\n\t\"\x7f\"\n\t\"^\"\n"},
	//Numbers
	{"18446744073709551615 0x8000 0","",UNL_COMPLETE,""},
	{"0xffffffffffffffff 8000 0","",UNL_COMPLETE,""},
	//Arithmetic
	{"0-1 1-2+0x21 0","",UNL_COMPLETE,""},
	{"0-1 1+2 0","",UNL_COMPLETE,""},
	//"0x"="0x0"
	{"6 7 0\n0-1 0 0\n1 0x","",UNL_COMPLETE,""},
	{"7 6 0\n0-1 0 0\n0x 1","",UNL_COMPLETE,""},
	//Test if writing to 1 will print to stdout.
	{"0-1 15 1 0-1 16 1 0-1 17 1 0-1 15 1 0-1 0 0 65 66 67","ABCA",UNL_COMPLETE,""},
	//Test hex lower and upper case.
	{
		"30 31  3 37 30 27 0-1 34 1\n"
		"31 32 12 37 31 27 0-1 35 1\n"
		"32 33 21 37 32 27 0-1 36 1\n"
		"0-1 0 0\n"
		"0xabcdef 0xAbCdEf 0Xabcdef 0XAbCdEf\n"
		"48 49 50 1",
		"012",UNL_COMPLETE,""
	},
	{"0xefg","",UNL_ERROR_PARSER,"Parser: Unseparated tokens\nline 1:\n\t\"0xefg\"\n\t\"^^^^ \"\n"},
	{"+","",UNL_ERROR_PARSER,"Parser: Leading operator\nline 1:\n\t\"+\"\n\t\"^\"\n"},
	{"+1","",UNL_ERROR_PARSER,"Parser: Leading operator\nline 1:\n\t\"+1\"\n\t\"^ \"\n"},
	{"1+","",UNL_ERROR_PARSER,"Parser: Trailing operator\nline 1:\n\t\"1+\"\n\t\" ^\"\n"},
	{"1+ ","",UNL_ERROR_PARSER,"Parser: Trailing operator\nline 1:\n\t\"1+\"\n\t\" ^\"\n"},
	{"1 + ","",UNL_ERROR_PARSER,"Parser: Trailing operator\nline 1:\n\t\"1 +\"\n\t\"  ^\"\n"},
	//Labels
	{"lbl","",UNL_ERROR_PARSER,"Parser: Unable to find label\nline 1:\n\t\"lbl\"\n\t\"^^^\"\n"},
	{"lbl: 0-1 0 0","",UNL_COMPLETE,""},
	{"lbl:lbl2: 0-1 0 0","",UNL_COMPLETE,""},
	{"lbl: lbl-1 0 lbl","",UNL_COMPLETE,""},
	{":","",UNL_ERROR_PARSER,"Parser: Unexpected token\nline 1:\n\t\":\"\n\t\"^\"\n"},
	{"0+lbl:0","",UNL_ERROR_PARSER,"Parser: Operating on declaration\nline 1:\n\t\"0+lbl:0\"\n\t\"  ^^^^ \"\n"},
	{"0 lbl:+0","",UNL_ERROR_PARSER,"Parser: Operating on declaration\nline 1:\n\t\"0 lbl:+0\"\n\t\"      ^ \"\n"},
	{"?-1 ?-1 0","",UNL_COMPLETE,""},
	{"0-1+? 0 ?-2","",UNL_COMPLETE,""},
	{"0?","",UNL_ERROR_PARSER,"Parser: Unseparated tokens\nline 1:\n\t\"0?\"\n\t\"^ \"\n"},
	{"?0","",UNL_ERROR_PARSER,"Parser: Unseparated tokens\nline 1:\n\t\"?0\"\n\t\"^ \"\n"},
	{"lbl?","",UNL_ERROR_PARSER,"Parser: Unseparated tokens\nline 1:\n\t\"lbl?\"\n\t\"^^^ \"\n"},
	{"?lbl","",UNL_ERROR_PARSER,"Parser: Unseparated tokens\nline 1:\n\t\"?lbl\"\n\t\"^   \"\n"},
	{"?:","",UNL_ERROR_PARSER,"Parser: Unexpected token\nline 1:\n\t\"?:\"\n\t\" ^\"\n"},
	{"lbl: :","",UNL_ERROR_PARSER,"Parser: Unexpected token\nline 1:\n\t\"lbl: :\"\n\t\"     ^\"\n"},
	{"zero:zero-one one:one-one zero","",UNL_COMPLETE,""},
	{"lbl: lbl: 0-1 0 0","",UNL_ERROR_PARSER,"Parser: Duplicate label declaration\nline 1:\n\t\"lbl: lbl: 0-1 0 0\"\n\t\"     ^^^^        \"\n"},
	{"lbl: LBL: 0-1 0 0","",UNL_COMPLETE,""},
	//Sublabels
	{".x","",UNL_ERROR_PARSER,"Parser: Unable to find label\nline 1:\n\t\".x\"\n\t\"^^\"\n"},
	{".","",UNL_ERROR_PARSER,"Parser: Unable to find label\nline 1:\n\t\".\"\n\t\"^\"\n"},
	{"lbl: .","",UNL_ERROR_PARSER,"Parser: Unable to find label\nline 1:\n\t\"lbl: .\"\n\t\"     ^\"\n"},
	{"lbl: .: 0-1 0 0","",UNL_COMPLETE,""},
	{"lbl: ..: 0-1 0 0","",UNL_COMPLETE,""},
	{"lbl:..x: 0-1 0 0","",UNL_COMPLETE,""},
	{"lbl:...x: 0-1 0 0","",UNL_COMPLETE,""},
	{".: 0-1 0 0","",UNL_COMPLETE,""},
	{"..: 0-1 0 0","",UNL_COMPLETE,""},
	{"lbl.x:0-1 0 0","",UNL_COMPLETE,""},
	{"lbl: .1:0-1 1 lbl.1","",UNL_COMPLETE,""},
	{"lbl: .x-2 lbl.x:0 0","",UNL_COMPLETE,""},
	{"lbl: .x:0-1 lbl.x:0 0","",UNL_ERROR_PARSER,"Parser: Duplicate label declaration\nline 1:\n\t\"lbl: .x:0-1 lbl.x:0 0\"\n\t\"            ^^^^^^   \"\n"},
	{"lbl.x:0-1 lbl: .x:0 0","",UNL_ERROR_PARSER,"Parser: Duplicate label declaration\nline 1:\n\t\"lbl.x:0-1 lbl: .x:0 0\"\n\t\"               ^^^   \"\n"},
	{"lbl0: .x:0-1 lbl1: .y:0 0","",UNL_COMPLETE,""},
	{"lbl: .x:.x.y-2 ..y:0 0 lbl.x.y","",UNL_COMPLETE,""},
	//Comments
	{"#","",UNL_RUNNING,""},
	{"#\n0-1 4 1 0-1 65 0","A",UNL_COMPLETE,""},
	{"#Hello\n0-1 0 0","",UNL_COMPLETE,""},
	{"#||#0-1 0 0","",UNL_COMPLETE,""},
	{"##|\n0-1 0 0","",UNL_COMPLETE,""},
	{"|#0-1 0 0","",UNL_ERROR_PARSER,"Parser: Unexpected token\nline 1:\n\t\"|#0-1 0 0\"\n\t\"^        \"\n"},
	{"0-1 6 1 0-1 0 0 65\n#","A",UNL_COMPLETE,""},
	{"0-1 6 1 0-1 0 0 65\n#abc","A",UNL_COMPLETE,""},
	{"#|\ncomment\n|#\n0-1 0 0","",UNL_COMPLETE,""},
	{"lbl1: 0-1 lbl2: lbl1#|comment|#lbl1 0","",UNL_COMPLETE,""},
	{"#|","",UNL_ERROR_PARSER,"Parser: Unterminated block quote\nline 1:\n\t\"#|\"\n\t\"^^\"\n"},
	{"# |#\n0-1 6 1 0-1 0 0 66","B",UNL_COMPLETE,""},
	{"#|#0-1 0 0","",UNL_ERROR_PARSER,"Parser: Unterminated block quote\nline 1:\n\t\"#|#0-1 0 0\"\n\t\"^^^^^^^^^^\"\n"},
	//Self modification test. Make sure that we can modify A, B, and C as expected.
	//Tests if an instruction can modify its jump operand without affecting its jump.
	{
		"?+2 neg+0  ?+1\n"
		"0-1 char+0 1\n"
		"?+2 neg+1  ?+1\n"
		"0-1 char+1 1\n"
		"?+2 neg+2  ?+1\n"
		"0-1 char+2 1\n"
		"?+2 neg+3  ?+1\n"
		"0-1 char+3 1\n"
		"0-1 0 0\n"
		" neg:4 10 16 22\n"
		"char:65 66 67 10",
		"ABC\n",UNL_COMPLETE,""
	},
	//Prints "Hello, World!". Also tests UTF-8 support.
	{
		"m\xc3\xa5in:\n"
		"       .len  one neg #if len=0, abort\n"
		"       0-1   .data 1 #print a letter \xc2\xaf\\_(\xe3\x83\x84)_/\xc2\xaf\n"
		"       0-2+? neg m\xc3\xa5in   #increment pointer and loop\n"
		".data: 72 101 108 108 111 44 0x20  #Hello,\n"
		"       87 111 114 108 100 33 10    #World!\n"
		"m\xc3\xa5in.len: m\xc3\xa5in.len-m\xc3\xa5in.data+1\n"
		"neg:0-1 one:1 0",
		"Hello, World!\n",UNL_COMPLETE,""
	},
	//Memory
	//Writing 0 to a high memory cell should do nothing.
	{"0-2 val 3 0-1 0 val:0","",UNL_COMPLETE,""},
	//The memory allocation in unileq.c should safely fail if we write to a high
	//address.
	{"0-2 val 3 0-1 0 val:1","",UNL_ERROR_MEMORY,"Failed to allocate memory.\nIndex: 18446744073709551614\n"}
};

//--------------------------------------------------------------------------------
//Testing

//A helper function used to capture stdout.
char unlbufstr[512]={0};
u32  unlbufpos=0;
void unlputchar(char c) {
	if (c==0) {return;}
	if (unlbufpos+1<sizeof(unlbufstr)) {
		unlbufstr[unlbufpos++]=c;
	}
}

int unlgetchar(void) {
	printf("Failed: called stdin\n");
	exit(1);
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
	esc['\"']='"';
	esc['\\']='\\';
	while (*src) {
		unsigned char c=(unsigned char)*src++;
		if (c>127) {
			printf("\\x%x%x",c>>4,c&15);
		} else if (esc[c]) {
			printf("\\%c",esc[c]);
		} else {
			printf("%c",c);
		}
	}
}

u64 unlrand(void) {
	//Generate a random, uniformly distributed 64 bit integer.
	static u64 state=0,inc=0;
	if (inc==0) {
		inc=((u64)&inc)^((u64)clock());
		inc=unlrand()|1;
		state=((u64)&state)^((u64)clock());
		printf("PRNG seed: 0x%016llx, 0x%016llx\n",(unsigned long long)state,(unsigned long long)inc);
	}
	u64 hash=state+=inc;
	hash++;hash+=hash<<10;hash^=hash>>51;
	hash++;hash+=hash<<32;hash^=hash>>14;
	hash++;hash+=hash<< 4;hash^=hash>>12;
	hash++;hash+=hash<<24;hash^=hash>>28;
	return hash;
}

int main(int argc,char** argv) {
	printf("Testing unileq\n");
	if (argc>1) {
		//Load a file and run it.
		printf("Loading \"%s\"\n",argv[1]);
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
			printf("Test %u\nsource  : \"",i+1);
			unlprint(test->code);
			printf("\"\n");
			//Run the test code.
			unlstate* unl=unlcreate();
			unlparsestr(unl,test->code);
			unlrun(unl,1024);
			//Print what we expect.
			printf("expected: \"");
			unlprint(test->out);
			printf("\", %d, \"",test->state);
			unlprint(test->statestr);
			printf("\"\n");
			//Print what we actually got.
			printf("returned: \"");
			unlbufstr[unlbufpos]=0;
			unlprint(unlbufstr);
			unlbufpos=0;
			printf("\", %d, \"",unl->state);
			unlprint(unl->statestr);
			printf("\"\n\n");
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
