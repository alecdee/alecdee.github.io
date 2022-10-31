/*------------------------------------------------------------------------------


unileq.c - v1.45

Copyright 2020 Alec Dee - MIT license - SPDX: MIT
alecdee.github.io - akdee144@gmail.com


--------------------------------------------------------------------------------
The Unileq Architecture


Unileq's purpose is to recreate the functionality of a normal computer using
only one computing instruction. This is like going into a forest with no tools
and trying to build a house. Since we only have one instruction, most modern
conveniences are gone. Things like multiplying numbers or memory allocation
need to be built from scratch using unileq's instruction.

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
                  |       0-2  txt  ?+1  # A = -2. Print a letter.
                  |


--------------------------------------------------------------------------------
Notes


Linux  : gcc -O3 unileq.c -o unileq
Windows: cl /O2 unileq.c

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
// The unileq interpreter state.


#define UNL_RUNNING      0
#define UNL_COMPLETE     1
#define UNL_ERROR_PARSER 2
#define UNL_ERROR_MEMORY 3
#define UNL_MAX_PARSE    (1<<30)

typedef struct UnlLabel {
	u64 addr;
	u32 child[16];
} UnlLabel;

typedef struct UnlState {
	u64 *mem,alloc,ip;
	u32 state;
	char statestr[256];
	UnlLabel* lblarr;
	u32 lblalloc,lblpos;
} UnlState;


UnlState* UnlCreate(void);
void UnlFree(UnlState* st);
void UnlClear(UnlState* st);

void UnlParseAssembly(UnlState* st,const char* str);
u32  UnlAddLabel(UnlState* st,u32 scope,const uchar* data,u32 len);
u64  UnlFindLabel(UnlState* st,const char* label);
void UnlParseFile(UnlState* st,const char* path);

void UnlPrintState(UnlState* st);
u64  UnlGetIP(UnlState* st);
void UnlSetIP(UnlState* st,u64 ip);
u64  UnlGetMem(UnlState* st,u64 addr);
void UnlSetMem(UnlState* st,u64 addr,u64 val);

void UnlRun(UnlState* st,u32 iters);


//---------------------------------------------------------------------------------
// Unileq architecture interpreter.


UnlState* UnlCreate(void) {
	// Allocate a unileq interpreter.
	UnlState* st=(UnlState*)malloc(sizeof(UnlState));
	if (st) {
		st->mem=0;
		st->lblarr=0;
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

void UnlClear(UnlState* st) {
	st->state=UNL_RUNNING;
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

void UnlParseAssembly(UnlState* st,const char* str) {
	// Convert unileq assembly language into a unileq program.
	#define  CNUM(c) ((uchar)(c<='9'?c-'0':((c-'A')&~32)+10))
	#define ISLBL(c) (CNUM(c)<36 || c=='_' || c=='.' || c>127)
	#define  ISOP(c) (c=='+' || c=='-')
	#define     NEXT (c=i++<len?ustr[i-1]:0)
	UnlClear(st);
	u32 i=0,j=0,len=0;
	const uchar* ustr=(const uchar*)str;
	uchar c,op;
	const char* err=0;
	// Get the string length.
	if (ustr) {
		while (len<UNL_MAX_PARSE && ustr[len]) {len++;}
	}
	if (len>=UNL_MAX_PARSE) {err="Input string too long";}
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
				lbl=UnlAddLabel(st,scope,ustr+(j-1),i-j);
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
		// We've encountered a parsing error.
		st->state=UNL_ERROR_PARSER;
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

u32 UnlAddLabel(UnlState* st,u32 scope,const uchar* data,u32 len) {
	// Add a label if it's new. Return its position in the label array.
	UnlLabel* arr=st->lblarr;
	u32 pos=st->lblpos;
	if (arr==0) {
		// Initialize the root label.
		arr=(UnlLabel*)malloc(sizeof(UnlLabel));
		if (arr==0) {return 0;}
		st->lblalloc=1;
		pos=1;
		memset(arr,0,sizeof(UnlLabel));
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
					arr=(UnlLabel*)realloc(arr,st->lblalloc*sizeof(UnlLabel));
					if (arr==0) {i=len;break;}
				}
				lbl=pos++;
				arr[parent].child[val]=lbl;
				memset(arr+lbl,0,sizeof(UnlLabel));
				arr[lbl].addr=(u64)-1;
			}
		}
	}
	st->lblarr=arr;
	st->lblpos=pos;
	return lbl;
}

u64 UnlFindLabel(UnlState* st,const char* label) {
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

void UnlParseFile(UnlState* st,const char* path) {
	// Load and parse a source file.
	UnlClear(st);
	st->state=UNL_ERROR_PARSER;
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
	// Return the memory value at addr.
	return addr<st->alloc?st->mem[addr]:0;
}

void UnlSetMem(UnlState* st,u64 addr,u64 val) {
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
			st->state=UNL_ERROR_MEMORY;
			snprintf(st->statestr,sizeof(st->statestr),"Failed to allocate memory.\nIndex: %" PRIu64 "\n",addr);
			return;
		}
	}
	st->mem[addr]=val;
}

void UnlRun(UnlState* st,u32 iters) {
	// Run unileq for a given number of iterations. If iters=-1, run forever. We will
	// spend 99% of our time in this function.
	if (st->state!=UNL_RUNNING) {
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
			// Execute a normal unileq instruction.
			ma=mem[a];
			if (ma<=mb) {ip=c;}
			mem[a]=ma-mb;
			continue;
		}
		// a is out of bounds or a special address.
		ip=c;
		if (a<io) {
			// Execute a normal unileq instruction.
			UnlSetMem(st,a,0-mb);
			if (st->state!=UNL_RUNNING) {
				break;
			}
			mem=st->mem;
			alloc=st->alloc;
		} else if (a==(u64)-1) {
			// Exit.
			st->state=UNL_COMPLETE;
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
// Example usage. Call "unileq file.unl" to run a file.


int main(int argc,char** argv) {
	UnlState* unl=UnlCreate();
	if (argc<=1) {
		// Print "Usage: unileq file.unl".
		UnlParseAssembly(unl,"\
			loop: len  ?     neg\
			      0-2  text  ?+1\
			      ?-2  neg   loop\
			text: 85 115 97 103 101 58 32 117 110 105 108 101\
			      113 32 102 105 108 101 46 117 110 108 10\
			neg:  0-1\
			len:  len-text\
		");
	} else {
		UnlParseFile(unl,argv[1]);
	}
	// Main loop.
	UnlRun(unl,(u32)-1);
	// Exit and print the status if there was an error.
	u32 ret=unl->state;
	if (ret!=UNL_COMPLETE) {UnlPrintState(unl);}
	UnlFree(unl);
	return (int)ret;
}

