/*
unileq.js - v1.14

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
     Interaction with the host environment can be done by reading or writing
     from special addresses.

     A = -1: End execution.
     A = -2: Write mem[B] to stdout.
     B = -3: Subtract stdin from mem[A].
     B = -4: Subtract current time from mem[A].

--------------------------------------------------------------------------------
Performance

Performance tests, measured in instructions per second:


                  |   Phone   |   Laptop  |   PC FF   |   PC CR
     -------------+-----------+-----------+-----------+-----------
      64 Bit Std  |   3604299 |   2646748 |   6951947 |  17073384
      64 Bit Fast |  19124087 |  36796100 |  97277391 |  97180701
      32 Bit Std  |  26121436 |  45665430 | 143715565 | 125252212


Tests should take 5 minutes or more. Tests run on a phone need to be run
several times to see the effect of thermal throttling.

Splitting into high/low arrays is about 8% faster than using interleaved memory.

Uint32Array is at least 5% faster than Float64Array across all hardware and
browsers.

When testing the math library, we jump 77% of the time. Delaying loading mem[C]
didn't provide a meaningful speedup.

Webassembly speedup isn't that great compared to UnlRun(). Wait until better
integration with javascript.

--------------------------------------------------------------------------------
TODO

Turn unl into an object.
Audio
Graphics
Mouse+Keyboard

*/
/*jshint bitwise: false*/
/*jshint eqeqeq: true  */
/*jshint curly: true   */

//--------------------------------------------------------------------------------
//64 bit unsigned integers.

function UnlU64Create(hi,lo) {
	if (hi===undefined) {
		//If arguments are empty, initialize to 0.
		hi=0;
		lo=0;
	} else if (lo===undefined) {
		if (hi.hi!==undefined) {
			//hi is another u64 object.
			lo=hi.lo;
			hi=hi.hi;
		} else if (hi>=0) {
			//hi is a positive number.
			lo=hi>>>0;
			hi=(hi/0x100000000)>>>0;
		} else {
			//hi is a negative number.
			lo=0x100000000-((-hi)>>>0);
			hi=0x0ffffffff-(((-hi)/0x100000000)>>>0);
			if (lo===0x100000000) {
				lo=0;
				hi++;
			}
		}
	}
	return {lo:lo,hi:hi};
}

