/*
unileq.c - v1.09

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
Architecture Specification

Unileq is a one instruction architecture inspired by subleq. It's name comes
from its one instruction, which stands for UNsigned Integer subtract and branch
if Less than or EQual. Using this instruction, and some ingenuity, we can
construct a unileq program that can do anything that a more complicated
architecture can do.

To execute a unileq instruction, let A, B, and C be the values held in three
consecutive memory addresses, and let mem[X] denote the memory value at address
X. We then subtract mem[B] from mem[A] and store it back in mem[A]. If mem[A]
was less than or equal to mem[B], then we jump to C. Otherwise, we advance to
the next three memory addresses after A, B, and C.

We keep track of the memory we're executing with the instruction pointer, IP,
which is set to 0 at the start of the program. Execution ends if IP=-1. The
psuedocode below shows a unileq instruction:

     A=mem[IP+0]
     B=mem[IP+1]
     C=mem[IP+2]
     if mem[A]<=mem[B]
          IP=C
     else
          IP=IP+3
     endif
     mem[A]=mem[A]-mem[B]

The instruction pointer and all memory values are 64 bit unsigned integers.
Overflow and underflow are handled by wrapping values around to be between 0 and
2^64-1 inclusive.

--------------------------------------------------------------------------------
Unileq Assembly Language

We can write a unileq program by setting the memory values directly, but it will
be easier to both read and write a unileq program by using an assembly language.
Note that because there's only one instruction, we can omit any notation
specifying what instruction to execute on some given memory values. We only need
to specify what values will make up the program, and the unileq instruction will
be executed on whatever values the instruction pointer is pointed to.

An outline of our language is given below:

#Single line comment.

#|
     multi-line
     comment
|#

?
     Inserts the current memory address.

Label:
     Label declaration. Declarations mark the current memory address for later
     recall. Declarations can't appear within an expression, ex: "0 label: +1".
     Duplicate declarations are an error.

     Labels are case sensitive and support UTF-8.
     First character    : a-zA-Z_.    and any character with a high bit
     Trailing characters: a-zA-Z_.0-9 and any character with a high bit

Label
     Inserts the memory address marked by "Label:". There must be whitespace or
     an operator between any two label recalls or numbers.

.Sublabel
     Shorthand for placing a label under another label's scope.
     Ex: "lbl:0 .sub:1" will be treated as "lbl:0 lbl.sub:1" internally.

Number
     Inserts the number's value. A number must be in decimal or hexadecimal
     form, such as "123" or "0xff".

Operator +-
     Adds or subtracts the number or label to the previous memory value.
     Parentheses are not supported. To express a negative number, use its
     unsigned form or the identity "0-x=-x".

     There cannot be two consecutive operators, ex: "0++1". Also, the first and
     last character of the program cannot be an operator.

Special memory addresses
     Writing to -1 will print to stdout.
     Reading from -1 will read from stdin.
     Jumping to -1 will end execution.

--------------------------------------------------------------------------------
TODO

Keep source under 20,000 bytes.

Linux  : gcc -O3 unileq.c -o unileq
Windows: cl /O2 unileq.c
*/

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <inttypes.h>

typedef uint32_t u32;
typedef uint64_t u64;

//--------------------------------------------------------------------------------
//Hash map for labels.

typedef struct unllabel unllabel;
struct unllabel {
	unllabel *next,*scope;
	const char* data;
	u64 addr;
	u32 hash,len,depth;
};

u32 unllabelcmp(unllabel* l,unllabel* r) {
	//Compare two labels from their last character to their first along with any
	//scope characters. Return 0 if they're equal.
	unllabel *lv=0,*rv=0;
	u32 llen=l->len,rlen=r->len;
	if (llen!=rlen || l->hash!=r->hash) {return 1;}
	for (u32 i=llen-1;i!=((u32)-1);i--) {
		if (i<llen) {lv=l;l=l->scope;llen=l->len;}
		if (i<rlen) {rv=r;r=r->scope;rlen=r->len;}
		if (lv==rv) {return 0;}
		char lc=lv->data[i-llen];
		char rc=rv->data[i-rlen];
		if (lc!=rc) {return 1;}
	}
	return 0;
}

