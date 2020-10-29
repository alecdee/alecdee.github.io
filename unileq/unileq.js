/*
unileq.js - v1.00

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
which is set to 0 at the start of the program. The psuedocode below shows a
unileq instruction:

     A=mem[IP+0]
     B=mem[IP+1]
     C=mem[IP+2]
     if mem[A]<=mem[B]
          IP=C
     else
          IP=IP+3
     endif
     mem[A]=mem[A]-mem[B]

If A=-1, then instead of executing a normal instruction, B and C will be used to
interact with the interpreter. For example, if C=0, then the interpreter will
end execution of the current unileq program.

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
     multi line
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
     Adds or subtracts the number or label from the previous value. Parentheses
     are not supported. To express a negative number, use its unsigned form or
     the identity "0-x=-x".

     There cannot be two consecutive operators, ex: "0++1". Also, the program
     cannot begin or end with an operator.

Interpreter Calls
     If A=-1, a call will be sent to the interpreter and no jump will be taken.
     The effect of a call depends on B and C.

     C=0: End execution. B can be any value.
     C=1: mem[B] will be written to stdout.
     C=2: stdin will be written to mem[B].
*/

//--------------------------------------------------------------------------------
//64 bit unsigned integers.

function u64create(hi,lo) {
	//If arguments empty, initialize to 0.
	//If low is empty, assume high is a u64 and copy it.
	var n=new Object();
	if (hi===undefined) {
		n.hi=0;
		n.lo=0;
	} else if (lo===undefined) {
		n.hi=hi.hi;
		n.lo=hi.lo;
	} else {
		n.hi=hi;
		n.lo=lo;
	}
	return n;
}

function u64tostr(n) {
	//Powers of 10 split into high 32 bits and low 32 bits.
	var pot=[
		0x8ac72304,0x89e80000,0x0de0b6b3,0xa7640000,
		0x01634578,0x5d8a0000,0x002386f2,0x6fc10000,
		0x00038d7e,0xa4c68000,0x00005af3,0x107a4000,
		0x00000918,0x4e72a000,0x000000e8,0xd4a51000,
		0x00000017,0x4876e800,0x00000002,0x540be400,
		0x00000000,0x3b9aca00,0x00000000,0x05f5e100,
		0x00000000,0x00989680,0x00000000,0x000f4240,
		0x00000000,0x000186a0,0x00000000,0x00002710,
		0x00000000,0x000003e8,0x00000000,0x00000064,
		0x00000000,0x0000000a,0x00000000,0x00000001
	];
	var nh=n.hi,nl=n.lo;
	var str="";
	for (var i=0;i<40;i+=2) {
		var dh=pot[i],dl=pot[i+1];
		var digit=48;
		while (nh>dh || (nh===dh && nl>=dl)) {
			digit++;
			nl-=dl;
			nh-=dh;
			if (nl<0) {
				nl+=0x100000000;
				nh--;
			}
		}
		if (str!=="" || digit>48) {
			str+=String.fromCharCode(digit);
		}
	}
	return str===""?"0":str;
}

function u64set(a,b) {
	//a=b
	a.lo=b.lo;
	a.hi=b.hi;
}

function u64zero(n) {
	//n=0
	n.lo=0;
	n.hi=0;
}

function u64cmp(a,b) {
	//if a<b, return -1
	//if a=b, return  0
	//if a>b, return  1
	var ah=a.hi,bh=b.hi;
	if (ah!==bh) {return ah<bh?-1:1;}
	var al=a.lo,bl=b.lo;
	if (al!==bl) {return al<bl?-1:1;}
	return 0;
}

function u64sub(r,a,b) {
	//r=a-b
	//return true if a<=b
	r.lo=a.lo-b.lo;
	r.hi=a.hi-b.hi;
	if (r.lo<0) {
		r.lo+=0x100000000;
		r.hi--;
	}
	if (r.hi<0) {
		r.hi+=0x100000000;
		return true;
	}
	return r.hi===0 && r.lo===0;
}

function u64add(r,a,b) {
	//r=a+b
	r.lo=a.lo+b.lo;
	r.hi=a.hi+b.hi;
	if (r.lo>=0x100000000) {
		r.lo-=0x100000000;
		r.hi++;
	}
	if (r.hi>=0x100000000) {
		r.hi-=0x100000000;
	}
}

