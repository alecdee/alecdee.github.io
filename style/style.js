/*------------------------------------------------------------------------------


style.js - v2.01

Copyright 2018 Alec Dee - MIT license - SPDX: MIT
alecdee.github.io - akdee144@gmail.com


--------------------------------------------------------------------------------
TODO


*/
/* jshint bitwise: false */
/* jshint eqeqeq: true   */
/* jshint curly: true    */


function HighlightPython(text) {
	// Set up regular expressions to match an expression to a style.
	var styledefault   ="color:#cccccc";
	var stylecomment   ="color:#999999";
	var stylequote     ="color:#2aa198";
	var stylemultiquote="color:#2aa198";
	var stylenumber    ="color:#2aa198";
	var styleoperator  ="color:#cccccc";
	var stylespecial   ="color:#2aa198";
	var styleimport    ="color:#859900";
	var stylebuiltin   ="color:#859900";
	var stylekeyword   ="color:#859900";
	var styleexception ="color:#859900";
	var arrspecial=["False","None","True"];
	var arrimport=["as","from","import"];
	var arrbuiltin=[
		"__build_class__","__debug__","__doc__","__import__","__loader__","__name__","__package__","__spec__",
		"abs","all","any","ascii","bin","bool","bytearray","bytes","callable","chr","classmethod","compile",
		"complex","copyright","credits","delattr","dict","dir","divmod","enumerate","eval","exec","exit",
		"filter","float","format","frozenset","getattr","globals","hasattr","hash","help","hex","id","input",
		"int","isinstance","issubclass","iter","len","license","list","locals","map","max","memoryview","min",
		"next","object","oct","open","ord","pow","print","property","quit","range","repr","reversed","round",
		"set","setattr","slice","sorted","staticmethod","str","sum","super","tuple","type","vars","zip"
	];
	var arrkeyword=[
		"and","assert","break","class","continue","def","del","elif","else","except","exec","finally","for",
		"global","if","in","is","lambda","not","or","pass","print","raise","return","try","while","with","yield"
	];
	var arrexception=[
		"ArithmeticError","AssertionError","AttributeError","BaseException","BlockingIOError","BrokenPipeError",
		"BufferError","BytesWarning","ChildProcessError","ConnectionAbortedError","ConnectionError",
		"ConnectionRefusedError","ConnectionResetError","DeprecationWarning","EOFError","EnvironmentError",
		"Exception","FileExistsError","FileNotFoundError","FloatingPointError","FutureWarning","GeneratorExit",
		"IOError","ImportError","ImportWarning","IndentationError","IndexError","InterruptedError",
		"IsADirectoryError","KeyError","KeyboardInterrupt","LookupError","MemoryError","NameError",
		"NotADirectoryError","NotImplemented","NotImplementedError","OSError","OverflowError",
		"PendingDeprecationWarning","PermissionError","ProcessLookupError","RecursionError","ReferenceError",
		"ResourceWarning","RuntimeError","RuntimeWarning","StopAsyncIteration","StopIteration","SyntaxError",
		"SyntaxWarning","SystemError","SystemExit","TabError","TimeoutError","TypeError","UnboundLocalError",
		"UnicodeDecodeError","UnicodeEncodeError","UnicodeError","UnicodeTranslateError",
		"UnicodeWarning","UserWarning","ValueError","Warning","ZeroDivisionError"
	];
	var htmlreplace={"&":"&amp","<":"&lt;",">":"&gt;"};
	var regexmatch=[
		["[_a-zA-Z][_a-zA-Z0-9]*",styledefault],
		[arrspecial,stylespecial],
		[arrimport,styleimport],
		[arrbuiltin,stylebuiltin],
		[arrkeyword,stylekeyword],
		[arrexception,styleexception],
		["(?:0|[1-9]\\d*)(?:\\.\\d*)?(?:[eE][+\\-]?\\d+)?",stylenumber],
		["0[xX][0-9a-fA-F]*",stylenumber],
		["[\\~\\!\\@\\$\\%\\^\\&\\*\\(\\)\\-\\+\\=\\<\\>\\/\\|\\[\\]]+",styleoperator],
		['"(?:\\\\[\\s\\S]|[^"\\\\])*?"',stylequote],
		["'(?:\\\\[\\s\\S]|[^'\\\\])*?'",stylequote],
		['"""[\\s\\S]*?"""',stylemultiquote],
		["'''[\\s\\S]*?'''",stylemultiquote],
		["#.*",stylecomment]
	];
	for (var i=0;i<regexmatch.length;i++) {
		var reg=regexmatch[i][0];
		if (i>0 && i<6) {reg="("+reg.join("|")+")[^_0-9a-zA-Z]";}
		regexmatch[i][0]=new RegExp(reg);
	}
	// Begin parsing the text.
	var prev=styledefault;
	var ret="<span style=\""+styledefault+"\">";
	while (text.length>0) {
		var minpos=text.length;
		var mintext="";
		var minstyle=styledefault;
		// Find the regex closest to index 0. If two occur at the same index, take the
		// latter regex.
		for (var i=0;i<regexmatch.length;i++) {
			var match=text.match(regexmatch[i][0]);
			if (match!==null && minpos>=match.index) {
				minpos=match.index;
				mintext=match[match.length-1];
				minstyle=regexmatch[i][1];
			}
		}
		// If we skipped over text and it's not whitespace, give it the default style.
		var prefix=text.substring(0,minpos);
		if (prefix.trim().length>0 && prev!==styledefault) {
			ret+="</span><span style=\""+styledefault+"\">";
			prev=styledefault;
		}
		ret+=prefix;
		// Append and style the best matched regex.
		if (prev!==minstyle) {
			ret+="</span><span style=\""+minstyle+"\">";
			prev=minstyle;
		}
		for (var i=0;i<mintext.length;i++) {
			var c=mintext[i];
			var r=htmlreplace[c];
			if (r===undefined) {ret+=c;}
			else {ret+=r;}
		}
		text=text.substring(minpos+mintext.length);
	}
	return ret+"</span>";
}

