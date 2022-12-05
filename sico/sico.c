/*------------------------------------------------------------------------------


sico.c - v1.46

Copyright 2020 Alec Dee - MIT license - SPDX: MIT
alecdee.github.io - akdee144@gmail.com


--------------------------------------------------------------------------------
The Single Instruction COmputer


SICO is a Single Instruction COmputer that mimics the functionality of a normal
computer while using only one computing instruction. This is like going into a
forest with no tools and trying to build a house. Since we only have one
instruction, most modern conveniences are gone. Things like multiplying numbers
or memory allocation need to be built from scratch using SICO's instruction.

The instruction is fairly simple: Given A, B, and C, compute mem[A]-mem[B] and
store the result in mem[A]. Then, if mem[A] was less than or equal to mem[B],
jump to C. Otherwise, jump by 3. We use the instruction pointer (IP) to keep
track of our place in memory. The pseudocode below shows a SICO instruction:


     A = mem[IP+0]
     B = mem[IP+1]
     C = mem[IP+2]
     IP += 3
     if mem[A] <= mem[B]: IP = C
     mem[A] -= mem[B]


The instruction pointer and memory values are all 64 bit unsigned integers.
Overflow and underflow are handled by wrapping values around to be between
0 and 2^64-1 inclusive.

Interaction with the host environment is done by reading and writing from
special memory addresses. For example, writing anything to -1 will end
execution of the SICO program.


--------------------------------------------------------------------------------
SICO Assembly Language


We can write a SICO program by setting the raw memory values directly, but it
will be easier to both read and write a program by using an assembly language.
Because there's only one instruction, we can skip defining what's used for data,
execution, or structure like in other languages. We only need to define memory
values, and the flow of the program will decide what gets executed.


This example shows a "Hello, World!" program in assembly.


     loop: len  one  exit            # Decrement [len]. If [len]<=1, exit.
           0-2  txt  ?+1             # Print a letter.
           ?-2  neg  loop            # Increment letter pointer.

     exit: 0-1  0    0

     txt:  72 101 108 108 111 44 32  # Hello,
           87 111 114 108 100 33 10  # World!
     len:  len-txt+1
     neg:  0-1
     one:  1


The rules of the assembly language are given below.


                  |
     Single Line  |  Denoted by #
     Comment      |
                  |  Ex:
                  |       # Hello,
                  |       # World!
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
                  |       ?+1  # Next address
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
                  |       label:  # declaration
                  |       label   # recall
                  |
     -------------+--------------------------------------------------------
                  |
     Sublabel     |  Denoted by a period in front of a label. Shorthand for
                  |  placing a label under another label's scope.
                  |
                  |  Ex:
                  |        A:
                  |       .B:  # Shorthand for A.B:
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
     Input /      |  For an instruction A B C, reading or writing from
     Output       |  special addresses will interact with the host. When
                  |  writing to these addresses, act as if mem[A]=0.
                  |
                  |  A = -1: End execution.
                  |  A = -2: Write mem[B] to stdout.
                  |  B = -3: mem[B] = stdin.
                  |  B = -4: mem[B] = environment timing frequency.
                  |  B = -5: mem[B] = system time.
                  |  A = -6: Sleep for mem[B]/freq seconds.
                  |
                  |  Ex:
                  |       0-2  txt  ?+1  # A = -2. Print a letter.
                  |


--------------------------------------------------------------------------------
Notes


Linux  : gcc -O3 sico.c -o sico
Windows: cl /O2 sico.c

Keep under 20k bytes.
Find a better form of label scoping.


*/


#define _CRT_SECURE_NO_WARNINGS
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <inttypes.h>
#include <time.h>
#ifdef _MSC_VER
	#include <windows.h>
	#define nanosleep(req,rem)\
		Sleep((DWORD)((req)->tv_sec*1000+(req)->tv_nsec/1000000))
#endif

typedef uint32_t u32;
typedef uint64_t u64;
typedef unsigned char uchar;


//---------------------------------------------------------------------------------
// The SICO interpreter state.


#define SICO_RUNNING      0
#define SICO_COMPLETE     1
#define SICO_ERROR_PARSER 2
#define SICO_ERROR_MEMORY 3
#define SICO_MAX_PARSE    (1<<30)

typedef struct SicoLabel {
	u64 addr;
	u32 child[16];
} SicoLabel;

typedef struct SicoState {
	u64 *mem,alloc,ip;
	u32 state;
	char statestr[256];
	SicoLabel* lblarr;
	u32 lblalloc,lblpos;
} SicoState;


SicoState* SicoCreate(void);
void SicoFree(SicoState* st);
void SicoClear(SicoState* st);