function UnlU64ToStr(n) {
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

function UnlU64Cmp(a,b) {
	//if a<b, return -1
	//if a=b, return  0
	//if a>b, return  1
	if (a.hi!==b.hi) {return a.hi<b.hi?-1:1;}
	if (a.lo!==b.lo) {return a.lo<b.lo?-1:1;}
	return 0;
}

function UnlU64Set(a,b) {
	//a=b
	a.lo=b.lo;
	a.hi=b.hi;
}

function UnlU64Zero(n) {
	//n=0
	n.lo=0;
	n.hi=0;
}

function UnlU64IsZero(n) {
	//n==0
	return n.lo===0 && n.hi===0;
}

function UnlU64Neg(r,a) {
	//r=-a
	r.lo=0x100000000-a.lo;
	r.hi= 0xffffffff-a.hi;
	if (r.lo>=0x100000000) {
		r.lo=0;
		if ((++r.hi)>=0x100000000) {
			r.hi=0;
		}
	}
}

function UnlU64Sub(r,a,b) {
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

function UnlU64Add(r,a,b) {
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

function UnlU64Mul(r,a,b) {
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

function UnlU64Inc(n) {
	//n++
	if ((++n.lo)>=0x100000000) {
		n.lo=0;
		if ((++n.hi)>=0x100000000) {
			n.hi=0;
		}
	}
}

function UnlU64Dec(n) {
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

function UnlLabelAlloc() {
	return {
		next:null,
		scope:null,
		data:null,
		pos:0,
		len:0,
		hash:0,
		depth:0,
		addr:UnlU64Create()
	};
}

function UnlLabelCmp(ls,rs) {
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

function UnlHashCreate() {
	var mask=(1<<20)-1;
	var map=new Array(mask+1);
	for (var i=0;i<=mask;i++) {
		map[i]=null;
	}
	return {mask:mask,map:map};
}

function UnlLabelInit(map,lbl,scope,data,pos,len) {
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
	while (match!==null && UnlLabelCmp(match,lbl)!==0) {
		match=match.next;
	}
	return match;
}

function UnlLabelAdd(map,lbl) {
	var dst=UnlLabelAlloc();
	dst.scope=lbl.scope;
	dst.data=lbl.data;
	dst.pos=lbl.pos;
	dst.len=lbl.len;
	dst.hash=lbl.hash;
	dst.depth=lbl.depth;
	UnlU64Set(dst.addr,lbl.addr);
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

function UnlCreate(output) {
	var st={
		output:output,
		outbuf:"",
		memh:null,
		meml:null,
		alloc:0,
		ip:UnlU64Create(),
		state:0,
		statestr:""
	};
	UnlClear(st);
	return st;
}

function UnlClear(st) {
	st.state=UNL_COMPLETE;
	st.statestr="";
	UnlU64Zero(st.ip);
	st.memh=null;
	st.meml=null;
	st.alloc=0;
	if (st.output!==null) {
		st.output.value="";
	}
	st.outbuf="";
}

function UnlPrint(st,str) {
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

function UnlParseStr(st,str) {
	//Convert unileq assembly language into a unileq program.
	UnlClear(st);
	st.state=UNL_RUNNING;
	var i=0,j=0,len=str.length;
	var c,op,err=null;
	function  CNUM(c) {return (c<=57?c+208:((c+191)&~32)+10)&255;}
	function ISLBL(c) {return CNUM(c)<36 || c===95 || c===46 || c>127;}
	function  ISOP(c) {return c===43 || c===45;}
	function   NEXT() {return (c=i++<len?str.charCodeAt(i-1):0);}
	if (len>=UNL_MAX_PARSE) {err="Input string too long";}
	//Process the string in 2 passes. The first pass is needed to find label values.
	var map=UnlHashCreate();
	if (map===null) {err="Unable to allocate hash map";}
	var lbl0=UnlLabelAlloc();
	for (var pass=0;pass<2 && err===null;pass++) {
		var scope=null,lbl=null;
		var addr=UnlU64Create(),val=UnlU64Create(),acc=UnlU64Create();
		var tmp0=UnlU64Create(),tmp1=UnlU64Create();
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
				if (UnlU64IsZero(addr)) {err="Leading operator";}
				UnlU64Dec(addr);
				op=c;
				NEXT();
			} else if (CNUM(c)<10) {
				//Number. If it starts with "0x", use hexadecimal.
				token=10;
				UnlU64Zero(val);
				if (c===48 && (NEXT()===120 || c===88)) {token=16;NEXT();}
				tmp0.lo=token;
				while ((tmp1.lo=CNUM(c))<token) {
					UnlU64Mul(val,val,tmp0);
					UnlU64Add(val,val,tmp1);
					NEXT();
				}
			} else if (c===63) {
				//Current address token.
				token=1;
				UnlU64Set(val,addr);
				NEXT();
			} else if (ISLBL(c)) {
				//Label.
				while (ISLBL(c)) {NEXT();}
				lbl=UnlLabelInit(map,lbl0,scope,str,j-1,i-j);
				if (c===58) {
					//Label declaration.
					if (pass===0) {
						if (lbl!==null) {err="Duplicate label declaration";}
						UnlU64Set(lbl0.addr,addr);
						lbl=UnlLabelAdd(map,lbl0);
						if (lbl===null) {err="Unable to allocate label";}
					}
					scope=lbl;
					if (ISOP(op)) {err="Operating on declaration";}
					op=c;
					NEXT();
				} else {
					token=1;
					if (lbl!==null) {UnlU64Set(val,lbl.addr);}
					else if (pass!==0) {err="Unable to find label";}
				}
			} else {
				err="Unexpected token";
				i++;
			}
			if (token!==0) {
				//Add a new value to memory.
				if (op===43) {UnlU64Add(val,acc,val);}
				else if (op===45) {UnlU64Sub(val,acc,val);}
				else if (pass!==0) {
					UnlU64Dec(addr);
					UnlSetMem(st,addr,acc);
					UnlU64Inc(addr);
				}
				UnlU64Inc(addr);
				UnlU64Set(acc,val);
				op=0;
				if (ISLBL(c) || c===63) {err="Unseparated tokens";}
			}
		}
		if (err===null && ISOP(op)) {err="Trailing operator";}
		if (pass!==0) {
			UnlU64Dec(addr);
			UnlSetMem(st,addr,acc);
			UnlU64Inc(addr);
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

function UnlGetMem(st,addr) {
	//Return the memory value at addr.
	var i=addr.lo;
	if (addr.hi===0 && i<st.alloc) {
		return UnlU64Create(st.memh[i],st.meml[i]);
	}
	return UnlU64Create();
}

function UnlSetMem(st,addr,val) {
	//Write val to the memory at addr.
	var pos=addr.lo;
	if (addr.hi!==0 || pos>=st.alloc) {
		//If we're writing to an address outside of our memory, attempt to resize it or
		//error out.
		if (UnlU64IsZero(val)) {return;}
		//Find the maximum we can allocate.
		var alloc=1,memh=null,meml=null;
		while (alloc<=pos) {alloc+=alloc;}
		//Attempt to allocate.
		if (addr.hi===0 && alloc>pos) {
			try {
				memh=new Uint32Array(alloc);
				meml=new Uint32Array(alloc);
			} catch(error) {
				memh=null;
				meml=null;
			}
		}
		if (memh!==null && meml!==null) {
			if (st.alloc>0) {
				memh.set(st.memh,0);
				meml.set(st.meml,0);
			}
			st.memh=memh;
			st.meml=meml;
			st.alloc=alloc;
		} else {
			st.state=UNL_ERROR_MEMORY;
			st.statestr="Failed to allocate memory.\nIndex: "+UnlU64ToStr(addr)+"\n";
			return;
		}
	}
	st.memh[pos]=val.hi;
	st.meml[pos]=val.lo;
}

function UnlRunStandard(st,iters) {
	//Run unileq for a given number of iterations. If iters<0, run forever.
	var a,b,c,ma,mb,ip=st.ip;
	var io=UnlU64Create(-4);
	iters=iters<0?Infinity:iters;
	for (;iters>0 && st.state===UNL_RUNNING;iters--) {
		//Load a, b, and c.
		a=UnlGetMem(st,ip);UnlU64Inc(ip);
		b=UnlGetMem(st,ip);UnlU64Inc(ip);
		c=UnlGetMem(st,ip);UnlU64Inc(ip);
		//Input
		if (UnlU64Cmp(b,io)<0) {
			mb=UnlGetMem(st,b);
		} else if (b.lo===0xfffffffc) {
			//Read time. time = (seconds since 1 Jan 1970) * 2^32.
			var time=performance.timing.navigationStart+performance.now();
			mb=UnlU64Create((time/1000)>>>0,((time%1000)*4294967.296)>>>0);
		} else {
			UnlU64Zero(mb);
		}
		//Output
		if (UnlU64Cmp(a,io)<0) {
			//Execute a normal unileq instruction.
			ma=UnlGetMem(st,a);
			if (UnlU64Sub(ma,ma,mb)) {
				UnlU64Set(ip,c);
			}
			UnlSetMem(st,a,ma);
			continue;
		} else if (a.lo===0xffffffff) {
			//Exit.
			st.state=UNL_COMPLETE;
		} else if (a.lo===0xfffffffe) {
			//Print to stdout.
			UnlPrint(st,String.fromCharCode(mb.lo&255));
		}
		UnlU64Set(ip,c);
	}
}

function UnlRun(st,iters) {
	//Run unileq for a given number of iterations. If iters<0, run forever.
	//This version of UnlRun() unrolls several operations to speed things up.
	//Depending on the platform, it's 4 to 10 times faster than standard.
	if (st.state!==UNL_RUNNING) {
		return;
	}
	//Performance testing.
	/*if (st.ip.lo===0 && st.ip.hi===0) {
		this.instructions=0;
		this.time=0;
		this.start=performance.now();
	}
	this.instructions+=iters;
	this.time-=performance.now();*/
	var iphi=st.ip.hi,iplo=st.ip.lo;
	var memh=st.memh,meml=st.meml;
	var alloc=st.alloc,alloc2=alloc-2;
	var ahi,alo,chi,clo;
	var bhi,blo,mbhi,mblo;
	var tmp0=UnlU64Create(),tmp1=UnlU64Create(),tmp2;
	var io=0xfffffffc;
	iters=iters<0?Infinity:iters;
	for (;iters>0;iters--) {
		//Load a, b, and c.
		if (iphi===0 && iplo<alloc2) {
			//Inbounds read.
			ahi=memh[iplo];
			alo=meml[iplo++];
			bhi=memh[iplo];
			blo=meml[iplo++];
			chi=memh[iplo];
			clo=meml[iplo++];
		} else {
			//Out of bounds read. Use UnlGetMem to read a, b, and c.
			tmp0.hi=iphi;tmp0.lo=iplo;
			tmp1=UnlGetMem(st,tmp0);ahi=tmp1.hi;alo=tmp1.lo;UnlU64Inc(tmp0);
			tmp1=UnlGetMem(st,tmp0);bhi=tmp1.hi;blo=tmp1.lo;UnlU64Inc(tmp0);
			tmp1=UnlGetMem(st,tmp0);chi=tmp1.hi;clo=tmp1.lo;UnlU64Inc(tmp0);
			iphi=tmp0.hi;iplo=tmp0.lo;
		}
		//Input
		if (bhi===0) {
			//Inbounds. Read mem[b] directly.
			if (blo<alloc) {
				mbhi=memh[blo];
				mblo=meml[blo];
			} else {
				mbhi=0;
				mblo=0;
			}
		} else if (bhi<0xffffffff || blo<io) {
			//Out of bounds. Use UnlGetMem to read mem[b].
			tmp0.hi=bhi;tmp0.lo=blo;
			tmp2=UnlGetMem(st,tmp0);
			mbhi=tmp2.hi;mblo=tmp2.lo;
		} else if (blo===0xfffffffc) {
			//Read time. time = (seconds since 1 Jan 1970) * 2^32.
			var time=performance.timing.navigationStart+performance.now();
			mbhi=(time/1000)>>>0;
			mblo=((time%1000)*4294967.296)>>>0;
		} else {
			//We couldn't find a special address to read.
			mbhi=0;
			mblo=0;
		}
		//Output
		if (ahi===0 && alo<alloc) {
			//Execute a normal unileq instruction.
			//Inbounds. Read and write to mem[a] directly.
			mblo=meml[alo]-mblo;
			if (mblo<0) {
				mblo+=0x100000000;
				mbhi++;
			}
			meml[alo]=mblo;
			mbhi=memh[alo]-mbhi;
			if (mbhi>=0) {
				memh[alo]=mbhi;
				if (mblo!==0 || mbhi>0) {
					continue;
				}
			} else {
				memh[alo]=mbhi+0x100000000;
			}
		} else if (ahi<0xffffffff || alo<io) {
			//Out of bounds. Use UnlSetMem to modify mem[a].
			tmp0.hi=ahi;tmp0.lo=alo;
			tmp2=UnlGetMem(st,tmp0);
			tmp1.hi=mbhi;tmp1.lo=mblo;
			if (!UnlU64Sub(tmp2,tmp2,tmp1)) {
				chi=iphi;
				clo=iplo;
			}
			UnlSetMem(st,tmp0,tmp2);
			if (st.state!==UNL_RUNNING) {
				break;
			}
			memh=st.memh;
			meml=st.meml;
			alloc=st.alloc;
			alloc2=alloc-2;
		} else if (alo===0xffffffff) {
			//Exit.
			st.state=UNL_COMPLETE;
			break;
		} else if (alo===0xfffffffe) {
			//Print to stdout.
			UnlPrint(st,String.fromCharCode(mblo&255));
		}
		iphi=chi;
		iplo=clo;
	}
	st.ip.hi=iphi;
	st.ip.lo=iplo;
	//Performance testing.
	/*this.time+=performance.now();
	if (st.state!==UNL_RUNNING) {
		var freq=(this.instructions-(iters+1))*1000.0/this.time;
		UnlPrint(st,"Speed: "+freq.toFixed(0)+" Hz\n");
		var time=(performance.now()-this.start)/1000.0;
		UnlPrint(st,"Time : "+time.toFixed(2)+" s\n");
	}*/
}
