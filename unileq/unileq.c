/*
--------------------------------------------------------------------------------
License


unileq.c - v1.39

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
The Unileq Architecture


The goal of unileq is to recreate the functionality of a normal computer using
only one computing instruction. This is like trying to build a working car out
of legos while only using one type of lego piece. Since we only have one
instruction, most modern conveniences are gone. Things like multiplying numbers
or memory allocation need to built from scratch using unileq's instruction.

The instruction is fairly simple: Given A, B, and C, compute mem[A]-mem[B] and
store the result in mem[A]. Then, if mem[A] was less than or equal to mem[B],
jump to C. Otherwise, jump by 3. We use the instruction pointer (IP) to keep
track of our place in memory. The pseudocode below shows a unileq instruction:


     A=mem[IP+0]
     B=mem[IP+1]
     C=mem[IP+2]
     if mem[A]<=mem[B]
          IP=C
     else
          IP=IP+3
     mem[A]=mem[A]-mem[B]


The instruction pointer and memory values are all 64 bit unsigned integers.
Overflow and underflow are handled by wrapping values around to be between 0 and
2^64-1 inclusive.

Interaction with the host environment is done by reading and writing from
special memory addresses. For example, writing anything to -1 will end execution
of the unileq program.


--------------------------------------------------------------------------------
Unileq Assembly Language


We can write a unileq program by setting the raw memory values directly, but it
will be easier to both read and write a program by using an assembly language.
Because there's only one instruction, we can skip defining what's used for data,
execution, or structure like in other languages. We only need to define memory
values, and the flow of the program will decide what gets executed.


This example shows a "Hello, World!" program in assembly.


     loop: len  one  exit            #Decrement [len]. If [len]<=1, exit.
           0-2  txt  ?+1             #Print a letter.
           ?-2  neg  loop            #Increment letter pointer.

     exit: 0-1  0    0

     txt:  72 101 108 108 111 44 32  #Hello,
           87 111 114 108 100 33 10  #World!
     len:  len-txt+1
     neg:  0-1
     one:  1


The rules of the assembly language are given below.


                  |
     Single Line  |  Denoted by #
     Comment      |
                  |  Ex:
                  |       #Hello,
                  |       #World!
                  |
     -------------+--------------------------------------------------------
                  |
     Multi Line   |  Denoted by #| and terminated with |#
     Comment      |
                  |  Ex:
                  |       #|
                  |            line 1
                  |            line 2
                  |       |#
                  |
     -------------+--------------------------------------------------------
                  |
     Current      |  Denoted by a question mark. Inserts the current memory
     Address      |  address.
                  |
                  |  Ex:
                  |       ?
                  |       ?+1     #Next address
                  |
     -------------+--------------------------------------------------------
                  |
     Label        |  Denoted by a name followed by a colon. Declarations
     Declaration  |  mark the current memory address for later recall.
                  |
                  |  Labels are case sensitive and support UTF-8. They can
                  |  consist of letters, underscores, periods, numbers, and
                  |  any characters with a high bit. However, the first
                  |  character can't be a number.
                  |
                  |  Ex:
                  |       loop:
                  |       Another_Label:
                  |       label3:
                  |
     -------------+--------------------------------------------------------
                  |
     Label        |  Denoted by a label name. Inserts the memory address
     Recall       |  declared by "Label:".
                  |
                  |  Ex:
                  |       label:     #declaration
                  |       label      #recall
                  |
     -------------+--------------------------------------------------------
                  |
     Sublabel     |  Denoted by a period in front of a label. Shorthand for
                  |  placing a label under another label's scope.
                  |
                  |  Ex:
                  |        A:
                  |       .B:     #Shorthand for A.B:
                  |
     -------------+--------------------------------------------------------
                  |
     Number       |  Inserts the number's value. A number must be in
                  |  decimal or hexadecimal form.
                  |
                  |  Ex:
                  |       123
                  |       0xff
                  |
     -------------+--------------------------------------------------------
                  |
     Operator     |  Denoted by a plus or minus. Adds or subtracts the
                  |  number or label from the previous value. Parentheses
                  |  are not supported. To express a negative number, use
                  |  the form "0-x".
                  |
                  |  Ex:
                  |       len-txt+1
                  |       ?+1
                  |
     -------------+--------------------------------------------------------
                  |
     Input /      |  Interaction with the host environment can be done by
     Output       |  reading or writing from special addresses.
                  |
                  |  A = -1: End execution.
                  |  A = -2: Write mem[B] to stdout.
                  |  B = -3: Subtract stdin from mem[A].
                  |  B = -4: Subtract timing frequency from mem[A].
                  |  B = -5: Subtract current time from mem[A].
                  |  A = -6: Sleep for mem[B]/2^32 seconds.
                  |
                  |  Ex:
                  |       0-2  txt  ?+1     #A = -2. Print a letter.
                  |


--------------------------------------------------------------------------------
Notes


Linux  : gcc -O3 unileq.c -o unileq
Windows: cl /O2 unileq.c


*/

