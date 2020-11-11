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
The Unileq Architecture

Whereas most computer architectures have hundreds or thousands of different
instructions that can be used to build a program, unileq has only one
instruction. Unileq's one instruction is simple: it performs a subtraction and
then jumps. Despite its simplicity, we can use this instruction to create any
program we want. Unileq is based off of subleq.

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

--------------------------------------------------------------------------------
TODO

Optimize unlrun().
*/
/*jshint bitwise: false*/
/*jshint eqeqeq: true*/

//--------------------------------------------------------------------------------
//64 bit unsigned integers.

function u64create(hi,lo) {
	//If arguments empty, initialize to 0.
	//If low is empty, assume high is a u64 and copy it.
	if (hi===undefined) {
		hi=0;
		lo=0;
	} else if (lo===undefined) {
		lo=hi;
		hi=0;
	}
	return {lo:lo,hi:hi};
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
	var nh=n.hi,nl=n.lo,str="";
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

function u64iszero(n) {
	//n==0
	return n.lo===0 && n.hi===0;
}

function u64sub(r,a,b) {
	//r=a-b
	//return true if a<=b
	var lo,hi;
	lo=a.lo-b.lo;
	hi=a.hi-b.hi;
	if (lo<0) {
		lo+=0x100000000;
		hi--;
	}
	r.lo=lo;
	if (hi<0) {
		r.hi=hi+0x100000000;
		return true;
	}
	r.hi=hi;
	return hi===0 && lo===0;
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

function u64mul(r,a,b) {
	var t=u64create();
	for (var i=31;i>=0;i--) {
		u64add(t,t,t);
		if ((b.hi&(1<<i))!==0) {
			u64add(t,t,a);
		}
	}
	for (i=31;i>=0;i--) {
		u64add(t,t,t);
		if ((b.lo&(1<<i))!==0) {
			u64add(t,t,a);
		}
	}
	u64set(r,t);
}

function u64inc(n) {
	//n++
	if ((++n.lo)>=0x100000000) {
		n.lo=0;
		if ((++n.hi)>=0x100000000) {
			n.hi=0;
		}
	}
}

function u64dec(n) {
	//n--
	if ((--n.lo)<0) {
		n.lo=0xffffffff;
		if ((--n.hi)<0) {
			n.hi=0xffffffff;
		}
	}
}

//--------------------------------------------------------------------------------
//Labels.

function unllabelalloc() {
	return {
		next:null,
		scope:null,
		data:null,
		pos:0,
		len:0,
		hash:0,
		depth:0,
		addr:u64create()
	};
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

function unlhashcreate() {
	var mask=(1<<20)-1;
	var map=new Array(mask+1);
	for (var i=0;i<=mask;i++) {
		map[i]=null;
	}
	return {mask:mask,map:map};
}

function unllabelinit(map,lbl,scope,data,pos,len) {
	//Initialize a label and return a match if we find one.
	//Count .'s to determine what scope we should be in.
	var s="";
	for (var i=0;i<len;i++) {
		s+=data[pos+i];
	}
	var depth=0;
	while (depth<len && data[pos+depth]==='.') {depth++;}
	while (scope.depth>depth) {scope=scope.scope;}
	depth=scope.depth;
	lbl.scope=scope;
	lbl.depth=depth+1;
	//Offset the data address by the parent scope's depth.
	depth-=depth>0;
	lbl.data=data;
	lbl.pos=pos+depth-scope.len;
	lbl.len=len+scope.len-depth;
	//Compute the hash of the label. Use the scope's hash to speed up computation.
	var hash=scope.hash;
	for (i=scope.len;i<lbl.len;i++) {
		hash+=lbl.data.charCodeAt(lbl.pos+i)+i;
		hash&=0xffffffff;
		hash=((hash>>9)|((hash&0x1ff)<<23));
		hash^=hash>>14;
		hash^=(hash&0xff)*0x00d75b4b;
	}
	lbl.hash=hash;
	//Search for a match.
	var match=map.map[hash&map.mask];
	while (match!==null && unllabelcmp(match,lbl)!==0) {
		match=match.next;
	}
	return match;
}

function unllabeladd(map,lbl) {
	var dst=unllabelalloc();
	dst.scope=lbl.scope;
	dst.data=lbl.data;
	dst.pos=lbl.pos;
	dst.len=lbl.len;
	dst.hash=lbl.hash;
	dst.depth=lbl.depth;
	u64set(dst.addr,lbl.addr);
	var hash=dst.hash&map.mask;
	dst.next=map.map[hash];
	map.map[hash]=dst;
	return dst;
}

//--------------------------------------------------------------------------------

var UNL_RUNNING     =0;
var UNL_COMPLETE    =1;
var UNL_ERROR_PARSER=2;
var UNL_ERROR_MEMORY=3;
var UNL_MAX_PARSE   =(1<<30);

function unlcreate(output) {
	var st={
		output:output,
		running:0,
		mem:null,
		alloc:0,
		ip:u64create(),
		state:0,
		statestr:""
	};
	unlclear(st);
	return st;
}

function unlclear(st) {
	st.state=UNL_COMPLETE;
	st.statestr="";
	u64zero(st.ip);
	st.mem=null;
	st.alloc=0;
	if (st.output!==null) {
		st.output.value="";
	}
}

function unlparsestr(st,str) {
	//Convert unileq assembly language into a unileq program.
	unlclear(st);
	st.state=UNL_RUNNING;
	var i=0,j=0,len=str.length;
	var c,op,err=null;
	function  CNUM(c) {return (c<=57?c+208:((c+191)&~32)+10)&255;}
	function ISLBL(c) {return CNUM(c)<36 || c===95 || c===46 || c>127;}
	function  ISOP(c) {return c===43 || c===45;}
	function   NEXT() {return (c=i++<len?str.charCodeAt(i-1):0);}
	if (len>=UNL_MAX_PARSE) {err="Input string too long";}
	//Process the string in 2 passes. The first pass is needed to find label values.
	var map=unlhashcreate();
	if (map===null) {err="Unable to allocate hash map";}
	var scope0=unllabelalloc(),lbl0=unllabelalloc();
	for (var pass=0;pass<2 && err===null;pass++) {
		var scope=scope0,lbl=null;
		var addr=u64create(),val=u64create(),acc=u64create();
		op=0;
		i=0;
		NEXT();
		j=i;
		while (c!==0 && err===null) {
			var n=0,token=0;
			if (c===13 || c===10 || c===9 || c===32) {
				//Whitespace.
				NEXT();
				continue;
			}
			if (c===35) {
				//Comment. If next='|', use the multi-line format.
				var mask=0,eoc=10,i0=i;
				if (NEXT()===124) {mask=255;eoc=31779;NEXT();}
				while (c!==0 && n!==eoc) {n=((n&mask)<<8)+c;NEXT();}
				if (mask!==0 && n!==eoc) {err="Unterminated block quote";j=i0;}
				continue;
			}
			j=i;
			if (ISOP(c)) {
				//Operator. Decrement addr since we're modifying the previous value.
				if (op!==0 ) {err="Double operator";}
				if (op===58) {err="Operating on declaration";}
				if (u64iszero(addr)) {err="Leading operator";}
				u64dec(addr);
				op=c;
				NEXT();
			} else if (CNUM(c)<10) {
				//Number. If it starts with "0x", use hexadecimal.
				token=10;
				u64zero(val);
				if (c===48 && (NEXT()===120 || c===88)) {token=16;NEXT();}
				while ((n=CNUM(c))<token) {
					u64mul(val,val,u64create(token));
					u64add(val,val,u64create(n));
					NEXT();
				}
			} else if (c===63) {
				//Next address token.
				token=1;
				u64set(val,addr);
				NEXT();
			} else if (ISLBL(c)) {
				//Label.
				while (ISLBL(c)) {NEXT();}
				lbl=unllabelinit(map,lbl0,scope,str,j-1,i-j);
				if (c===58) {
					//Label declaration.
					if (pass===0) {
						if (lbl!==null) {err="Duplicate label declaration";}
						u64set(lbl0.addr,addr);
						lbl=unllabeladd(map,lbl0);
						if (lbl===null) {err="Unable to allocate label";}
					}
					scope=lbl;
					if (ISOP(op)) {err="Operating on declaration";}
					op=c;
					NEXT();
				} else {
					token=1;
					if (lbl!==null) {u64set(val,lbl.addr);}
					else if (pass!==0) {err="Unable to find label";}
				}
			} else {
				err="Unexpected token";
				i++;
			}
			if (token!==0) {
				//Add a new value to memory.
				if (op===43) {u64add(val,acc,val);}
				else if (op===45) {u64sub(val,acc,val);}
				else if (pass!==0) {
					u64dec(addr);
					unlsetmem(st,addr,acc);
					u64inc(addr);
				}
				u64inc(addr);
				u64set(acc,val);
				op=0;
				if (ISLBL(c) || c===63) {err="Unseparated tokens";}
			}
		}
		if (err===null && ISOP(op)) {err="Trailing operator";}
		if (pass!==0) {
			u64dec(addr);
			unlsetmem(st,addr,acc);
			u64inc(addr);
		}
	}
	if (err!==null) {
		//We've encountered a parsing error.
		st.state=UNL_ERROR_PARSER;
		st.statestr="Parser: "+err+"\n";
		if (i-- && j--)
		{
			var line=1;
			var window="",under="";
			//Find the boundaries of the line we're currently parsing.
			var s0=0,s1=j,k;
			for (k=0;k<j;k++) {
				if (str[k]==="\n") {
					line++;
					s0=k+1;
				}
			}
			while (s1<len && str[s1]!=="\n") {s1++;}
			//Trim whitespace.
			while (s0<s1 && str[s0  ]<=" ") {s0++;}
			while (s1>s0 && str[s1-1]<=" ") {s1--;}
			//Extract the line and underline the error.
			s0=j>s0+30?j-30:s0;
			for (k=0;k<61;k++,s0++) {
				c=s0<s1 && k<60?str[s0]:"";
				window+=c;
				under+=c && s0>=j && s0<i?"^":(c<=" "?c:" ");
			}
			st.statestr="Parser: "+err+"\nline "+line+":\n\t\""+window+"\"\n\t\""+under+"\"\n";
		}
	}
}

function unlgetmem(st,addr,ret) {
	//Return the memory value at addr.
	if (addr.hi===0 && addr.lo<st.alloc) {
		u64set(ret,st.mem[addr.lo]);
	} else {
		u64zero(ret);
	}
}

function unlsetmem(st,addr,val) {
	//Write val to the memory at addr.
	var pos=addr.lo;
	if (addr.hi!==0 || pos>=st.alloc) {
		//If we're writing to an address outside of our memory, attempt to resize it or
		//error out.
		if (u64iszero(val)) {return;}
		//Find the maximum we can allocate.
		var alloc=1,mem=null;
		while (alloc<=pos) {alloc+=alloc;}
		//Attempt to allocate.
		if (addr.hi===0 && alloc>pos) {
			mem=new Array(alloc);
		}
		if (mem!==null) {
			var omem=st.mem,oalloc=st.alloc;
			for (var i=0;i<alloc;i++) {
				mem[i]=i<oalloc?omem[i]:u64create();
			}
			st.mem=mem;
			st.alloc=alloc;
		} else {
			st.state=UNL_ERROR_MEMORY;
			st.statestr="Failed to allocate memory.\nIndex: "+u64tostr(addr)+"\n";
			return;
		}
	}
	u64set(st.mem[pos],val);
}

function unlrun(st,iters) {
	//Run unileq for a given number of iterations. If iters=-1, run forever.
	var dec=iters>=0?1:0;
	var a=u64create(),b=u64create(),c=u64create();
	var ma=u64create(),mb=u64create(),ip=st.ip;
	var output=st.output;
	for (;iters!==0 && st.state===UNL_RUNNING;iters-=dec) {
		//Load a, b, and c.
		unlgetmem(st,ip,a);u64inc(ip);
		unlgetmem(st,ip,b);u64inc(ip);
		unlgetmem(st,ip,c);u64inc(ip);
		//Execute a normal unileq instruction.
		unlgetmem(st,b,mb);
		if (a.hi!==0xffffffff || a.lo!==0xffffffff) {
			unlgetmem(st,a,ma);
			if (u64sub(ma,ma,mb)) {
				u64set(ip,c);
			}
			unlsetmem(st,a,ma);
			continue;
		}
		//Otherwise, call the interpreter.
		if (c.hi===0) {
			if (c.lo===0) {
				//Exit.
				st.state=UNL_COMPLETE;
			} else if (c.lo===1) {
				//Write mem[b] to stdout.
				if (output!==null) {
					output.value+=String.fromCharCode(mb.lo&255);
				}
			} else if (c.lo===2) {
				//Read stdin to mem[b].
				//unlsetmem(st,b,(uchar)getchar());
			}
		}
	}
}

//--------------------------------------------------------------------------------
//Editor.

function unlsetup(source,runid,resetid,inputid,outputid) {
	var runbutton=document.getElementById(runid);
	var resetbutton=document.getElementById(resetid);
	var input=document.getElementById(inputid);
	var output=document.getElementById(outputid);
	var st=unlcreate(output);
	if (source!==null) {
		st.running=1;
		unlparsestr(st,source);
	}
	if (runbutton!==null) {
		runbutton.onclick=function() {
			if (st.state===UNL_RUNNING) {
				st.running=1-st.running;
			} else {
				unlparsestr(st,input.value);
				st.running=1;
			}
			runbutton.innerText=["Resume","Stop"][st.running];
		};
	}
	if (resetbutton!==null) {
		resetbutton.onclick=function() {
			unlclear(st);
			st.running=0;
			if (runbutton!==null) {runbutton.innerText="Run";}
			if (source!==null) {unlparsestr(st,source);}
		};
	}
	var avg=0.0,avgden=0.0,avgprint=0;
	function update() {
		var text=st.running===0?"Resume":"Stop";
		if (st.state!==UNL_RUNNING && st.running!==0) {
			st.running=0;
			text="Run";
			if (st.state!==UNL_COMPLETE && output!==null) {
				output.value+=st.statestr;
			}
		}
		if (runbutton!==null && runbutton.innertext!==text) {
			runbutton.innerText=text;
		}
		if (st.running===0) {
			if (avgprint===0) {
				avgprint=1;
				var str="time: "+(avg/avgden).toFixed(6);
				if (output!==null) {output.value+=str+"\n";}
			}
			return;
		}
		var t0=performance.now();
		unlrun(st,250000);
		avg+=performance.now()-t0;
		avgden+=1000.0;
	}
	setInterval(update,1000.0/60.0);
	return st;
}