function HighlightUnileq(str) {
	// Convert unileq assembly language into a formatted HTML string.
	// Define styles.
	var stylearr=[
		"</span><span style='color:#eeeeee'>", // default, number, operator, label ref
		"</span><span style='color:#999999'>", // comment
		"</span><span style='color:#aabb80'>"  // label declaration
	];
	var styledefault =0;
	var stylecomment =1;
	var stylenumber  =0;
	var styleoperator=0;
	var stylelabelref=0;
	var stylelabeldec=2;
	var style=styledefault,prevstyle=styledefault;
	var htmlconvert=document.createElement("div");
	var htmlret="<span>";
	// Helper functions for processing the string.
	var i=0,i0=0,j=0,len=str.length,c;
	function  CNUM(c) {return (c<=57?c+208:((c+191)&~32)+10)&255;}
	function ISLBL(c) {return CNUM(c)<36 || c===95 || c===46 || c>127;}
	function  ISOP(c) {return c===43 || c===45;}
	function   NEXT() {return (c=i++<len?str.charCodeAt(i-1):0);}
	// Process the string.
	NEXT();
	while (c!==0) {
		i0=i-1;
		if (c===13 || c===10 || c===9 || c===32) {
			// Whitespace.
			NEXT();
		} else if (c===35) {
			// Comment. If next='|', use the multi-line format.
			var mask=0,eoc=10,n=0;
			if (NEXT()===124) {mask=255;eoc=31779;NEXT();}
			while (c!==0 && n!==eoc) {n=((n&mask)<<8)+c;NEXT();}
			style=stylecomment;
		} else if (ISOP(c)) {
			// Operator.
			NEXT();
			style=styleoperator;
		} else if (CNUM(c)<10) {
			// Number. If it starts with "0x", use hexadecimal.
			var token=10;
			if (c===48 && (NEXT()===120 || c===88)) {token=16;NEXT();}
			while (CNUM(c)<token) {NEXT();}
			style=stylenumber;
		} else if (c===63) {
			// Current address token.
			NEXT();
			style=stylelabelref;
		} else if (ISLBL(c)) {
			// Label.
			while (ISLBL(c)) {NEXT();}
			if (c===58) {
				// Label declaration.
				NEXT();
				style=stylelabeldec;
			} else {
				style=stylelabelref;
			}
		} else if (c===58) {
			// Lone label declaration.
			NEXT();
			style=stylelabeldec;
		} else {
			// Unknown
			NEXT();
			style=styledefault;
		}
		if (prevstyle!==style) {
			// Extract the highlighted substring and convert it to HTML friendly text.
			var sub=str.substring(j,i0);
			htmlconvert.innerText=sub;
			sub=htmlconvert.innerHTML;
			htmlret+=stylearr[prevstyle]+sub;
			j=i0;
			prevstyle=style;
		}
	}
	// We need to manually handle the tail end of the string.
	var sub=str.substring(j,str.length);
	htmlconvert.innerText=sub;
	sub=htmlconvert.innerHTML;
	htmlret+=stylearr[prevstyle]+sub+"</span>";
	return htmlret;
}

function HighlightStyle(classname,func) {
	// Replace innerHTML with highlighted text.
	var elems=document.getElementsByClassName(classname);
	for (var i=0;i<elems.length;i++) {
		var elem=elems[i];
		elem.innerHTML=func(elem.innerText);
	}
}

function StyleFooter() {
	// De-obfuscate the email address in the footer to allow the email to work with
	// ctrl+f.
	var footer=document.getElementById("footer");
	if (footer!==null) {
		var text=footer.innerHTML;
		footer.innerHTML=text.replace(new RegExp("\\<b\\>.*?\\<\\/b\\>","g"),"");
	}
}

function StyleOnload() {
	// var time=performance.now();
	StyleFooter();
	HighlightStyle("langpython",HighlightPython);
	HighlightStyle("langunileq",HighlightUnileq);
	// console.log("Time: "+(performance.now()-time));
	// 55 ms
}

window.addEventListener("load",StyleOnload,true);