#define _CRT_SECURE_NO_WARNINGS
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <inttypes.h>
#include <time.h>
#ifdef _MSC_VER
	#include <windows.h>
	void thrd_sleep(struct timespec* ts,void* zone) {
		((void)zone);
		Sleep((DWORD)(ts->tv_sec*1000+ts->tv_nsec/1000000));
	}
#else
	#include <threads.h>
#endif

typedef uint32_t u32;
typedef uint64_t u64;
typedef unsigned char uchar;


//--------------------------------------------------------------------------------
//The unileq interpreter state.


#define UNL_RUNNING      0
#define UNL_COMPLETE     1
#define UNL_ERROR_PARSER 2
#define UNL_ERROR_MEMORY 3
#define UNL_MAX_PARSE    (1<<30)

typedef struct UnlState {
	u64 *mem,alloc,ip;
	u32 state;
	char statestr[256];
} UnlState;

UnlState* UnlCreate(void);
void UnlFree(UnlState* st);
void UnlParseAssembly(UnlState* st,const char* str);
void UnlParseFile(UnlState* st,const char* path);
void UnlClear(UnlState* st);
void UnlPrintState(UnlState* st);
u64  UnlGetIP(UnlState* st);
void UnlSetIP(UnlState* st,u64 ip);
u64  UnlGetMem(UnlState* st,u64 addr);
void UnlSetMem(UnlState* st,u64 addr,u64 val);
void UnlRun(UnlState* st,u32 iters);


//--------------------------------------------------------------------------------
//Hash map for labels.


typedef struct UnlLabel {
	struct UnlLabel *next,*scope;
	const uchar* data;
	u64 addr;
	u32 hash,len,depth;
} UnlLabel;

u32 UnlLabelCmp(UnlLabel* l,UnlLabel* r) {
	//Compare two labels from their last character to their first along with any
	//scope characters. Return 0 if they're equal.
	UnlLabel *lv=0,*rv=0;
	if (l->len!=r->len || l->hash!=r->hash) {return 1;}
	for (u32 i=l->len-1;i!=(u32)-1;i--) {
		if (l && i<l->len) {lv=l;l=l->scope;}
		if (r && i<r->len) {rv=r;r=r->scope;}
		if (lv==rv) {return 0;}
		if (lv->data[i]!=rv->data[i]) {return 1;}
	}
	return 0;
}

typedef struct UnlHashMap {
	UnlLabel** map;
	u32 mask;
} UnlHashMap;

UnlHashMap* UnlHashCreate(void) {
	UnlHashMap* map=(UnlHashMap*)malloc(sizeof(UnlHashMap));
	if (map) {
		map->mask=(1<<20)-1;
		map->map=(UnlLabel**)malloc((map->mask+1)*sizeof(UnlLabel*));
		if (map->map) {
			for (u32 i=0;i<=map->mask;i++) {map->map[i]=0;}
			return map;
		}
		free(map);
	}
	return 0;
}

void UnlHashFree(UnlHashMap* map) {
	if (map) {
		for (u32 i=0;i<=map->mask;i++) {
			UnlLabel *lbl,*next=map->map[i];
			while ((lbl=next)) {
				next=lbl->next;
				free(lbl);
			}
		}
		free(map->map);
		free(map);
	}
}

