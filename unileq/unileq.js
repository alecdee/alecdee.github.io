/*------------------------------------------------------------------------------


unileq.js - v1.25

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

Webassembly speedup isn't that great compared to UnlRun() and adds a lot of
complexity. Wait until better integration with javascript.

We busy wait if sleeping for less than 4ms. This is because the HTML5 standard
enforces a minimum setTimeout() time of 4ms.


--------------------------------------------------------------------------------
TODO


Mouse+Keyboard
Audio


*/
/* jshint bitwise: false */
/* jshint eqeqeq: true   */
/* jshint curly: true    */


//---------------------------------------------------------------------------------
// 64 bit unsigned integers.


function UnlU64Create(hi,lo) {
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
	return {lo:lo,hi:hi};
}

function UnlU64ToStr(n) {
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

function UnlU64Cmp(a,b) {
	// if a<b, return -1
	// if a=b, return  0
	// if a>b, return  1
	if (a.hi!==b.hi) {return a.hi<b.hi?-1:1;}
	if (a.lo!==b.lo) {return a.lo<b.lo?-1:1;}
	return 0;
}

function UnlU64Set(a,b) {
	// a=b
	a.lo=b.lo;
	a.hi=b.hi;
}

function UnlU64Zero(n) {
	// n=0
	n.lo=0;
	n.hi=0;
}

function UnlU64IsZero(n) {
	// n==0
	return n.lo===0 && n.hi===0;
}

function UnlU64Neg(r,a) {
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

function UnlU64Sub(r,a,b) {
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

function UnlU64Add(r,a,b) {
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

function UnlU64Mul(r,a,b) {
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

function UnlU64Inc(n) {
	// n++
	if ((++n.lo)>=0x100000000) {
		n.lo=0;
		if ((++n.hi)>=0x100000000) {
			n.hi=0;
		}
	}
}

function UnlU64Dec(n) {
	// n--
	if ((--n.lo)<0) {
		n.lo=0xffffffff;
		if ((--n.hi)<0) {
			n.hi=0xffffffff;
		}
	}
}


//---------------------------------------------------------------------------------
// Unileq architecture interpreter.


var UNL_RUNNING     =0;
var UNL_COMPLETE    =1;
var UNL_ERROR_PARSER=2;
var UNL_ERROR_MEMORY=3;
var UNL_MAX_PARSE   =1<<30;

function UnlCreate(textout,canvas) {
	var st={
		// State variables
		state:   0,
		statestr:"",
		ip:      UnlU64Create(),
		memh:    null,
		meml:    null,
		alloc:   0,
		lblroot: UnlCreateLabel(),
		sleep:   null,
		// Input/Output
		output:  textout,
		outbuf:  "",
		canvas:  canvas,
		canvctx: null,
		canvdata:null,
		// Functions
		Clear:   function(){return UnlClear(st);},
		Print:   function(str){return UnlPrint(st,str);},
		ParseAssembly:function(str){return UnlParseAssembly(st,str);},
		GetMem:  function(addr){return UnlGetMem(st,addr);},
		SetMem:  function(addr,val){return UnlSetMem(st,addr,val);},
		Run:     function(stoptime){return UnlRun(st,stoptime);}
	};
	UnlClear(st);
	return st;
}

function UnlClear(st) {
	// Clear the interpreter state.
	st.state=UNL_COMPLETE;
	st.statestr="";
	UnlU64Zero(st.ip);
	st.memh=null;
	st.meml=null;
	st.alloc=0;
	st.lblroot=UnlCreateLabel();
	st.sleep=null;
	if (st.output!==null) {
		st.output.value="";
	}
	st.outbuf="";
	if (st.canvctx!==null) {
		st.canvctx.clearRect(0,0,st.canvas.width,st.canvas.height);
	}
	if (st.canvas!==null) {
		st.canvas.style.display="none";
	}
}

function UnlPrint(st,str) {
	// Print to output and autoscroll to bottom. If output is null, print to console.
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

function UnlParseAssembly(st,str) {
	// Convert unileq assembly language into a unileq program.
	UnlClear(st);
	st.state=UNL_RUNNING;
	var i=0,j=0,len=str.length;
	var c,op,err=null;
	function  CNUM(c) {return (c<=57?c+208:((c+191)&~32)+10)&255;}
	function ISLBL(c) {return CNUM(c)<36 || c===95 || c===46 || c>127;}
	function  ISOP(c) {return c===43 || c===45;}
	function   NEXT() {return (c=i++<len?str.charCodeAt(i-1):0);}
	if (len>=UNL_MAX_PARSE) {err="Input string too long";}
	// Process the string in 2 passes. The first pass is needed to find label values.
	for (var pass=0;pass<2 && err===null;pass++) {
		var scope=st.lblroot;
		var addr=UnlU64Create(),val=UnlU64Create(),acc=UnlU64Create();
		var tmp0=UnlU64Create(),tmp1=UnlU64Create();
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
				if (UnlU64IsZero(addr)) {err="Leading operator";}
				UnlU64Dec(addr);
				op=c;
				NEXT();
			} else if (CNUM(c)<10) {
				// Number. If it starts with "0x", use hexadecimal.
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
				// Current address token.
				token=1;
				UnlU64Set(val,addr);
				NEXT();
			} else if (ISLBL(c)) {
				// Label.
				while (ISLBL(c)) {NEXT();}
				var lbl=UnlAddLabel(st,scope,str,j-1,i-j);
				if (lbl===null) {err="Unable to allocate label";break;}
				UnlU64Set(val,lbl.addr);
				var isset=val.hi!==0xffffffff || val.lo!==0xffffffff;
				if (c===58) {
					// Label declaration.
					if (pass===0) {
						if (isset) {err="Duplicate label declaration";}
						UnlU64Set(lbl.addr,addr);
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
		// We've encountered a parsing error.
		st.state=UNL_ERROR_PARSER;
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

function UnlCreateLabel() {
	var lbl={
		addr: UnlU64Create(-1),
		child:new Array(16).fill(null)
	};
	return lbl;
}

function UnlAddLabel(st,scope,data,idx,len) {
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
				lbl=UnlCreateLabel();
				parent.child[val]=lbl;
			}
		}
	}
	return lbl;
}

function UnlFindLabel(st,label) {
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
	return UnlU64Create(lbl.addr);
}

function UnlGetMem(st,addr) {
	// Return the memory value at addr.
	var i=addr.lo;
	if (addr.hi===0 && i<st.alloc) {
		return UnlU64Create(st.memh[i],st.meml[i]);
	}
	return UnlU64Create();
}

function UnlSetMem(st,addr,val) {
	// Write val to the memory at addr.
	var pos=addr.lo;
	if (addr.hi!==0 || pos>=st.alloc) {
		// If we're writing to an address outside of our memory, attempt to resize it or
		// error out.
		if (UnlU64IsZero(val)) {return;}
		// Find the maximum we can allocate.
		var alloc=1,memh=null,meml=null;
		while (alloc<=pos) {alloc+=alloc;}
		// Attempt to allocate.
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

function UnlDrawImage(st,imghi,imglo) {
	var canvas=st.canvas;
	if (canvas===null || canvas===undefined) {
		return;
	}
	// Get the image data.
	if (imghi>0 || imglo>0xffffffff) {
		return;
	}
	var memh=st.memh,meml=st.meml;
	var alloc=st.alloc;
	var width=imglo<alloc?meml[imglo]:0;
	imglo++;
	var height=imglo<alloc?meml[imglo]:0;
	imglo++;
	var srcdata=imglo<alloc?meml[imglo]:0;
	if (width>65536 || height>65536) {
		return;
	}
	// Resize the canvas.
	if (canvas.width!==width || canvas.height!==height || st.canvdata===null) {
		canvas.width=width;
		canvas.height=height;
		st.canvctx=canvas.getContext("2d");
		st.canvdata=st.canvctx.createImageData(width,height);
	}
	if (canvas.style.display==="none") {
		canvas.style.display="block";
	}
	// Copy the ARGB data to the RGBA canvas.
	var pixels=width*height*4;
	var dstdata=st.canvdata.data;
	var hi,lo;
	for (var i=0;i<pixels;i+=4) {
		if (srcdata<alloc) {
			hi=memh[srcdata];
			lo=meml[srcdata];
			srcdata++;
		}
		dstdata[i  ]=(hi&0xffff)>>>8;
		dstdata[i+1]=lo>>>24;
		dstdata[i+2]=(lo&0xffff)>>>8;
		dstdata[i+3]=hi>>>24;
	}
	st.canvctx.putImageData(st.canvdata,0,0);
}

/*function UnlRunStandard(st) {
	//Run unileq for a given number of iterations.
	var a,b,c,ma,mb,ip=st.ip;
	var io=UnlU64Create(-4);
	for (var iters=st.instperframe;iters>0 && st.state===UNL_RUNNING;iters--) {
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
}*/

function UnlRun(st,stoptime) {
	// Run unileq while performance.now()<stoptime.
	//
	// This version of UnlRun() unrolls several operations to speed things up.
	// Depending on the platform, it's 4 to 10 times faster than standard.
	if (st.state!==UNL_RUNNING) {
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
			setTimeout(UnlRun,sleep-2,st,stoptime);
			return;
		}
		// Busy wait.
		while (performance.now()<st.sleep) {}
		st.sleep=null;
	}
	// Performance testing.
	/*if (st.ip.hi===0 && st.ip.lo===0) {
		this.time=performance.now();
	}*/
	var iphi=st.ip.hi,iplo=st.ip.lo;
	var memh=st.memh,meml=st.meml;
	var alloc=st.alloc,alloc2=alloc-2;
	var ahi,alo,chi,clo;
	var bhi,blo,mbhi,mblo;
	var tmp0=UnlU64Create(),tmp1=UnlU64Create(),tmp2;
	var io=0x100000000-32;
	var timeiters=0;
	while (true) {
		// Periodically check if we've run for too long.
		if (--timeiters<=0) {
			if (performance.now()>=stoptime) {
				break;
			}
			timeiters=2048;
		}
		// Load a, b, and c.
		if (iphi===0 && iplo<alloc2) {
			// Inbounds read.
			ahi=memh[iplo  ];
			alo=meml[iplo++];
			bhi=memh[iplo  ];
			blo=meml[iplo++];
			chi=memh[iplo  ];
			clo=meml[iplo++];
		} else {
			// Out of bounds read. Use UnlGetMem to read a, b, and c.
			tmp0.hi=iphi;tmp0.lo=iplo;
			tmp1=UnlGetMem(st,tmp0);ahi=tmp1.hi;alo=tmp1.lo;UnlU64Inc(tmp0);
			tmp1=UnlGetMem(st,tmp0);bhi=tmp1.hi;blo=tmp1.lo;UnlU64Inc(tmp0);
			tmp1=UnlGetMem(st,tmp0);chi=tmp1.hi;clo=tmp1.lo;UnlU64Inc(tmp0);
			iphi=tmp0.hi;iplo=tmp0.lo;
			timeiters-=3;
		}
		// Input
		if (bhi===0) {
			// Inbounds. Read mem[b] directly.
			if (blo<alloc) {
				mbhi=memh[blo];
				mblo=meml[blo];
			} else {
				mbhi=0;
				mblo=0;
			}
		} else if (bhi<0xffffffff || blo<io) {
			// Out of bounds. Use UnlGetMem to read mem[b].
			tmp0.hi=bhi;tmp0.lo=blo;
			tmp2=UnlGetMem(st,tmp0);
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
			// Execute a normal unileq instruction.
			// Inbounds. Read and write to mem[a] directly.
			mblo=meml[alo]-mblo;
			if (mblo<0) {
				mblo+=0x100000000;
				mbhi++;
			}
			meml[alo]=mblo;
			mbhi=memh[alo]-mbhi;
			if (mbhi<0) {
				mbhi+=0x100000000;
				iphi=chi;
				iplo=clo;
			} else if (mbhi===0 && mblo===0) {
				iphi=chi;
				iplo=clo;
			}
			memh[alo]=mbhi;
			continue;
		} else if (ahi<0xffffffff || alo<io) {
			// Out of bounds. Use UnlSetMem to modify mem[a].
			tmp0.hi=ahi;tmp0.lo=alo;
			tmp2=UnlGetMem(st,tmp0);
			tmp1.hi=mbhi;tmp1.lo=mblo;
			if (UnlU64Sub(tmp2,tmp2,tmp1)) {
				iphi=chi;
				iplo=clo;
			}
			UnlSetMem(st,tmp0,tmp2);
			if (st.state!==UNL_RUNNING) {
				break;
			}
			memh=st.memh;
			meml=st.meml;
			alloc=st.alloc;
			alloc2=alloc-2;
			timeiters-=2;
			continue;
		}
		// Special addresses.
		iphi=chi;
		iplo=clo;
		if (alo===0xffffffff) {
			// Exit.
			st.state=UNL_COMPLETE;
			break;
		} else if (alo===0xfffffffe) {
			// Print to stdout.
			UnlPrint(st,String.fromCharCode(mblo&255));
			timeiters-=1;
		} else if (alo===0xfffffffa) {
			// Sleep.
			var sleep=mbhi*1000+mblo*(1000.0/4294967296.0);
			var sleeptill=performance.now()+sleep;
			// If sleeping for longer than the time we have or more than 4ms, abort.
			if (sleep>4 || sleeptill>=stoptime) {
				st.sleep=sleeptill;
				if (sleeptill<stoptime) {
					setTimeout(UnlRun,sleep-2,st,stoptime);
				}
				break;
			}
			// Busy wait.
			while (performance.now()<sleeptill) {}
			timeiters=0;
		} else if (alo===0xfffffff9) {
			// Draw an image.
			UnlDrawImage(st,mbhi,mblo);
		}
	}
	st.ip.hi=iphi;
	st.ip.lo=iplo;
	// Performance testing.
	/*if (st.state!==UNL_RUNNING) {
		var time=performance.now()-this.time;
		UnlPrint(st,"time: "+time);
	}*/
}