void SicoParseAssembly(SicoState* st,const char* str);
u32  SicoAddLabel(SicoState* st,u32 scope,const uchar* data,u32 len);
u64  SicoFindLabel(SicoState* st,const char* label);
void SicoParseFile(SicoState* st,const char* path);

void SicoPrintState(SicoState* st);
u64  SicoGetIP(SicoState* st);
void SicoSetIP(SicoState* st,u64 ip);
u64  SicoGetMem(SicoState* st,u64 addr);
void SicoSetMem(SicoState* st,u64 addr,u64 val);

void SicoRun(SicoState* st,u32 iters);


//---------------------------------------------------------------------------------
// SICO architecture interpreter.


SicoState* SicoCreate(void) {
	// Allocate a SICO interpreter.
	SicoState* st=(SicoState*)malloc(sizeof(SicoState));
	if (st) {
		st->mem=0;
		st->lblarr=0;
		SicoClear(st);
	}
	return st;
}

void SicoFree(SicoState* st) {
	if (st) {
		SicoClear(st);
		free(st);
	}
}

void SicoClear(SicoState* st) {
	st->state=SICO_RUNNING;
	st->statestr[0]=0;
	st->ip=0;
	free(st->mem);
	st->mem=0;
	st->alloc=0;
	free(st->lblarr);
	st->lblarr=0;
	st->lblalloc=0;
	st->lblpos=0;
}