typedef struct unlhashmap unlhashmap;
struct unlhashmap {
	u32 mask;
	unllabel** map;
};

unlhashmap* unlhashcreate(void) {
	unlhashmap* map=(unlhashmap*)malloc(sizeof(unlhashmap));
	if (map) {
		map->mask=(1<<20)-1;
		map->map=(unllabel**)malloc((map->mask+1)*sizeof(unllabel*));
		if (map->map) {
			for (u32 i=0;i<=map->mask;i++) {map->map[i]=0;}
			return map;
		}
		free(map);
	}
	return 0;
}

void unlhashfree(unlhashmap* map) {
	if (map) {
		for (u32 i=0;i<=map->mask;i++) {
			unllabel *next=map->map[i],*lbl;
			while (next) {
				lbl=next;
				next=lbl->next;
				free(lbl);
			}
		}
		free(map->map);
		free(map);
	}
}

unllabel* unllabelinit(unlhashmap* map,unllabel* lbl,unllabel* scope,const char* data,u32 len) {
	//Initialize a label and return a match if we find one.
	//Count .'s to determine what scope we should be in.
	u32 depth=0;
	while (depth<len && data[depth]=='.') {depth++;}
	while (scope->depth>depth) {scope=scope->scope;}
	depth=scope->depth;
	lbl->scope=scope;
	lbl->depth=depth+1;
	//Offset the data address by the parent scope's depth.
	depth-=depth>0;
	lbl->data=data+depth;
	lbl->len=len+scope->len-depth;
	//Compute the hash of the label. Use the scope's hash to speed up computation.
	u32 hash=scope->hash;
	for (u32 i=0;i<lbl->len-scope->len;i++) {
		hash+=lbl->data[i]+1;
		hash=(hash>>9)|(hash<<23);
		hash^=hash>>14;
		hash*=0xe4d75b4b;
		hash=(hash>>7)|(hash<<25);
		hash^=hash>>6;
		hash*=0x253aa2ed;
		hash=(hash>>17)|(hash<<15);
		hash^=hash>>6;
		hash*=0x5d24324b;
		hash=(hash>>16)|(hash<<16);
	}
	lbl->hash=hash;
	//Search for a match.
	unllabel* match=map->map[hash&map->mask];
	while (match && unllabelcmp(match,lbl)) {match=match->next;}
	return match;
}

unllabel* unllabeladd(unlhashmap* map,unllabel* lbl) {
	unllabel* dst=(unllabel*)malloc(sizeof(unllabel));
	if (dst) {
		memcpy(dst,lbl,sizeof(unllabel));
		u32 hash=lbl->hash&map->mask;
		dst->next=map->map[hash];
		map->map[hash]=dst;
	}
	return dst;
}

//--------------------------------------------------------------------------------
//Unileq architecture emulator.

#define UNL_RUNNING      1
#define UNL_ERROR_PARSER 2
#define UNL_ERROR_MEMORY 4
#define UNL_MAX_PARSE    (1<<30)

typedef struct unlstate unlstate;
struct unlstate {
	u64 *mem,alloc,ip;
	u32 state;
	char statestr[256];
};

void unlclear(unlstate* st);
void unlsetmem(unlstate* st,u64 addr,u64 val);

unlstate* unlcreate(void) {
	//Allocate a unileq emulator.
	unlstate* st=(unlstate*)malloc(sizeof(unlstate));
	if (st) {
		st->mem=0;
		unlclear(st);
	}
	return st;
}

void unlfree(unlstate* st) {
	if (st) {
		unlclear(st);
		free(st);
	}
}

