/*------------------------------------------------------------------------------


sico.js - v1.29

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


     loop: len  one  exit        # Decrement [len]. If [len]<=1, exit.
           0-2  txt  ?+1         # Print a letter.
           ?-2  neg  loop        # Increment letter pointer.

     exit: 0-1  0    0

     txt:  'H 'e 'l 'l 'o ', '
           'W 'o 'r 'l 'd '! 10
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
     Recall       |  declared by "label:".
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
     Current      |  Denoted by a question mark. Inserts the current memory
     Address      |  address.
                  |
                  |  Ex:
                  |       ?
                  |       ?+1  # Next address
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
     ASCII        |  Denoted by an apostrophe. Inserts an ASCII value.
     Literal      |
                  |  Ex:
                  |       'H 'e 'l 'l 'o  # Evaluates to 72 101 108 108 111
                  |
     -------------+--------------------------------------------------------
                  |
     Operator     |  Denoted by a plus or minus. Adds or subtracts the
                  |  number or label from the previous value. Parentheses
                  |  are not supported. To express a negative number such
                  |  as -5, use the form "0-5".
                  |
                  |  Ex:
                  |       len-txt+1
                  |       ?+1
                  |
     -------------+--------------------------------------------------------
                  |
     Input /      |  Addresses above 2^63-1 are considered special and
     Output       |  reading or writing to them will interact with the
                  |  host. For an instruction A, B, C:
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
Performance


Performance tests, measured in millions of instructions per second:


               Environment            |   Rate
     ---------------------------------+----------
       i5-10210Y - CPU     - C        |
       R9-3900X  - CPU     - C        |
       Pixel 2   - Firefox - JS Fast  |
       i5-10210Y - Firefox - JS STD   |    2.64
       Pixel 2   - Chrome  - JS STD   |    3.60
       R9-3900X  - Firefox - JS STD   |    6.95
       R9-3900X  - Chrome  - JS STD   |   17.07
       Pixel 2   - Chrome  - JS Fast  |   19.12
       i5-10210Y - Firefox - JS Fast  |   36.79
       R9-3900X  - Chrome  - JS Fast  |   97.18
       R9-3900X  - Firefox - JS Fast  |   97.27



Tests should take 5 minutes or more. Tests run on a phone need to be run
several times to see the effect of thermal throttling.

Splitting into high/low arrays is about 8% faster than using interleaved memory.

Uint32Array is at least 5% faster than Float64Array across all hardware and
browsers.

When testing the math library, we jump 77% of the time. Delaying loading mem[C]
didn't provide a meaningful speedup.

Webassembly speedup isn't that great compared to SicoRun() and adds a lot of
complexity. Wait until better integration with javascript.

We busy wait if sleeping for less than 4ms. This is because the HTML5 standard
enforces a minimum setTimeout() time of 4ms.


--------------------------------------------------------------------------------
TODO


Redo performance tests.
Merge editor. Add option to pause if not on page.

Mouse+Keyboard
Audio


*/
/* jshint bitwise: false */
/* jshint eqeqeq: true   */
/* jshint curly: true    */


//---------------------------------------------------------------------------------
// 64 bit unsigned integers.


function SicoU64Create(hi,lo) {
	if (hi===undefined) {
		// If arguments are empty, initialize to 0.
		hi=0;
		lo=0;
	} else if (lo===undefined) {
		if (hi.hi!==undefined) {
			// hi is another u64 object.
			lo=hi.lo;
			hi=hi.hi;
		} else if (hi>=0) {
			// hi is a positive number.
			lo=hi>>>0;
			hi=(hi/0x100000000)>>>0;
		} else {
			// hi is a negative number.
			lo=0x100000000-((-hi)>>>0);
			hi=0x0ffffffff-(((-hi)/0x100000000)>>>0);
			if (lo===0x100000000) {
				lo=0;
				hi++;
			}
		}
	}
	return {hi:hi,lo:lo};
}