void SicoParseAssembly(SicoState* st,const char* str) {
	// Convert SICO assembly language into a SICO program.
	#define  CNUM(c) ((uchar)(c<='9'?c-'0':((c-'A')&~32)+10))
	#define ISLBL(c) (CNUM(c)<36 || c=='_' || c=='.' || c>127)
	#define  ISOP(c) (c=='+' || c=='-')
	#define     NEXT (c=i++<len?ustr[i-1]:0)
	SicoClear(st);
	u32 i=0,j=0,len=0;
	const uchar* ustr=(const uchar*)str;
	uchar c,op;
	const char* err=0;
	// Get the string length.
	if (ustr) {
		while (len<SICO_MAX_PARSE && ustr[len]) {len++;}
	}
	if (len>=SICO_MAX_PARSE) {err="Input string too long";}
	// Process the string in 2 passes. The first pass is needed to find label values.
	for (u32 pass=0;pass<2 && err==0;pass++) {
		u32 scope=0,lbl;
		u64 addr=0,val=0,acc=0;
		op=0;
		i=0;
		NEXT;
		j=i;
		while (c && err==0) {
			u32 n=0,token=0;
			if (c=='\r' || c=='\n' || c=='\t' || c==' ') {
				// Whitespace.
				NEXT;
				continue;
			}
			if (c=='#') {
				// Comment. If next='|', use the multi-line format.
				u32 mask=0,eoc='\n',i0=i;
				if (NEXT=='|') {mask=255;eoc=('|'<<8)+'#';NEXT;}
				while (c && n!=eoc) {n=((n&mask)<<8)+c;NEXT;}
				if (mask && n!=eoc) {err="Unterminated block quote";j=i0;}
				continue;
			}
			j=i;
			if (ISOP(c)) {
				// Operator. Decrement addr since we're modifying the previous value.
				if (op) {err="Double operator";}
				if (op==':') {err="Operating on declaration";}
				if (addr--==0) {err="Leading operator";}
				op=c;
				NEXT;
			} else if (CNUM(c)<10) {
				// Number. If it starts with "0x", use hexadecimal.
				token=10;
				val=0;
				if (c=='0' && (NEXT=='x' || c=='X')) {token=16;NEXT;}
				while ((n=CNUM(c))<token) {val=val*token+n;NEXT;}
			} else if (c=='?') {
				// Current address token.
				token=1;
				val=addr;
				NEXT;
			} else if (ISLBL(c)) {
				// Label.
				while (ISLBL(c)) {NEXT;}
				lbl=SicoAddLabel(st,scope,ustr+(j-1),i-j);
				if (lbl==0) {err="Unable to allocate label";break;}
				val=st->lblarr[lbl].addr;
				if (c==':') {
					// Label declaration.
					if (pass==0) {
						if (val+1) {err="Duplicate label declaration";}
						st->lblarr[lbl].addr=addr;
					}
					if (ustr[j-1]!='.') {scope=lbl;}
					if (ISOP(op)) {err="Operating on declaration";}
					op=c;
					NEXT;
				} else {
					token=1;
					if (pass && val+1==0) {err="Unable to find label";}
				}
			} else {
				err="Unexpected token";
				i++;
			}
			if (token) {
				// Add a new value to memory.
				if (op=='+') {val=acc+val;}
				else if (op=='-') {val=acc-val;}
				else if (pass) {SicoSetMem(st,addr-1,acc);}
				addr++;
				acc=val;
				op=0;
				if (ISLBL(c) || c=='?') {err="Unseparated tokens";}
			}
		}
		if (err==0 && ISOP(op)) {err="Trailing operator";}
		if (pass) {SicoSetMem(st,addr-1,acc);}
	}
	if (err) {
		// We've encountered a parsing error.
		st->state=SICO_ERROR_PARSER;
		const char* fmt="Parser: %s\n";
		u32 line=1;
		uchar window[61],under[61];
		if (i-- && j--)
		{
			fmt="Parser: %s\nLine  : %u\n\n\t%s\n\t%s\n\n";
			// Find the boundaries of the line we're currently parsing.
			u32 s0=0,s1=j,k;
			for (k=0;k<j;k++) {
				if (ustr[k]=='\n') {
					line++;
					s0=k+1;
				}
			}
			while (s1<len && ustr[s1]!='\n') {s1++;}
			// Trim whitespace.
			while (s0<s1 && ustr[s0  ]<=' ') {s0++;}
			while (s1>s0 && ustr[s1-1]<=' ') {s1--;}
			// Extract the line and underline the error.
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
}

u32 SicoAddLabel(SicoState* st,u32 scope,const uchar* data,u32 len) {
	// Add a label if it's new. Return its position in the label array.
	SicoLabel* arr=st->lblarr;
	u32 pos=st->lblpos;
	if (arr==0) {
		// Initialize the root label.
		arr=(SicoLabel*)malloc(sizeof(SicoLabel));
		if (arr==0) {return 0;}
		st->lblalloc=1;
		pos=1;
		memset(arr,0,sizeof(SicoLabel));
		arr[0].addr=(u64)-1;
	}
	// If the label starts with a '.', make it a child of the last non '.' label.
	u32 lbl=data[0]=='.'?scope:0;
	for (u32 i=0;i<len;i++) {
		uchar c=data[i];
		for (u32 j=4;j<8;j-=4) {
			u32 val=(u32)((c>>j)&15);
			u32 parent=lbl;
			lbl=arr[parent].child[val];
			if (lbl==0) {
				if (pos>=st->lblalloc) {
					st->lblalloc<<=1;
					arr=(SicoLabel*)realloc(arr,st->lblalloc*sizeof(SicoLabel));
					if (arr==0) {i=len;break;}
				}
				lbl=pos++;
				arr[parent].child[val]=lbl;
				memset(arr+lbl,0,sizeof(SicoLabel));
				arr[lbl].addr=(u64)-1;
			}
		}
	}
	st->lblarr=arr;
	st->lblpos=pos;
	return lbl;
}

u64 SicoFindLabel(SicoState* st,const char* label) {
	// Returns the given label's address. Returns -1 if no label was found.
	if (st->lblarr==0) {return (u64)-1;}
	uchar c;
	u32 lbl=0;
	for (u32 i=0;(c=(uchar)label[i])!=0;i++) {
		for (u32 j=4;j<8;j-=4) {
			u32 val=(u32)((c>>j)&15);
			lbl=st->lblarr[lbl].child[val];
			if (lbl==0) {return (u64)-1;}
		}
	}
	return st->lblarr[lbl].addr;
}

void SicoParseFile(SicoState* st,const char* path) {
	// Load and parse a source file.
	SicoClear(st);
	st->state=SICO_ERROR_PARSER;
	FILE* in=fopen(path,"rb");
	// Check if the file exists.
	if (in==0) {
		snprintf(st->statestr,sizeof(st->statestr),"Could not open file \"%s\"\n",path);
		return;
	}
	// Check the file's size.
	fseek(in,0,SEEK_END);
	size_t size=(size_t)ftell(in);
	char* str=0;
	if (size<SICO_MAX_PARSE) {
		str=(char*)malloc((size+1)*sizeof(char));
	}
	if (str==0) {
		snprintf(st->statestr,sizeof(st->statestr),"File \"%s\" too large: %zu bytes\n",path,size);
	} else {
		fseek(in,0,SEEK_SET);
		for (size_t i=0;i<size;i++) {str[i]=(char)getc(in);}
		str[size]=0;
		SicoParseAssembly(st,str);
		free(str);
	}
	fclose(in);
}

void SicoPrintState(SicoState* st) {
	const char* str=st->statestr;
	if (str[0]==0 && st->state==SICO_RUNNING) {str="Running\n";}
	printf("SICO state: %08x\n%s",st->state,str);
}

u64 SicoGetIP(SicoState* st) {
	return st->ip;
}

void SicoSetIP(SicoState* st,u64 ip) {
	st->ip=ip;
}

u64 SicoGetMem(SicoState* st,u64 addr) {
	// Return the memory value at addr.
	return addr<st->alloc?st->mem[addr]:0;
}

void SicoSetMem(SicoState* st,u64 addr,u64 val) {
	// Write val to the memory at addr.
	if (addr>=st->alloc) {
		// If we're writing to an address outside of our memory, attempt to resize it or
		// error out.
		if (val==0) {return;}
		// Safely find the maximum we can allocate.
		u64 alloc=1,*mem=0;
		while (alloc && alloc<=addr) {alloc+=alloc;}
		if (alloc==0) {alloc--;}
		size_t max=((size_t)-1)/sizeof(u64);
		if ((sizeof(u64)>sizeof(size_t) || ((size_t)alloc)>max) && alloc>((u64)max)) {
			alloc=(u64)max;
		}
		// Attempt to allocate.
		if (alloc>addr) {
			mem=(u64*)realloc(st->mem,((size_t)alloc)*sizeof(u64));
		}
		if (mem) {
			memset(mem+st->alloc,0,((size_t)(alloc-st->alloc))*sizeof(u64));
			st->mem=mem;
			st->alloc=alloc;
		} else {
			st->state=SICO_ERROR_MEMORY;
			snprintf(st->statestr,sizeof(st->statestr),"Failed to allocate memory.\nIndex: %" PRIu64 "\n",addr);
			return;
		}
	}
	st->mem[addr]=val;
}

void SicoRun(SicoState* st,u32 iters) {
	// Run SICO for a given number of iterations. If iters=-1, run forever. We will
	// spend 99% of our time in this function.
	if (st->state!=SICO_RUNNING) {
		return;
	}
	u32 dec=(iters+1)>0;
	u64 a,b,c,ma,mb,ip=st->ip,io=(u64)-32;
	u64 *mem=st->mem,alloc=st->alloc;
	for (;iters;iters-=dec) {
		// Load a, b, and c.
		a=ip<alloc?mem[ip]:0;ip++;
		b=ip<alloc?mem[ip]:0;ip++;
		c=ip<alloc?mem[ip]:0;ip++;
		// Input
		if (b<alloc) {
			// Read mem[b].
			mb=mem[b];
		} else if (b<io) {
			// b is out of bounds.
			mb=0;
		} else if (b==(u64)-3) {
			// Read stdin.
			mb=(uchar)getchar();
		} else if (b==(u64)-4) {
			// Timing frequency. 2^32 = 1 second.
			mb=1ULL<<32;
		} else if (b==(u64)-5) {
			// Read time. time = (seconds since 1 Jan 1970) * 2^32.
			struct timespec ts;
			timespec_get(&ts,TIME_UTC);
			mb=(((u64)ts.tv_sec)<<32)+(((u64)ts.tv_nsec)*0x100000000ULL)/1000000000ULL;
		} else {
			mb=0;
		}
		// Output
		if (a<alloc) {
			// Execute a normal SICO instruction.
			ma=mem[a];
			if (ma<=mb) {ip=c;}
			mem[a]=ma-mb;
			continue;
		}
		// a is out of bounds or a special address.
		ip=c;
		if (a<io) {
			// Execute a normal SICO instruction.
			SicoSetMem(st,a,0-mb);
			if (st->state!=SICO_RUNNING) {
				break;
			}
			mem=st->mem;
			alloc=st->alloc;
		} else if (a==(u64)-1) {
			// Exit.
			st->state=SICO_COMPLETE;
			break;
		} else if (a==(u64)-2) {
			// Print to stdout.
			putchar((char)mb);
		} else if (a==(u64)-6) {
			// Sleep.
			struct timespec ts={
				(long)(mb>>32),
				(long)((mb&0xffffffffULL)*1000000000ULL/0x100000000ULL)
			};
			nanosleep(&ts,0);
		}
	}
	st->ip=ip;
}


//---------------------------------------------------------------------------------
// Example usage. Call "sico file.sico" to run a file.


int main(int argc,char** argv) {
	SicoState* st=SicoCreate();
	if (argc<=1) {
		// Print "Usage: sico file.sico".
		SicoParseAssembly(st,"\
			loop: len  ?     neg\
			      0-2  text  ?+1\
			      ?-2  neg   loop\
			text: 85 115 97 103 101 58 32 115 105 99 111\
			      32 102 105 108 101 46 115 105 99 111 10\
			neg:  0-1\
			len:  len-text\
		");
	} else {
		SicoParseFile(st,argv[1]);
	}
	// Main loop.
	SicoRun(st,(u32)-1);
	// Exit and print the status if there was an error.
	u32 ret=st->state;
	if (ret!=SICO_COMPLETE) {SicoPrintState(st);}
	SicoFree(st);
	return (int)ret;
}

