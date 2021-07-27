/*
unileq.js - v1.11

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
of legos while using only one type of lego piece. Since we only have one
instruction, most modern conveniences are gone. Things like multiplying numbers
or memory allocation need to built from scratch using unileq's instruction.

The instruction is fairly simple: Given A, B, and C, compute mem[A]-mem[B] and
store the result in mem[A]. Then, if mem[A] was less than or equal to mem[B],
jump to C. Otherwise, jump by 3. We use the instruction pointer (IP) to keep
track of our place in memory. The python code below shows a unileq instruction:

     A, B, C = mem[IP+0], mem[IP+1], mem[IP+2]
     IP = C if mem[A] <= mem[B] else (IP+3)
     mem[A] = mem[A] - mem[B]

The instruction pointer and memory values are all 64 bit unsigned integers.
Overflow and underflow are handled by wrapping values around to be between 0 and
2^64-1 inclusive.

If A=-1, then instead of executing a normal instruction, B and C will be used to
interact with the interpreter. For example, if C=0, then the interpreter will
end execution of the current unileq program.

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

Interpreter Calls
     If A=-1, a call will be sent to the interpreter and no jump will be taken.
     The effect of a call depends on B and C.

     C=0: End execution. B can be any value.
     C=1: mem[B] will be written to stdout.
     C=2: stdin will be written to mem[B].

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
//64 bit unsigned integers.

function unlu64create(hi,lo) {
	//If arguments empty, initialize to 0.
	if (hi===undefined) {
		hi=0;
		lo=0;
	} else if (lo===undefined) {
		if (hi instanceof Object) {
			lo=hi.lo;
			hi=hi.hi;
		} else {
			lo=hi;
			hi=0;
		}
	}
	return {lo:lo,hi:hi};
}

function unlu64tostr(n) {
	//Convert a 64-bit number to its base 10 representation.
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
	var nl=n.lo,nh=n.hi,str="";
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

function unlu64cmp(a,b) {
	//if a<b, return -1
	//if a=b, return  0
	//if a>b, return  1
	if (a.hi!==b.hi) {return a.hi<b.hi?-1:1;}
	if (a.lo!==b.lo) {return a.lo<b.lo?-1:1;}
	return 0;
}

function unlu64set(a,b) {
	//a=b
	a.lo=b.lo;
	a.hi=b.hi;
}

function unlu64zero(n) {
	//n=0
	n.lo=0;
	n.hi=0;
}

function unlu64iszero(n) {
	//n==0
	return n.lo===0 && n.hi===0;
}

function unlu64sub(r,a,b) {
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

function unlu64add(r,a,b) {
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

function unlu64mul(r,a,b) {
	//r=a*b
	var a0=a.lo&0xffff,a1=a.lo>>>16;
	var a2=a.hi&0xffff,a3=a.hi>>>16;
	var b0=b.lo&0xffff,b1=b.lo>>>16;
	var b2=b.hi&0xffff;
	var m=a0*b1+a1*b0,lo,hi;
	hi=a0*b.hi+a1*b1+a2*b.lo+(m>>>16);
	lo=a0*b0+((m<<16)>>>0);
	if ( m>=0x100000000) {hi+=0x10000;}
	if (lo>=0x100000000) {hi++;}
	hi+=(a1*b2+a3*b0)<<16;
	r.lo=lo>>>0;
	r.hi=hi>>>0;
}

function unlu64inc(n) {
	//n++
	if ((++n.lo)>=0x100000000) {
		n.lo=0;
		if ((++n.hi)>=0x100000000) {
			n.hi=0;
		}
	}
}

function unlu64dec(n) {
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
		addr:unlu64create()
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
	unlu64set(dst.addr,lbl.addr);
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
		memh:[0],
		meml:[0],
		alloc:0,
		ip:unlu64create(),
		state:0,
		statestr:""
	};
	unlclear(st);
	return st;
}

function unlclear(st) {
	st.state=UNL_COMPLETE;
	st.statestr="";
	unlu64zero(st.ip);
	st.memh=[0];
	st.meml=[0];
	st.alloc=0;
	if (st.output!==null) {
		st.output.value="";
	}
}

function unlprint(st,str) {
	//Print to output and autoscroll to bottom.
	var output=st.output;
	if (output!==null) {
		var newtext=output.value+str;
		if (newtext.length>4096) {
			newtext=newtext.substring(0,4096);
		}
		output.value=newtext;
		output.scrollTop=output.scrollHeight;
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
	var lbl0=unllabelalloc();
	for (var pass=0;pass<2 && err===null;pass++) {
		var scope=null,lbl=null;
		var addr=unlu64create(),val=unlu64create(),acc=unlu64create();
		var tmp0=unlu64create(),tmp1=unlu64create();
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
				if (unlu64iszero(addr)) {err="Leading operator";}
				unlu64dec(addr);
				op=c;
				NEXT();
			} else if (CNUM(c)<10) {
				//Number. If it starts with "0x", use hexadecimal.
				token=10;
				unlu64zero(val);
				if (c===48 && (NEXT()===120 || c===88)) {token=16;NEXT();}
				tmp0.lo=token;
				while ((tmp1.lo=CNUM(c))<token) {
					unlu64mul(val,val,tmp0);
					unlu64add(val,val,tmp1);
					NEXT();
				}
			} else if (c===63) {
				//Current address token.
				token=1;
				unlu64set(val,addr);
				NEXT();
			} else if (ISLBL(c)) {
				//Label.
				while (ISLBL(c)) {NEXT();}
				lbl=unllabelinit(map,lbl0,scope,str,j-1,i-j);
				if (c===58) {
					//Label declaration.
					if (pass===0) {
						if (lbl!==null) {err="Duplicate label declaration";}
						unlu64set(lbl0.addr,addr);
						lbl=unllabeladd(map,lbl0);
						if (lbl===null) {err="Unable to allocate label";}
					}
					scope=lbl;
					if (ISOP(op)) {err="Operating on declaration";}
					op=c;
					NEXT();
				} else {
					token=1;
					if (lbl!==null) {unlu64set(val,lbl.addr);}
					else if (pass!==0) {err="Unable to find label";}
				}
			} else {
				err="Unexpected token";
				i++;
			}
			if (token!==0) {
				//Add a new value to memory.
				if (op===43) {unlu64add(val,acc,val);}
				else if (op===45) {unlu64sub(val,acc,val);}
				else if (pass!==0) {
					unlu64dec(addr);
					unlsetmem(st,addr,acc);
					unlu64inc(addr);
				}
				unlu64inc(addr);
				unlu64set(acc,val);
				op=0;
				if (ISLBL(c) || c===63) {err="Unseparated tokens";}
			}
		}
		if (err===null && ISOP(op)) {err="Trailing operator";}
		if (pass!==0) {
			unlu64dec(addr);
			unlsetmem(st,addr,acc);
			unlu64inc(addr);
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

function unlgetmem(st,addr) {
	//Return the memory value at addr.
	var i=addr.lo;
	if (addr.hi===0 && i<st.alloc) {
		return unlu64create(st.memh[i],st.meml[i]);
	} else {
		return unlu64create();
	}
}

function unlsetmem(st,addr,val) {
	//Write val to the memory at addr.
	var pos=addr.lo;
	if (addr.hi!==0 || pos>=st.alloc) {
		//If we're writing to an address outside of our memory, attempt to resize it or
		//error out.
		if (unlu64iszero(val)) {return;}
		//Find the maximum we can allocate.
		var alloc=1,memh=null,meml=null;
		while (alloc<=pos) {alloc+=alloc;}
		//Attempt to allocate.
		if (addr.hi===0 && alloc>pos) {
			try {
				memh=new Uint32Array(alloc+1);
				meml=new Uint32Array(alloc+1);
			} catch(error) {
				memh=null;
				meml=null;
			}
		}
		if (memh!==null && meml!==null) {
			var omemh=st.memh,omeml=st.meml,oalloc=st.alloc;
			for (var i=0;i<oalloc;i++) {
				memh[i]=omemh[i];
				meml[i]=omeml[i];
			}
			for (;i<=alloc;i++) {
				memh[i]=0;
				meml[i]=0;
			}
			st.memh=memh;
			st.meml=meml;
			st.alloc=alloc;
		} else {
			st.state=UNL_ERROR_MEMORY;
			st.statestr="Failed to allocate memory.\nIndex: "+unlu64tostr(addr)+"\n";
			return;
		}
	}
	st.memh[pos]=val.hi;
	st.meml[pos]=val.lo;
}

function unlrun_standard(st,iters) {
	//Run unileq for a given number of iterations. If iters=-1, run forever.
	var dec=iters>=0?1:0;
	var a,b,c,ma,mb,ip=st.ip;
	for (;iters!==0 && st.state===UNL_RUNNING;iters-=dec) {
		//Load a, b, and c.
		a=unlgetmem(st,ip);unlu64inc(ip);
		b=unlgetmem(st,ip);unlu64inc(ip);
		c=unlgetmem(st,ip);unlu64inc(ip);
		mb=unlgetmem(st,b);
		if (a.hi!==0xffffffff || a.lo!==0xffffffff) {
			//Execute a normal unileq instruction.
			ma=unlgetmem(st,a);
			if (unlu64sub(ma,ma,mb)) {
				unlu64set(ip,c);
			}
			unlsetmem(st,a,ma);
		} else if (c.hi===0) {
			//Otherwise, call the interpreter.
			if (c.lo===0) {
				//Exit.
				st.state=UNL_COMPLETE;
			} else if (c.lo===1) {
				//Write mem[b] to stdout.
				unlprint(st,String.fromCharCode(unlgetmem(st,mb).lo&255));
			}
		}
	}
}

function unlrun(st,iters) {
	//Run unileq for a given number of iterations. If iters=-1, run forever.
	//This version of unlrun() unrolls several operations to speed things up.
	if (st.state!==UNL_RUNNING) {return;}
	var a,b,c,ma,mb;
	var pos=st.ip,tmp=unlu64create();
	var lo,hi,iplo=pos.lo,iphi=pos.hi;
	var memh=st.memh,meml=st.meml,alloc=st.alloc;
	iters=iters<0?Infinity:iters;
	for (;iters>0;iters--) {
		//Load a, b, and c.
		if (iphi===0 && iplo<0xfffffffd) {
			a=iplo<alloc?iplo:alloc;iplo++;
			b=iplo<alloc?iplo:alloc;iplo++;
			c=iplo<alloc?iplo:alloc;iplo++;
		} else {
			a=(iphi===0 && iplo<alloc)?iplo:alloc;
			if ((++iplo)>=0x100000000) {iplo=0;iphi=(iphi+1)>>>0;}
			b=(iphi===0 && iplo<alloc)?iplo:alloc;
			if ((++iplo)>=0x100000000) {iplo=0;iphi=(iphi+1)>>>0;}
			c=(iphi===0 && iplo<alloc)?iplo:alloc;
			if ((++iplo)>=0x100000000) {iplo=0;iphi=(iphi+1)>>>0;}
		}
		//Execute a normal unileq instruction.
		mb=meml[b];
		mb=(memh[b]===0 && mb<alloc)?mb:alloc;
		ma=meml[a];
		if (memh[a]===0 && ma<alloc) {
			//In bounds.
			if (ma!==mb) {
				lo=meml[ma]-meml[mb];
				hi=memh[ma]-memh[mb];
				if (lo<0) {
					lo+=0x100000000;
					hi--;
				}
				if (hi<0) {
					hi+=0x100000000;
					iplo=meml[c];
					iphi=memh[c];
				} else if (hi===0 && lo===0) {
					iplo=meml[c];
					iphi=memh[c];
				}
				meml[ma]=lo;
				memh[ma]=hi;
			} else {
				//Zeroing out an address (ma==mb) occurs 30% of the time.
				iplo=meml[c];
				iphi=memh[c];
				meml[ma]=0;
				memh[ma]=0;
			}
		} else if (memh[a]!==0xffffffff || ma!==0xffffffff) {
			//Out of bounds. Need to expand memory. Assume mem[a]=0.
			iphi=memh[c];
			iplo=meml[c];
			lo=-meml[mb];
			hi=-memh[mb];
			if (lo<0) {
				lo+=0x100000000;
				hi--;
			}
			tmp.hi=hi<0?hi+0x100000000:hi;
			tmp.lo=lo;
			pos.hi=memh[a];
			pos.lo=ma;
			unlsetmem(st,pos,tmp);
			if (st.state!==UNL_RUNNING) {break;}
			memh=st.memh;
			meml=st.meml;
			alloc=st.alloc;
		} else if (memh[c]===0) {
			//Otherwise, call the interpreter.
			c=meml[c];
			if (c===0) {
				//Exit.
				st.state=UNL_COMPLETE;
				break;
			} else if (c===1) {
				//Write mem[b] to stdout.
				unlprint(st,String.fromCharCode(meml[mb]&255));
			}
		}
	}
	pos.hi=iphi;
	pos.lo=iplo;
}