void unlparsestr(unlstate* st,const char* str) {
	//Convert unileq assembly language into a unileq program.
	#define  CNUM(c) (c>='a'?c-'a'+10:(c>='A'?c-'A'+10:(c>='0' && c<='9'?c-'0':99)))
	#define ISLBL(c) (CNUM(c)<36 || c=='_' || c=='.' || c<0)
	#define  ISOP(c) (c=='+' || c=='-')
	#define     NEXT (c=++i<=len?str[i-1]:0)
	unlclear(st);
	u32 i=0,j=0,len=0;
	char c,op;
	const char* err=0;
	//Get the string length.
	if (str) {
		while (len<UNL_MAX_PARSE && str[len]) {len++;}
	}
	if (len>=UNL_MAX_PARSE) {err="Input string too long";}
	//Process the string in 2 passes. The first pass is needed to find label values.
	unlhashmap* hash=unlhashcreate();
	if (hash==0) {err="Unable to allocate hash map";}
	unllabel scope0={0,0,0,0,0,0,0},lbl0;
	for (u32 pass=0;pass<2 && err==0;pass++) {
		unllabel *scope=&scope0,*lbl;
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
				if (NEXT=='|') {mask=255;eoc=('|'<<8)|'#';}
				while (c && n!=eoc) {n=((n&mask)<<8)|c;NEXT;}
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
				//Next address token.
				token=1;
				val=addr;
				NEXT;
			} else if (ISLBL(c)) {
				//Label.
				while (ISLBL(c)) {NEXT;}
				lbl=unllabelinit(hash,&lbl0,scope,str+(j-1),i-j);
				if (c==':') {
					//Label declaration.
					if (pass==0) {
						if (lbl) {err="Duplicate label declaration";}
						lbl0.addr=addr;
						lbl=unllabeladd(hash,&lbl0);
						if (lbl==0) {err="Unable to allocate label";}
					}
					scope=lbl;
					NEXT;
					if (ISOP(op)) {err="Operating on declaration";}
					op=':';
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
				else if (pass) {unlsetmem(st,addr-1,acc);}
				addr++;
				acc=val;
				op=0;
				if (ISLBL(c) || c=='?') {err="Unseparated tokens";}
			}
		}
		if (err==0 && ISOP(op)) {err="Trailing operator";i++;}
		if (pass) {unlsetmem(st,addr-1,acc);}
	}
	if (err) {
		//We've encountered a parsing error.
		st->state=UNL_ERROR_PARSER;
		const char* fmt="Parser: %s\n";
		u32 line=1;
		char window[61],under[61];
		if (i-- && j--)
		{
			fmt="Parser: %s\nline %u:\n\t'%s'\n\t'%s'\n";
			//Find the boundaries of the line we're currently parsing.
			u32 s0=0,s1=j,k;
			for (k=0;k<j;k++) {
				if (str[k]=='\n') {
					line++;
					s0=k+1;
				}
			}
			while (s1<len && str[s1]!='\n') {s1++;}
			//Trim whitespace.
			while (s0<s1 && ((u32)str[s0  ])<33) {s0++;}
			while (s1>s0 && ((u32)str[s1-1])<33) {s1--;}
			//Extract the line and underline the error.
			s0=j>s0+30?j-30:s0;
			for (k=0;k<61;k++,s0++) {
				c=(s0<s1 && k<60)?str[s0]:0;
				window[k]=c;
				under[k]=((u32)c)<33?c:(s0>=j && s0<i?'^':' ');
			}
		}
		snprintf(st->statestr,sizeof(st->statestr),fmt,err,line,window,under);
	}
	unlhashfree(hash);
}

void unlparsefile(unlstate* st,const char* path) {
	//Load and parse a source file.
	unlclear(st);
	FILE* in=fopen(path,"rb");
	//Check if the file exists.
	if (in==0) {
		st->state=UNL_ERROR_PARSER;
		snprintf(st->statestr,sizeof(st->statestr),"Could not open file \"%s\"\n",path);
		return;
	}
	//Check the file's size.
	fseek(in,0,SEEK_END);
	long int size=ftell(in);
	char* str=0;
	if (size>=0 && size<UNL_MAX_PARSE) {
		str=(char*)malloc((size+1)*sizeof(char));
	}
	if (str==0) {
		st->state=UNL_ERROR_PARSER;
		snprintf(st->statestr,sizeof(st->statestr),"File \"%s\" too large: %ld bytes\n",path,size);
	} else {
		fseek(in,0,SEEK_SET);
		for (long int i=0;i<size;i++) {str[i]=(char)getc(in);}
		str[size]=0;
		unlparsestr(st,str);
		free(str);
	}
	fclose(in);
}