function SicoU64ToStr(n) {
	// Convert a 64-bit number to its base 10 representation.
	// Powers of 10 split into high 32 bits and low 32 bits.
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
	for (var i=0;i<pot.length;i+=2) {
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

function SicoU64ToF64(a) {
	return a.hi*4294967296+a.lo;
}

function SicoU64Cmp(a,b) {
	// if a<b, return -1
	// if a=b, return  0
	// if a>b, return  1
	if (a.hi!==b.hi) {return a.hi<b.hi?-1:1;}
	if (a.lo!==b.lo) {return a.lo<b.lo?-1:1;}
	return 0;
}

function SicoU64Set(a,b) {
	// a=b
	a.lo=b.lo;
	a.hi=b.hi;
}

function SicoU64Zero(n) {
	// n=0
	n.lo=0;
	n.hi=0;
}

function SicoU64IsZero(n) {
	// n==0
	return n.lo===0 && n.hi===0;
}

function SicoU64Neg(r,a) {
	// r=-a
	r.lo=0x100000000-a.lo;
	r.hi=0x0ffffffff-a.hi;
	if (r.lo>=0x100000000) {
		r.lo=0;
		if ((++r.hi)>=0x100000000) {
			r.hi=0;
		}
	}
}

function SicoU64Sub(r,a,b) {
	// r=a-b
	// return true if a<=b
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

function SicoU64Add(r,a,b) {
	// r=a+b
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

function SicoU64Mul(r,a,b) {
	// r=a*b
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

function SicoU64Inc(n) {
	// n++
	if ((++n.lo)>=0x100000000) {
		n.lo=0;
		if ((++n.hi)>=0x100000000) {
			n.hi=0;
		}
	}
}

function SicoU64Dec(n) {
	// n--
	if ((--n.lo)<0) {
		n.lo=0xffffffff;
		if ((--n.hi)<0) {
			n.hi=0xffffffff;
		}
	}
}


//---------------------------------------------------------------------------------
// SICO architecture interpreter.


var SICO_COMPLETE    =0;
var SICO_RUNNING     =1;
var SICO_ERROR_PARSER=2;
var SICO_ERROR_MEMORY=3;
var SICO_MAX_PARSE   =1<<30;

function SicoCreate(textout,canvas) {
	var st={
		// State variables
		state:   0,
		statestr:"",
		ip:      SicoU64Create(),
		mem:     null,
		alloc:   0,
		lblroot: SicoCreateLabel(),
		sleep:   null,
		// Input/Output
		output:  textout,
		outbuf:  "",
		outpos:  0,
		canvas:  canvas,
		canvctx: null,
		canvdata:null,
		// Functions
		Clear:   function(){return SicoClear(st);},
		Print:   function(str){return SicoPrint(st,str);},
		ParseAssembly:function(str){return SicoParseAssembly(st,str);},
		GetMem:  function(addr){return SicoGetMem(st,addr);},
		SetMem:  function(addr,val){return SicoSetMem(st,addr,val);},
		Run:     function(stoptime){return SicoRun(st,stoptime);}
	};
	SicoClear(st);
	return st;
}

function SicoClear(st) {
	// Clear the interpreter state.
	st.state=SICO_COMPLETE;
	st.statestr="";
	SicoU64Zero(st.ip);
	st.mem=null;
	st.alloc=0;
	st.lblroot=SicoCreateLabel();
	st.sleep=null;
	if (st.output!==null) {
		st.output.value="";
	}
	st.outbuf="";
	st.outpos=0;
	if (st.canvctx!==null) {
		st.canvctx.clearRect(0,0,st.canvas.width,st.canvas.height);
	}
	if (st.canvas!==null) {
		st.canvas.style.display="none";
	}
}

function SicoPrint(st,str) {
	// Print to output and autoscroll to bottom. Try to mimic the effects of a
	// terminal. If output is null, print to console.
	var output=st.output;
	st.outbuf+=str;
	if (output!==null) {
		var outval=output.value;
		var outpos=st.outpos;
		if (outpos<0 || outpos>outval.length) {
			outpos=outval.length;
		}
		str=st.outbuf;
		st.outbuf="";
		for (var i=0;i<str.length;i++) {
			var c=str[i];
			if (c==="\r") {
				while (outpos>0 && outval[outpos-1]!=="\n") {
					outpos--;
				}
			} else if (c==="\b") {
				if (outpos>0 && outval[outpos-1]!=="\n") {
					outpos--;
				}
			} else if (c==="\n" || outpos>=outval.length) {
				outval+=c;
				outpos=outval.length;
			} else {
				outval=outval.substring(0,outpos)+c+outval.substring(outpos+1);
				outpos++;
			}
			if (outval.length>8192) {
				outval=outval.substring(outval.length-1024);
				outpos=outpos>1024?outpos-1024:0;
			}
		}
		output.value=outval;
		output.scrollTop=output.scrollHeight;
		st.outpos=outpos;
	} else {
		str=st.outbuf.split("\n");
		for (var i=0;i<str.length-1;i++) {
			console.log(str[i]);
		}
		st.outbuf=str[str.length-1];
	}
}

function SicoParseAssembly(st,str) {
	// Convert SICO assembly language into a SICO program.
	SicoClear(st);
	st.state=SICO_RUNNING;
	var i=0,j=0,len=str.length;
	var c,op,err=null;
	function  CNUM(c) {return (c<=57?c+208:((c+191)&~32)+10)&255;}
	function ISLBL(c) {return CNUM(c)<36 || c===95 || c===46 || c>127;}
	function  ISOP(c) {return c===43 || c===45;}
	function   NEXT() {return (c=i++<len?str.charCodeAt(i-1):0);}
	if (len>=SICO_MAX_PARSE) {err="Input string too long";}
	// Process the string in 2 passes. The first pass is needed to find label values.
	for (var pass=0;pass<2 && err===null;pass++) {
		var scope=st.lblroot;
		var addr=SicoU64Create(),val=SicoU64Create(),acc=SicoU64Create();
		var tmp0=SicoU64Create(),tmp1=SicoU64Create();
		op=0;
		i=0;
		NEXT();
		j=i;
		while (c!==0 && err===null) {
			var n=0,token=0;
			if (c===13 || c===10 || c===9 || c===32) {
				// Whitespace.
				NEXT();
				continue;
			}
			if (c===35) {
				// Comment. If next='|', use the multi-line format.
				var mask=0,eoc=10,i0=i;
				if (NEXT()===124) {mask=255;eoc=31779;NEXT();}
				while (c!==0 && n!==eoc) {n=((n&mask)<<8)+c;NEXT();}
				if (mask!==0 && n!==eoc) {err="Unterminated block quote";j=i0;}
				continue;
			}
			j=i;
			if (ISOP(c)) {
				// Operator. Decrement addr since we're modifying the previous value.
				if (op!==0 ) {err="Double operator";}
				if (op===58) {err="Operating on declaration";}
				if (SicoU64IsZero(addr)) {err="Leading operator";}
				SicoU64Dec(addr);
				op=c;
				NEXT();
			} else if (CNUM(c)<10) {
				// Number. If it starts with "0x", use hexadecimal.
				token=10;
				SicoU64Zero(val);
				if (c===48 && (NEXT()===120 || c===88)) {token=16;NEXT();}
				tmp0.lo=token;
				while ((tmp1.lo=CNUM(c))<token) {
					SicoU64Mul(val,val,tmp0);
					SicoU64Add(val,val,tmp1);
					NEXT();
				}
			} else if (c===39) {
				// ASCII literal. Ex: 'H 'e 'l 'l 'o
				token=1;
				val=SicoU64Create(NEXT());
				NEXT();
			} else if (c===63) {
				// Current address token.
				token=1;
				SicoU64Set(val,addr);
				NEXT();
			} else if (ISLBL(c)) {
				// Label.
				while (ISLBL(c)) {NEXT();}
				var lbl=SicoAddLabel(st,scope,str,j-1,i-j);
				if (lbl===null) {err="Unable to allocate label";break;}
				SicoU64Set(val,lbl.addr);
				var isset=val.hi!==0xffffffff || val.lo!==0xffffffff;
				if (c===58) {
					// Label declaration.
					if (pass===0) {
						if (isset) {err="Duplicate label declaration";}
						SicoU64Set(lbl.addr,addr);
					}
					if (str[j-1]!=='.') {scope=lbl;}
					if (ISOP(op)) {err="Operating on declaration";}
					op=c;
					NEXT();
				} else {
					token=1;
					if (pass!==0 && !isset) {err="Unable to find label";}
				}
			} else {
				err="Unexpected token";
				i++;
			}
			if (token!==0) {
				// Add a new value to memory.
				if (op===43) {SicoU64Add(val,acc,val);}
				else if (op===45) {SicoU64Sub(val,acc,val);}
				else if (pass!==0) {
					SicoU64Dec(addr);
					SicoSetMem(st,addr,acc);
					SicoU64Inc(addr);
				}
				SicoU64Inc(addr);
				SicoU64Set(acc,val);
				op=0;
				if (ISLBL(c) || c===63 || c===39) {err="Unseparated tokens";}
			}
		}
		if (err===null && ISOP(op)) {err="Trailing operator";}
		if (pass!==0) {
			SicoU64Dec(addr);
			SicoSetMem(st,addr,acc);
			SicoU64Inc(addr);
		}
	}
	if (err!==null) {
		// We've encountered a parsing error.
		st.state=SICO_ERROR_PARSER;
		st.statestr="Parser: "+err+"\n";
		if (i-- && j--)
		{
			var line=1;
			var window="",under="";
			// Find the boundaries of the line we're currently parsing.
			var s0=0,s1=j,k;
			for (k=0;k<j;k++) {
				if (str[k]==="\n") {
					line++;
					s0=k+1;
				}
			}
			while (s1<len && str[s1]!=="\n") {s1++;}
			// Trim whitespace.
			while (s0<s1 && str[s0  ]<=" ") {s0++;}
			while (s1>s0 && str[s1-1]<=" ") {s1--;}
			// Extract the line and underline the error.
			s0=j>s0+30?j-30:s0;
			for (k=0;k<61;k++,s0++) {
				c=s0<s1 && k<60?str[s0]:"";
				window+=c;
				under+=c && s0>=j && s0<i?"^":(c<=" "?c:" ");
			}
			st.statestr="Parser: "+err+"\nLine  : "+line+"\n\n\t"+window+"\n\t"+under+"\n\n";
		}
	}
}

function SicoCreateLabel() {
	var lbl={
		addr: SicoU64Create(-1),
		child:new Array(16).fill(null)
	};
	return lbl;
}

function SicoAddLabel(st,scope,data,idx,len) {
	// Add a label if it's new.
	// If the label starts with a '.', make it a child of the last non '.' label.
	var lbl=data[idx]==='.'?scope:st.lblroot;
	for (var i=0;i<len;i++) {
		var c=data.charCodeAt(idx+i);
		for (var j=4;j>=0;j-=4) {
			var val=(c>>>j)&15;
			var parent=lbl;
			lbl=parent.child[val];
			if (lbl===null) {
				lbl=SicoCreateLabel();
				parent.child[val]=lbl;
			}
		}
	}
	return lbl;
}

function SicoFindLabel(st,label) {
	// Returns the given label's address. Returns null if no label was found.
	var lbl=st.lblroot,len=label.length;
	if (lbl===null) {return null;}
	for (var i=0;i<len;i++) {
		var c=label.charCodeAt(i);
		for (var j=4;j>=0;j-=4) {
			var val=(c>>>j)&15;
			lbl=lbl.child[val];
			if (lbl===null) {return null;}
		}
	}
	return SicoU64Create(lbl.addr);
}

function SicoGetMem(st,addr) {
	// Return the memory value at addr.
	var i=SicoU64ToF64(addr);
	if (i<st.alloc) {
		i+=i;
		return SicoU64Create(st.mem[i],st.mem[i+1]);
	}
	return SicoU64Create();
}

function SicoSetMem(st,addr,val) {
	// Write val to the memory at addr.
	var pos=addr.lo;
	if (addr.hi!==0 || pos>=st.alloc) {
		// If we're writing to an address outside of our memory, attempt to resize it or
		// error out.
		if (SicoU64IsZero(val)) {return;}
		// Find the maximum we can allocate.
		var alloc=1,mem=null;
		while (alloc<=pos) {alloc+=alloc;}
		// Attempt to allocate.
		if (addr.hi===0 && alloc>pos) {
			try {
				mem=new Uint32Array(alloc*2);
			} catch(error) {
				mem=null;
			}
		}
		if (mem!==null) {
			if (st.mem!==null) {
				mem.set(st.mem,0);
			}
			st.mem=mem;
			st.alloc=alloc;
		} else {
			st.state=SICO_ERROR_MEMORY;
			st.statestr="Failed to allocate memory.\nIndex: "+SicoU64ToStr(addr)+"\n";
			return;
		}
	}
	pos+=pos;
	st.mem[pos  ]=val.hi;
	st.mem[pos+1]=val.lo;
}

function SicoDrawImage(st,imghi,imglo) {
	var canvas=st.canvas;
	if (canvas===null || canvas===undefined) {
		return;
	}
	// Get the image data.
	var imgpos=imghi*8589934592+imglo*2;
	var mem=st.mem;
	var alloc=st.alloc*2;
	if (imgpos>alloc-6) {
		return;
	}
	var imgwidth =mem[imgpos  ]*4294967296+mem[imgpos+1];
	var imgheight=mem[imgpos+2]*4294967296+mem[imgpos+3];
	var imgdata  =mem[imgpos+4]*8589934592+mem[imgpos+5]*2;
	var imgpixels=imgwidth*imgheight*2;
	if (imgwidth>65536 || imgheight>65536 || imgdata+imgpixels>alloc) {
		return;
	}
	// Resize the canvas.
	if (canvas.width!==imgwidth || canvas.height!==imgheight || st.canvdata===null) {
		canvas.width=imgwidth;
		canvas.height=imgheight;
		st.canvctx=canvas.getContext("2d");
		st.canvdata=st.canvctx.createImageData(imgwidth,imgheight);
	}
	if (canvas.style.display==="none") {
		canvas.style.display="block";
	}
	// Copy the ARGB data to the RGBA canvas.
	var dstdata=st.canvdata.data;
	var hi,lo;
	imgpixels+=imgpixels;
	for (var i=0;i<imgpixels;i+=4) {
		hi=mem[imgdata++];
		lo=mem[imgdata++];
		dstdata[i  ]=(hi&0xffff)>>>8;
		dstdata[i+1]=lo>>>24;
		dstdata[i+2]=(lo&0xffff)>>>8;
		dstdata[i+3]=hi>>>24;
	}
	st.canvctx.putImageData(st.canvdata,0,0);
}

function SicoRun(st,stoptime) {
	// Run SICO while performance.now()<stoptime.
	//
	// This version of SicoRun() unrolls several operations to speed things up.
	// Depending on the platform, it's 4 to 10 times faster than using u64 functions.
	if (st.state!==SICO_RUNNING) {
		return;
	}
	if (st.sleep!==null) {
		// If sleeping for longer than the time we have, abort.
		if (st.sleep>=stoptime) {
			return;
		}
		// If we're sleeping for more than 4ms, defer until later.
		var sleep=st.sleep-performance.now();
		if (sleep>4) {
			setTimeout(SicoRun,sleep-2,st,stoptime);
			return;
		}
		// Busy wait.
		while (performance.now()<st.sleep) {}
		st.sleep=null;
	}
	// Performance testing.
	/*if (st.ip.hi===0 && st.ip.lo===0) {
		this.inst=0;
		this.time=0;
	}
	var dbginst=0;
	var dbgtime=performance.now();*/
	var iphi=st.ip.hi,iplo=st.ip.lo,i;
	var mem=st.mem;
	var alloc=st.alloc,alloc2=alloc-2;
	var ahi,alo,chi,clo;
	var bhi,blo,mbhi,mblo;
	var tmp0=SicoU64Create(),tmp1=SicoU64Create(),tmp2;
	var timeiters=0;
	while (true) {
		// dbginst++;
		// Periodically check if we've run for too long.
		if (--timeiters<=0) {
			if (performance.now()>=stoptime) {
				break;
			}
			timeiters=4096;
		}
		// Load a, b, and c.
		if (iphi===0 && iplo<alloc2) {
			// Inbounds read.
			i=iplo+iplo;
			iplo+=3;
			ahi=mem[i  ];
			alo=mem[i+1];
			bhi=mem[i+2];
			blo=mem[i+3];
			chi=mem[i+4];
			clo=mem[i+5];
		} else {
			// Out of bounds read. Use SicoGetMem to read a, b, and c.
			tmp0.hi=iphi;tmp0.lo=iplo;
			tmp1=SicoGetMem(st,tmp0);ahi=tmp1.hi;alo=tmp1.lo;SicoU64Inc(tmp0);
			tmp1=SicoGetMem(st,tmp0);bhi=tmp1.hi;blo=tmp1.lo;SicoU64Inc(tmp0);
			tmp1=SicoGetMem(st,tmp0);chi=tmp1.hi;clo=tmp1.lo;SicoU64Inc(tmp0);
			iphi=tmp0.hi;iplo=tmp0.lo;
			timeiters-=32;
		}
		// Input
		if (bhi===0) {
			// Inbounds. Read mem[b] directly.
			if (blo<alloc) {
				i=blo+blo;
				mbhi=mem[i  ];
				mblo=mem[i+1];
			} else {
				mbhi=0;
				mblo=0;
			}
		} else if (bhi<0x80000000) {
			// Out of bounds. Use SicoGetMem to read mem[b].
			tmp0.hi=bhi;tmp0.lo=blo;
			tmp2=SicoGetMem(st,tmp0);
			mbhi=tmp2.hi;mblo=tmp2.lo;
			timeiters-=1;
		} else if (blo===0xfffffffc) {
			// Timing frequency. 2^32 = 1 second.
			mbhi=1;
			mblo=0;
		} else if (blo===0xfffffffb) {
			// Read time. time = (seconds since 1 Jan 1970) * 2^32.
			var date=performance.timing.navigationStart+performance.now();
			mbhi=(date/1000)>>>0;
			mblo=((date%1000)*4294967.296)>>>0;
			timeiters-=2;
		} else {
			// We couldn't find a special address to read.
			mbhi=0;
			mblo=0;
		}
		// Output
		if (ahi===0 && alo<alloc) {
			// Execute a normal SICO instruction.
			// Inbounds. Read and write to mem[a] directly.
			i=alo+alo;
			mblo=mem[i+1]-mblo;
			mbhi=mem[i  ]-mbhi-(mblo<0);
			mem[i+1]=mblo;
			mem[i  ]=mbhi;
			if (mbhi<0 || (mbhi===0 && mblo===0)) {
				iphi=chi;
				iplo=clo;
			}
			continue;
		} else if (ahi<0x80000000) {
			// Out of bounds. Use SicoSetMem to modify mem[a].
			tmp0.hi=ahi;tmp0.lo=alo;
			tmp2=SicoGetMem(st,tmp0);
			tmp1.hi=mbhi;tmp1.lo=mblo;
			if (SicoU64Sub(tmp2,tmp2,tmp1)) {
				iphi=chi;
				iplo=clo;
			}
			SicoSetMem(st,tmp0,tmp2);
			if (st.state!==SICO_RUNNING) {
				break;
			}
			mem=st.mem;
			alloc=st.alloc;
			alloc2=alloc-2;
			timeiters-=8;
			continue;
		}
		// Special addresses.
		iphi=chi;
		iplo=clo;
		if (ahi<0xffffffff) {
			// The gap between special addresses and working memory.
		} else if (alo===0xffffffff) {
			// Exit.
			st.state=SICO_COMPLETE;
			break;
		} else if (alo===0xfffffffe) {
			// Print to stdout.
			SicoPrint(st,String.fromCharCode(mblo&255));
			timeiters-=1;
		} else if (alo===0xfffffffa) {
			// Sleep.
			var sleep=mbhi*1000+mblo*(1000.0/4294967296.0);
			var sleeptill=performance.now()+sleep;
			// If sleeping for longer than the time we have or more than 4ms, abort.
			if (sleep>4 || sleeptill>=stoptime) {
				st.sleep=sleeptill;
				if (sleeptill<stoptime) {
					setTimeout(SicoRun,sleep-2,st,stoptime);
				}
				break;
			}
			// Busy wait.
			while (performance.now()<sleeptill) {}
			timeiters=0;
		} else if (alo===0xfffffff9) {
			// Draw an image.
			SicoDrawImage(st,mbhi,mblo);
			timeiters=0;
		}
	}
	st.ip.hi=iphi;
	st.ip.lo=iplo;
	// Performance testing.
	/*this.time+=performance.now()-dbgtime;
	this.inst+=dbginst;
	if (st.state!==SICO_RUNNING) {
		SicoPrint(st,"\n-----------------------\nDebug Stats:\n\n");
		SicoPrint(st,"inst: "+this.inst+"\n");
		SicoPrint(st,"sec : "+(this.time/1000.0)+"\n");
		SicoPrint(st,"rate: "+(this.inst/(this.time*1000))+"\n");
	}*/
}