UnlLabel* UnlLabelInit(UnlHashMap* map,UnlLabel* lbl,UnlLabel* scope,const uchar* data,u32 len) {
	//Initialize a label and return a match if we find one.
	//Count .'s to determine what scope we should be in.
	u32 depth=0;
	while (depth<len && data[depth]=='.') {depth++;}
	while (scope && scope->depth>depth) {scope=scope->scope;}
	depth=scope?scope->depth:0;
	u32 hash=scope?scope->hash:0;
	u32 scopelen=scope?scope->len:0;
	lbl->scope=scope;
	lbl->depth=depth+1;
	//Offset the data address by the parent scope's depth.
	u32 dif=scopelen-depth+(depth>0);
	lbl->data=data-dif;
	lbl->len=len+dif;
	//Compute the hash of the label. Use the scope's hash to speed up computation.
	for (u32 i=scopelen;i<lbl->len;i++) {
		hash+=lbl->data[i]+i;
		hash+=hash<<17;hash^=hash>>11;
		hash+=hash<< 5;hash^=hash>> 7;
		hash+=hash<< 9;hash^=hash>>14;
		hash+=hash<<10;hash^=hash>> 6;
		hash+=hash<< 7;hash^=hash>> 9;
	}
	lbl->hash=hash;
	//Search for a match.
	UnlLabel* match=map->map[hash&map->mask];
	while (match && UnlLabelCmp(match,lbl)) {match=match->next;}
	return match;
}

UnlLabel* UnlLabelAdd(UnlHashMap* map,UnlLabel* lbl) {
	UnlLabel* dst=(UnlLabel*)malloc(sizeof(UnlLabel));
	if (dst) {
		memcpy(dst,lbl,sizeof(UnlLabel));
		u32 hash=dst->hash&map->mask;
		dst->next=map->map[hash];
		map->map[hash]=dst;
	}
	return dst;
}


//--------------------------------------------------------------------------------
//Unileq architecture interpreter.


UnlState* UnlCreate(void) {
	//Allocate a unileq interpreter.
	UnlState* st=(UnlState*)malloc(sizeof(UnlState));
	if (st) {
		st->mem=0;
		UnlClear(st);
	}
	return st;
}

void UnlFree(UnlState* st) {
	if (st) {
		UnlClear(st);
		free(st);
	}
}

void UnlParseAssembly(UnlState* st,const char* str) {
	//Convert unileq assembly language into a unileq program.
	#define  CNUM(c) ((uchar)(c<='9'?c-'0':((c-'A')&~32)+10))
	#define ISLBL(c) (CNUM(c)<36 || c=='_' || c=='.' || c>127)
	#define  ISOP(c) (c=='+' || c=='-')
	#define     NEXT (c=i++<len?ustr[i-1]:0)
	UnlClear(st);
	u32 i=0,j=0,len=0;
	const uchar* ustr=(const uchar*)str;
	uchar c,op;
	const char* err=0;
	//Get the string length.
	if (ustr) {
		while (len<UNL_MAX_PARSE && ustr[len]) {len++;}
	}
	if (len>=UNL_MAX_PARSE) {err="Input string too long";}
	//Process the string in 2 passes. The first pass is needed to find label values.
	UnlHashMap* map=UnlHashCreate();
	if (map==0) {err="Unable to allocate hash map";}
	for (u32 pass=0;pass<2 && err==0;pass++) {
		UnlLabel *scope=0,*lbl,lbl0;
		u64 addr=0,val=0,acc=0;
		op=0;
		i=0;
		NEXT;
		j=i;
		while (c && err==0) {
			u32 n=0,token=0;
			if (c=='\r' || c=='\n' || c=='\t' || c==' ') {
				//Whitespace.
				NEXT;
				continue;
			}
			if (c=='#') {
				//Comment. If next='|', use the multi-line format.
				u32 mask=0,eoc='\n',i0=i;
				if (NEXT=='|') {mask=255;eoc=('|'<<8)+'#';NEXT;}
				while (c && n!=eoc) {n=((n&mask)<<8)+c;NEXT;}
				if (mask && n!=eoc) {err="Unterminated block quote";j=i0;}
				continue;
			}
			j=i;
			if (ISOP(c)) {
				//Operator. Decrement addr since we're modifying the previous value.
				if (op) {err="Double operator";}
				if (op==':') {err="Operating on declaration";}
				if (addr--==0) {err="Leading operator";}
				op=c;
				NEXT;
			} else if (CNUM(c)<10) {
				//Number. If it starts with "0x", use hexadecimal.
				token=10;
				val=0;
				if (c=='0' && (NEXT=='x' || c=='X')) {token=16;NEXT;}
				while ((n=CNUM(c))<token) {val=val*token+n;NEXT;}
			} else if (c=='?') {
				//Current address token.
				token=1;
				val=addr;
				NEXT;
			} else if (ISLBL(c)) {
				//Label.
				while (ISLBL(c)) {NEXT;}
				lbl=UnlLabelInit(map,&lbl0,scope,ustr+(j-1),i-j);
				if (c==':') {
					//Label declaration.
					if (pass==0) {
						if (lbl) {err="Duplicate label declaration";}
						lbl0.addr=addr;
						lbl=UnlLabelAdd(map,&lbl0);
						if (lbl==0) {err="Unable to allocate label";}
					}
					scope=lbl;
					if (ISOP(op)) {err="Operating on declaration";}
					op=c;
					NEXT;
				} else {
					token=1;
					if (lbl) {val=lbl->addr;}
					else if (pass) {err="Unable to find label";}
				}
			} else {
				err="Unexpected token";
				i++;
			}
			if (token) {
				//Add a new value to memory.
				if (op=='+') {val=acc+val;}
				else if (op=='-') {val=acc-val;}
				else if (pass) {UnlSetMem(st,addr-1,acc);}
				addr++;
				acc=val;
				op=0;
				if (ISLBL(c) || c=='?') {err="Unseparated tokens";}
			}
		}
		if (err==0 && ISOP(op)) {err="Trailing operator";}
		if (pass) {UnlSetMem(st,addr-1,acc);}
	}
	if (err) {
		//We've encountered a parsing error.
		st->state=UNL_ERROR_PARSER;
		const char* fmt="Parser: %s\n";
		u32 line=1;
		uchar window[61],under[61];
		if (i-- && j--)
		{
			fmt="Parser: %s\nLine  : %u\n\n\t%s\n\t%s\n\n";
			//Find the boundaries of the line we're currently parsing.
			u32 s0=0,s1=j,k;
			for (k=0;k<j;k++) {
				if (ustr[k]=='\n') {
					line++;
					s0=k+1;
				}
			}
			while (s1<len && ustr[s1]!='\n') {s1++;}
			//Trim whitespace.
			while (s0<s1 && ustr[s0  ]<=' ') {s0++;}
			while (s1>s0 && ustr[s1-1]<=' ') {s1--;}
			//Extract the line and underline the error.
			s0=j>s0+30?j-30:s0;
			for (k=0;k<60 && s0<s1;k++,s0++) {
				c=ustr[s0];
				window[k]=c;
				under[k]=s0>=j && s0<i?'^':(c<=' '?c:' ');
			}
			window[k]=under[k]=0;
		}
		snprintf(st->statestr,sizeof(st->statestr),fmt,err,line,window,under);
	}
	UnlHashFree(map);
}