void unlprintstate(unlstate* st) {
	const char* str=st->statestr;
	if (str[0]==0 && st->state==UNL_RUNNING) {str="Running\n";}
	printf("Unileq state: %08x\n%s",st->state,str);
}

void unlclear(unlstate* st) {
	st->state=UNL_RUNNING;
	st->statestr[0]=0;
	st->ip=0;
	free(st->mem);
	st->mem=0;
	st->alloc=0;
}

u64 unlgetip(unlstate* st) {
	return st->ip;
}

void unlsetip(unlstate* st,u64 ip) {
	//Jumping to -1 aborts the program.
	st->ip=ip;
	if (ip+1) {st->state|= UNL_RUNNING;}
	else      {st->state&=~UNL_RUNNING;}
}

u64 unlgetmem(unlstate* st,u64 addr) {
	//Return the memory value at addr.
	return addr<st->alloc?st->mem[addr]:0;
}

void unlsetmem(unlstate* st,u64 addr,u64 val) {
	//Write val to the memory at addr.
	if (addr>=st->alloc) {
		//If we're writing to an address outside of our memory, attempt to resize it or
		//error out.
		if (val==0) {return;}
		//Safely find the maximum we can allocate.
		u64 alloc=1,*mem=0;
		while (alloc && alloc<=addr) {alloc+=alloc;}
		if (alloc==0) {alloc=(u64)-1;}
		size_t salloc=(size_t)alloc,smax=((size_t)-1)/sizeof(u64);
		if (((u64)salloc)!=alloc || salloc>smax) {alloc=smax;}
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

void unlrun(unlstate* st,u32 iters) {
	//Run unileq for a given number of iterations. If iters=-1, run forever.
	u32 dec=iters+1!=0;
	u64 a,b,c,av,ip=st->ip,io=(u64)-1;
	for (;iters && ip!=io && st->state==UNL_RUNNING;iters-=dec) {
		//Load a, b, and c.
		a=unlgetmem(st,ip++);
		b=unlgetmem(st,ip++);
		c=unlgetmem(st,ip++);
		//If b=-1, wait for input. Otherwise, load mem[b].
		if (b<io) {
			b=unlgetmem(st,b);
		} else {
			b=getchar();
			b&=255;
		}
		if (a<io) {
			//Write to mem[a] and jump if mem[a]<=mem[b].
			av=unlgetmem(st,a);
			unlsetmem(st,a,av-b);
			if (av>b) {continue;}
		} else {
			//a=-1, so print mem[b].
			putchar(b&255);
		}
		ip=c;
	}
	unlsetip(st,ip);
}

//--------------------------------------------------------------------------------
//Example usage. Call "unileq file.unl" to run a file.

int main(int argc,char** argv) {
	unlstate* unl=unlcreate();
	if (argc<=1) {
		//Print a usage message. Use diverse syntax to test the interpreter.
		unlparsestr(
			unl,
			"neg m1 neg:main\n"
			"one:1 m1:main+1\n"
			"main:\n"
			"       #if len=0, goto -1\n"
			"       .len one main -?+ 01\n"
			"       4+? neg ?+1 #increment pointer\n"
			"       0-1 .data-1 main #|print a letter and loop|#"
			".data: 85 115 97 103 101 58 0x20 117 110 105 108 101"
			"       113 32 102 0x69 108 101 46 117 110 108 10 33 "
			"main.len: main.len-main.data"
		);
	} else {
		//Load a file.
		unlparsefile(unl,argv[1]);
	}
	//Main loop.
	unlrun(unl,-1);
	//Exit and print status if there was an error.
	u32 ret=unl->state;
	if (ret) {unlprintstate(unl);}
	unlfree(unl);
	return ret;
}

