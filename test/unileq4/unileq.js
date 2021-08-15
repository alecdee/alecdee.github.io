/*
unileq.js - v1.12

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

The goal of unileq is to create the functionality of a normal computer using
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
Because there's only one instruction, we can omit any notation specifying what
instruction to execute on some given memory values. The flow of the program will
decide what gets executed and what doesn't.

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

Input/Output
     Interaction with the host environment can be done by setting A or B to
     special addresses.

     A=-1: End execution.
     A=-2: Write mem[B] to stdout.
     B=-3: Read stdin to mem[A].
     B=-4: Read current time to mem[A].

--------------------------------------------------------------------------------
TODO

Webassembly speedup isn't that great compared to unlrun(). Wait until better
integration with javascript.
Audio
Graphics
Mouse+Keyboard

*/
/*jshint bitwise: false*/
/*jshint eqeqeq: true*/

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
		addr:0
	};
}

function unllabelcmp(ls,rs) {
	//Compare two labels from their last character to their first along with any
	//scope characters.
	var lv=null,rv=null,lc,rc,data=ls.data;
	var llen=ls.len,rlen=rs.len;
	if (llen!==rlen) {return llen<rlen?-1:1;}
	for (var i=llen-1;i!==-1;i--) {
		if (i<llen) {lv=ls;ls=ls.scope;llen=ls!==null?ls.len:0;}
		if (i<rlen) {rv=rs;rs=rs.scope;rlen=rs!==null?rs.len:0;}
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
	while (scope!==null && scope.depth>depth) {scope=scope.scope;}
	depth=scope!==null?scope.depth:0;
	var hash=scope!==null?scope.hash:0;
	var scopelen=scope!==null?scope.len:0;
	lbl.scope=scope;
	lbl.depth=depth+1;
	//Offset the data address by the parent scope's depth.
	var dif=scopelen-depth+(depth>0);
	lbl.data=data;
	lbl.pos=pos-dif;
	lbl.len=len+dif;
	//Compute the hash of the label. Use the scope's hash to speed up computation.
	for (i=scopelen;i<lbl.len;i++) {
		hash+=data.charCodeAt(lbl.pos+i)+i;
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
	dst.addr=lbl.addr;
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
		outbuf:"",
		mem:null,
		alloc:0,
		ip:0,
		mod:0x100000000,
		mask:0,
		state:0,
		statestr:""
	};
	st.mask=st.mod-1;
	unlclear(st);
	return st;
}

function unlclear(st) {
	st.state=UNL_COMPLETE;
	st.statestr="";
	st.ip=0;
	st.mem=[0];
	st.alloc=0;
	if (st.output!==null) {
		st.output.value="";
	}
	st.outbuf="";
}

function unlprint(st,str) {
	//Print to output and autoscroll to bottom. If output is null, print to console.
	var output=st.output;
	if (output!==null) {
		str=output.value+str;
		if (str.length>8192) {
			str=str.substring(str.length-4096);
		}
		output.value=str;
		output.scrollTop=output.scrollHeight;
	} else {
		str=(st.outbuf+str).split("\n");
		for (var i=0;i<str.length-1;i++) {
			console.log(str[i]);
		}
		st.outbuf=str[str.length-1];
	}
}

function unlparsestr(st,str) {
	//Convert unileq assembly language into a unileq program.
	unlclear(st);
	st.state=UNL_RUNNING;
	var i=0,j=0,len=str.length;
	var c,op,err=null;
	var mask=st.mask;
	function  CNUM(c) {return (c<=57?c+208:((c+191)&~32)+10)&255;}
	function ISLBL(c) {return CNUM(c)<36 || c===95 || c===46 || c>127;}
	function  ISOP(c) {return c===43 || c===45;}
	function   NEXT() {return (c=i++<len?str.charCodeAt(i-1):0);}
	if (len>=UNL_MAX_PARSE) {err="Input string too long";}
	//Process the string in 2 passes. The first pass is needed to find label values.
	var map=unlhashcreate();
	if (map===null) {err="Unable to allocate hash map";}
	var lbl0=unllabelalloc();
	for (var pass=0;pass<2 && err===null;pass++) {
		var scope=null,lbl=null;
		var addr=0,val=0,acc=0;
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
				var nmask=0,eoc=10,i0=i;
				if (NEXT()===124) {nmask=255;eoc=31779;NEXT();}
				while (c!==0 && n!==eoc) {n=((n&nmask)<<8)+c;NEXT();}
				if (nmask!==0 && n!==eoc) {err="Unterminated block quote";j=i0;}
				continue;
			}
			j=i;
			if (ISOP(c)) {
				//Operator. Decrement addr since we're modifying the previous value.
				if (op!==0 ) {err="Double operator";}
				if (op===58) {err="Operating on declaration";}
				if (addr===0) {err="Leading operator";}
				addr--;
				op=c;
				NEXT();
			} else if (CNUM(c)<10) {
				//Number. If it starts with "0x", use hexadecimal.
				token=10;
				val=0;
				if (c===48 && (NEXT()===120 || c===88)) {token=16;NEXT();}
				while ((n=CNUM(c))<token) {
					val=((val*token)&mask)+n;
					NEXT();
				}
			} else if (c===63) {
				//Current address token.
				token=1;
				val=addr;
				NEXT();
			} else if (ISLBL(c)) {
				//Label.
				while (ISLBL(c)) {NEXT();}
				lbl=unllabelinit(map,lbl0,scope,str,j-1,i-j);
				if (c===58) {
					//Label declaration.
					if (pass===0) {
						if (lbl!==null) {err="Duplicate label declaration";}
						lbl0.addr=addr;
						lbl=unllabeladd(map,lbl0);
						if (lbl===null) {err="Unable to allocate label";}
					}
					scope=lbl;
					if (ISOP(op)) {err="Operating on declaration";}
					op=c;
					NEXT();
				} else {
					token=1;
					if (lbl!==null) {val=lbl.addr;}
					else if (pass!==0) {err="Unable to find label";}
				}
			} else {
				err="Unexpected token";
				i++;
			}
			if (token!==0) {
				//Add a new value to memory.
				if (op===43) {val=(acc+val)&mask;}
				else if (op===45) {val=(acc-val)&mask;}
				else if (pass!==0) {unlsetmem(st,addr-1,acc);}
				addr++;
				acc=val;
				op=0;
				if (ISLBL(c) || c===63) {err="Unseparated tokens";}
			}
		}
		if (err===null && ISOP(op)) {err="Trailing operator";}
		if (pass!==0) {unlsetmem(st,addr-1,acc);}
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

function unlgetmem(st,addr) {
	//Return the memory value at addr.
	return addr<st.alloc?st.mem[addr]:0;
}

function unlsetmem(st,addr,val) {
	//Write val to the memory at addr.
	addr&=st.mask;
	if (addr<0) {addr+=st.mod;}
	val&=st.mask;
	if (val<0) {val+=st.mod;}
	if (addr>=st.alloc) {
		//If we're writing to an address outside of our memory, attempt to resize it or
		//error out.
		if (val===0) {return;}
		//Find the maximum we can allocate.
		var alloc=1,mem=null;
		while (alloc<=addr) {alloc+=alloc;}
		//Attempt to allocate.
		if (alloc>addr) {
			try {
				mem=new Uint32Array(alloc);
			} catch(error) {
				mem=null;
			}
		}
		if (mem!==null) {
			var origmem=st.mem,origalloc=st.alloc;
			for (var i=0;i<origalloc;i++) {
				mem[i]=origmem[i];
			}
			for (;i<=alloc;i++) {
				mem[i]=0;
			}
			st.mem=mem;
			st.alloc=alloc;
		} else {
			st.state=UNL_ERROR_MEMORY;
			st.statestr="Failed to allocate memory.\nIndex: "+addr+"\n";
			return;
		}
	}
	st.mem[addr]=val;
}

function unlrun(st,iters) {
	//Run unileq for a given number of iterations. If iters<0, run forever.
	if (st.state!==UNL_RUNNING) {
		return;
	}
	//Performance testing.
	if (st.ip.hi===0 && st.ip.lo===0) {
		unlrun.instructions=0;
		unlrun.time=0;
	}
	unlrun.instructions+=iters;
	unlrun.time-=performance.now();
	var mod=st.mod;
	var a,b,c,mb,dif,ip=st.ip,io=mod-4;
	var mem=st.mem,alloc=st.alloc;
	iters=iters<0?Infinity:iters;
	for (;iters>0;iters--) {
		//Load a, b, and c.
		if (ip+2<alloc) {
			a=mem[ip++];
			b=mem[ip++];
			c=mem[ip++];
		} else {
			a=ip<alloc?mem[ip]:0;
			if (++ip>=mod) {ip-=mod;}
			b=ip<alloc?mem[ip]:0;
			if (++ip>=mod) {ip-=mod;}
			c=ip<alloc?mem[ip]:0;
			if (++ip>=mod) {ip-=mod;}
		}
		//Input
		if (b<alloc) {
			//Read mem[b].
			mb=mem[b];
		} else if (b<io) {
			mb=0;
		} else if (b===mod-3) {
			//Read stdin.
		} else if (b===mod-4) {
			//Read time.
			mb=Date.now()&(mod-1);
		} else {
			mb=0;
		}
		//Output
		//Execute a normal unileq instruction.
		if (a<alloc) {
			dif=mem[a]-mb;
			if (dif<0) {
				mem[a]=dif+0x100000000;
			} else {
				mem[a]=dif;
				if (dif!==0) {continue;}
			}
		} else if (a<io) {
			unlsetmem(st,a,-mb);
			if (st.state!==UNL_RUNNING) {
				break;
			}
			mem=st.mem;
			alloc=st.alloc;
		} else if (a===mod-1) {
			//Exit.
			st.state=UNL_COMPLETE;
			break;
		} else if (a===mod-2) {
			//Print to stdout.
			unlprint(st,String.fromCharCode(mb));
		}
		ip=c;
	}
	st.ip=ip;
	//Performance testing.
	unlrun.time+=performance.now();
	if (st.state!==UNL_RUNNING) {
		var freq=(unlrun.instructions-(iters+1))*1000.0/unlrun.time;
		unlprint(st,"Speed: "+freq.toFixed(0)+" Hz\n");
	}
}