void UnlParseFile(UnlState* st,const char* path) {
	//Load and parse a source file.
	UnlClear(st);
	st->state=UNL_ERROR_PARSER;
	FILE* in=fopen(path,"rb");
	//Check if the file exists.
	if (in==0) {
		snprintf(st->statestr,sizeof(st->statestr),"Could not open file \"%s\"\n",path);
		return;
	}
	//Check the file's size.
	fseek(in,0,SEEK_END);
	size_t size=(size_t)ftell(in);
	char* str=0;
	if (size<UNL_MAX_PARSE) {
		str=(char*)malloc((size+1)*sizeof(char));
	}
	if (str==0) {
		snprintf(st->statestr,sizeof(st->statestr),"File \"%s\" too large: %zu bytes\n",path,size);
	} else {
		fseek(in,0,SEEK_SET);
		for (size_t i=0;i<size;i++) {str[i]=(char)getc(in);}
		str[size]=0;
		UnlParseAssembly(st,str);
		free(str);
	}
	fclose(in);
}

void UnlClear(UnlState* st) {
	st->state=UNL_RUNNING;
	st->statestr[0]=0;
	st->ip=0;
	free(st->mem);
	st->mem=0;
	st->alloc=0;
}

void UnlPrintState(UnlState* st) {
	const char* str=st->statestr;
	if (str[0]==0 && st->state==UNL_RUNNING) {str="Running\n";}
	printf("Unileq state: %08x\n%s",st->state,str);
}

u64 UnlGetIP(UnlState* st) {
	return st->ip;
}

void UnlSetIP(UnlState* st,u64 ip) {
	st->ip=ip;
}

u64 UnlGetMem(UnlState* st,u64 addr) {
	//Return the memory value at addr.
	return addr<st->alloc?st->mem[addr]:0;
}