function u64inc(n) {
	//n++
	n.lo++;
	if (n.lo>=0x100000000) {
		n.lo=0;
		n.hi++;
		if (n.hi>=0x100000000) {
			n.hi=0;
		}
	}
	return n;
}

//--------------------------------------------------------------------------------
//Labels.

function unllabelalloc() {
}

function unllabelcreate(lbl,scope,data,pos,len) {
	//Count .'s to determine the current label's depth. If we're shallow, travel up
	//to a higher scope.
	var depth=0;
	for (;depth<len && data[depth]==='.';depth++);
	while (scope.depth>depth) {scope=scope.scope;}
	depth=scope.depth;
	lbl.scope=scope;
	lbl.depth=depth+1;
	//Offset the data position by the parent scope's depth.
	depth-=depth>0;
	lbl.data=data;
	lbl.len=len+scope.len-depth;
	lbl.pos=pos+depth-lbl.len;
	return lbl;
}

function unllabelcmp(ls,rs) {
	//Compare two labels from their last character to their first along with any
	//scope characters.
	var lv=null,rv=null,lc,rc,data=ls.data;
	var llen=ls.len,rlen=rs.len;
	if (llen!==rlen) {return llen<rlen?-1:1;}
	for (var i=llen-1;i!==-1;i--) {
		if (i<llen) {lv=ls;ls=ls.scope;llen=ls.len;}
		if (i<rlen) {rv=rs;rs=rs.scope;rlen=rs.len;}
		if (lv===rv) {return 0;}
		lc=data[i+lv.pos];
		rc=data[i+rv.pos];
		if (lc!==rc) {return lc<rc?-1:1;}
	}
	return 0;
}

/*typedef struct unllabel {
	struct unllabel *next,*scope;
	const uchar* data;
	u64 addr;
	u32 hash,len,depth;
} unllabel;

typedef struct unlhashmap {
	unllabel** map;
	u32 mask;
} unlhashmap;

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
			unllabel *lbl,*next=map->map[i];
			while ((lbl=next)) {
				next=lbl->next;
				free(lbl);
			}
		}
		free(map->map);
		free(map);
	}
}

unllabel* unllabelinit(unlhashmap* map,unllabel* lbl,unllabel* scope,const uchar* data,u32 len) {
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
	lbl->data=data+depth-scope->len;
	lbl->len=len+scope->len-depth;
	//Compute the hash of the label. Use the scope's hash to speed up computation.
	u32 hash=scope->hash;
	for (u32 i=scope->len;i<lbl->len;i++) {
		hash+=lbl->data[i]+i;
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
}*/

//--------------------------------------------------------------------------------

var UNL_RUNNING     =1;
var UNL_ERROR_PARSER=2;

function unlcreate(str,output) {
	var st=new Object();
	st.memtree=null;
	st.ip=0;
	st.state=0;
	st.errorstr="";
	st.running=0;
	st.output=output;
	unlparsestr(st,str);
	return st;
}

function unlclear(st) {
}

function unlparsestr(st,str) {
	unlclear(st);
	console.log("parsing");
	console.log(str);
}

//--------------------------------------------------------------------------------
//Editor.

var unleditorstate=null;
function unlupdate() {
	var st=unleditorstate;
	if (st===null || st.running===0) {return;}
	unladvance(st,1000);
}

function unlsetup(runid,resetid,inputid,outputid) {
	var runbutton=document.getElementById(runid);
	var resetbutton=document.getElementById(resetid);
	var input=document.getElementById(inputid);
	var output=document.getElementById(outputid);
	var st=unlcreate("",output);
	runbutton.onclick=function() {
		st.running=1-st.running;
		if (st.state===0) {
			unlparsestr(st,input.value);
			if (st.state===0) {st.running=0;}
		}
		runbutton.innerText=["Run","Stop"][st.running];
	};
	resetbutton.onclick=function() {
		st.state=0;
		st.running=0;
		output.innerText="";
		runbutton.innerText="Run";
	};
	unleditorstate=st;
	setInterval(unlupdate,1000.0/60.0);
}

var a=u64create(0xffffffff,0xffffffff);
var b=u64create(0x0,10);
var c=u64create();
console.log(u64sub(c,a,a));
console.log(u64tostr(b));