void UnlSetMem(UnlState* st,u64 addr,u64 val) {
	//Write val to the memory at addr.
	if (addr>=st->alloc) {
		//If we're writing to an address outside of our memory, attempt to resize it or
		//error out.
		if (val==0) {return;}
		//Safely find the maximum we can allocate.
		u64 alloc=1,*mem=0;
		while (alloc && alloc<=addr) {alloc+=alloc;}
		if (alloc==0) {alloc--;}
		size_t max=((size_t)-1)/sizeof(u64);
		if ((sizeof(u64)>sizeof(size_t) || ((size_t)alloc)>max) && alloc>((u64)max)) {
			alloc=(u64)max;
		}
		//Attempt to allocate.
		if (alloc>addr) {
			mem=(u64*)realloc(st->mem,((size_t)alloc)*sizeof(u64));
		}
		if (mem) {
			memset(mem+st->alloc,0,((size_t)(alloc-st->alloc))*sizeof(u64));
			st->mem=mem;
			st->alloc=alloc;
		} else {
			st->state=UNL_ERROR_MEMORY;
			snprintf(st->statestr,sizeof(st->statestr),"Failed to allocate memory.\nIndex: %" PRIu64 "\n",addr);
			return;
		}
	}
	st->mem[addr]=val;
}

void UnlRun(UnlState* st,u32 iters) {
	//Run unileq for a given number of iterations. If iters=-1, run forever. We will
	//spend 99% of our time in this function.
	if (st->state!=UNL_RUNNING) {
		return;
	}
	u32 dec=iters!=(u32)-1;
	u64 a,b,ma,mb,ip=st->ip,io=(u64)-32;
	u64 *mem=st->mem,alloc=st->alloc;
	for (;iters;iters-=dec) {
		//Load a and b. c is loaded only if we jump.
		a=ip<alloc?mem[ip]:0;ip++;
		b=ip<alloc?mem[ip]:0;ip++;
		//Input
		if (b<alloc) {
			//Read mem[b].
			mb=mem[b];
		} else if (b<io) {
			//b is out of bounds.
			mb=0;
		} else if (b==(u64)-3) {
			//Read stdin.
			mb=(uchar)getchar();
		} else if (b==(u64)-4) {
			//Timing frequency. 2^32 = 1 second.
			mb=1ULL<<32;
		} else if (b==(u64)-5) {
			//Read time. time = (seconds since 1 Jan 1970) * 2^32.
			struct timespec ts;
			timespec_get(&ts,TIME_UTC);
			mb=(((u64)ts.tv_sec)<<32)+(((u64)ts.tv_nsec)*0x100000000ULL)/1000000000ULL;
		} else {
			mb=0;
		}
		//Output
		if (a<alloc) {
			//Execute a normal unileq instruction.
			ma=mem[a];
			if (ma<=mb) {
				ip=ip<alloc?mem[ip]:0;
			} else {
				ip++;
			}
			mem[a]=ma-mb;
			continue;
		}
		//a is out of bounds or a special address.
		ip=ip<alloc?mem[ip]:0;
		if (a<io) {
			//Execute a normal unileq instruction.
			UnlSetMem(st,a,-mb);
			if (st->state!=UNL_RUNNING) {
				break;
			}
			mem=st->mem;
			alloc=st->alloc;
		} else if (a==(u64)-1) {
			//Exit.
			st->state=UNL_COMPLETE;
			break;
		} else if (a==(u64)-2) {
			//Print to stdout.
			putchar((char)mb);
		} else if (a==(u64)-6) {
			//Sleep.
			struct timespec ts={
				(long)(mb>>32),
				(long)((mb&0xffffffffULL)*1000000000ULL/0x100000000ULL)
			};
			thrd_sleep(&ts,0);
		}
	}
	st->ip=ip;
}


//--------------------------------------------------------------------------------
//Example usage. Call "unileq file.unl" to run a file.


int main(int argc,char** argv) {
	UnlState* unl=UnlCreate();
	if (argc<=1) {
		//Print a usage message.
		UnlParseAssembly(
			unl,
			"loop: len  ?     neg   #if [len]=0, exit\n"
			"      0-2  data  ?+1   #print a letter\n"
			"      ?-2  neg   loop  #increment and loop\n"
			"data: 85 115 97 103 101 58 32 117 110 105 108 101"
			"      113 32 102 105 108 101 46 117 110 108 10\n"
			"neg:  0-1\n"
			"len:  len-data"
		);
	} else {
		//Load a file.
		UnlParseFile(unl,argv[1]);
	}
	//Main loop.
	UnlRun(unl,(u32)-1);
	//Exit and print status if there was an error.
	u32 ret=unl->state;
	if (ret!=UNL_COMPLETE) {UnlPrintState(unl);}
	UnlFree(unl);
	return (int)ret;
}

