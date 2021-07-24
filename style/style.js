//Author  : Alec Dee, akdee144@gmail.com.
//Modified: 19 Jul 2021
/*jshint bitwise: false*/
/*jshint eqeqeq: true*/

function python_highlight(text) {
	//Set up regular expressions to match an expression to a style.
	var style_default   ="color:#cccccc";
	var style_comment   ="color:#999999";
	var style_quote     ="color:#2aa198";
	var style_multiquote="color:#2aa198";
	var style_number    ="color:#2aa198";
	var style_operator  ="color:#cccccc";
	var style_special   ="color:#2aa198";
	var style_import    ="color:#859900"; 
	var style_builtin   ="color:#859900"; 
	var style_keyword   ="color:#859900";
	var style_exception ="color:#859900";
	var arr_special=["False","None","True"];
	var arr_import=["as","from","import"];
	var arr_builtin=[
		"__build_class__","__debug__","__doc__","__import__","__loader__","__name__","__package__","__spec__",
		"abs","all","any","ascii","bin","bool","bytearray","bytes","callable","chr","classmethod","compile",
		"complex","copyright","credits","delattr","dict","dir","divmod","enumerate","eval","exec","exit",
		"filter","float","format","frozenset","getattr","globals","hasattr","hash","help","hex","id","input",
		"int","isinstance","issubclass","iter","len","license","list","locals","map","max","memoryview","min",
		"next","object","oct","open","ord","pow","print","property","quit","range","repr","reversed","round",
		"set","setattr","slice","sorted","staticmethod","str","sum","super","tuple","type","vars","zip"
	];
	var arr_keyword=[
		"and","assert","break","class","continue","def","del","elif","else","except","exec","finally","for",
		"global","if","in","is","lambda","not","or","pass","print","raise","return","try","while","with","yield"
	];
	var arr_exception=[
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
	var regex_match=[
		["[_a-zA-Z][_a-zA-Z0-9]*",style_default],
		[arr_special,style_special],
		[arr_import,style_import],
		[arr_builtin,style_builtin],
		[arr_keyword,style_keyword],
		[arr_exception,style_exception],
		["(?:0|[1-9]\\d*)(?:\\.\\d*)?(?:[eE][+\\-]?\\d+)?",style_number],
		["0[xX][0-9a-fA-F]*",style_number],
		["[\\~\\!\\@\\$\\%\\^\\&\\*\\(\\)\\-\\+\\=\\<\\>\\/\\|\\[\\]]+",style_operator],
		["\".*\"",style_quote],
		["\'.*\'",style_quote],
		["\"\"\"[\\s\\S]*?\"\"\"",style_multiquote],
		["'''[\\s\\S]*?'''",style_multiquote],
		["#.*",style_comment]
	];
	for (var i=0;i<regex_match.length;i++) {
		var reg=regex_match[i][0];
		if (i>0 && i<6) {reg="("+reg.join("|")+")[^_0-9a-zA-Z]";}
		regex_match[i][0]=new RegExp(reg);
	}
	//Begin parsing the text.
	var prev=style_default;
	var ret="<span style=\""+style_default+"\">";
	while (text.length>0) {
		var minpos=text.length;
		var mintext="";
		var minstyle=style_default;
		//Find the regex closest to index 0. If two occur at the same index, take the
		//latter regex.
		for (var i=0;i<regex_match.length;i++) {
			var match=text.match(regex_match[i][0]);
			if (match!==null && minpos>=match.index) {
				minpos=match.index;
				mintext=match[match.length-1];
				minstyle=regex_match[i][1];
			}
		}
		//If we skipped over text and it's not whitespace, give it the default style.
		var prefix=text.substring(0,minpos);
		if (prefix.trim().length>0 && prev!==style_default) {
			ret+="</span><span style=\""+style_default+"\">";
			prev=style_default;
		}
		ret+=prefix;
		//Append and style the best matched regex.
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

function unileq_highlight0(text)
{
	//Set up regular expressions to match an expression to a style.
	var style_default ="color:#eeeeee";
	var style_comment ="color:#999999";
	var style_number  ="color:#eeeeee";
	var style_operator="color:#eeeeee";
	var style_labelref="color:#eeeeee";
	var style_labeldec="color:#aabb80";
	var htmlreplace={"&":"&amp","<":"&lt;",">":"&gt;"};
	var regex_match=
	[
		["[\\._a-zA-Z][\\._a-zA-Z0-9]*",style_labelref],
		["[\\._a-zA-Z][\\._a-zA-Z0-9]*\\:",style_labeldec],
		["\\?",style_labelref],
		["0[xX][0-9a-fA-F]*",style_number],
		["[0-9]+",style_number],
		["[\\-\\+]",style_operator],
		["#.*",style_comment],
		["#\\|[\\s\\S]*?\\|#",style_comment]
	];
	for (var i=0;i<regex_match.length;i++)
	{
		var reg=regex_match[i][0];
		regex_match[i][0]=new RegExp(reg);
	}
	//Begin parsing the text.
	var prev=style_default;
	var ret="<span style=\""+style_default+"\">";
	while (text.length>0)
	{
		var minpos=text.length;
		var mintext="";
		var minstyle=style_default;
		//Find the regex closest to index 0. If two occur at the same index, take the
		//latter regex.
		for (var i=0;i<regex_match.length;i++)
		{
			var match=text.match(regex_match[i][0]);
			if (match!==null && minpos>=match.index)
			{
				minpos=match.index;
				mintext=match[match.length-1];
				minstyle=regex_match[i][1];
			}
		}
		//If we skipped over text and it's not whitespace, give it the default style.
		var prefix=text.substring(0,minpos);
		if (prefix.trim().length>0 && prev!==style_default)
		{
			ret+="</span><span style=\""+style_default+"\">";
			prev=style_default;
		}
		ret+=prefix;
		//Append and style the best matched regex.
		if (prev!==minstyle)
		{
			ret+="</span><span style=\""+minstyle+"\">";
			prev=minstyle;
		}
		for (var i=0;i<mintext.length;i++)
		{
			var c=mintext[i];
			var r=htmlreplace[c];
			if (r===undefined) {ret+=c;}
			else {ret+=r;}
		}
		text=text.substring(minpos+mintext.length);
	}
	return ret+"</span>";
}

function unileq_highlight(str) {
	var style_default ="eeeeee";
	var style_comment ="999999";
	var style_number  ="eeeeee";
	var style_operator="eeeeee";
	var style_labelref="eeeeee";
	var style_labeldec="aabb80";
	var htmlconvert=document.createElement("div");
	var ret="";
	var style=null,prevstyle=null;
	//Convert unileq assembly language into a unileq program.
	var i=0,j0=0,j1=0,len=str.length,c;
	function  CNUM(c) {return (c<=57?c+208:((c+191)&~32)+10)&255;}
	function ISLBL(c) {return CNUM(c)<36 || c===95 || c===46 || c>127;}
	function  ISOP(c) {return c===43 || c===45;}
	function   NEXT() {return (c=i++<len?str.charCodeAt(i-1):0);}
	//Process the string.
	NEXT();
	while (c!==0) {
		j1=i-1;
		if (c===13 || c===10 || c===9 || c===32) {
			//Whitespace.
			NEXT();
		} else if (c===35) {
			//Comment. If next='|', use the multi-line format.
			var mask=0,eoc=10,n=0;
			if (NEXT()===124) {mask=255;eoc=31779;NEXT();}
			while (c!==0 && n!==eoc) {n=((n&mask)<<8)+c;NEXT();}
			style=style_comment;
		} else if (ISOP(c)) {
			//Operator.
			NEXT();
			style=style_operator;
		} else if (CNUM(c)<10) {
			//Number. If it starts with "0x", use hexadecimal.
			var token=10;
			if (c===48 && (NEXT()===120 || c===88)) {token=16;NEXT();}
			while (CNUM(c)<token) {NEXT();}
			style=style_number;
		} else if (c===63) {
			//Current address token.
			NEXT();
			style=style_labelref;
		} else if (ISLBL(c)) {
			//Label.
			while (ISLBL(c)) {NEXT();}
			if (c===58) {
				//Label declaration.
				NEXT();
				style=style_labeldec;
			} else {
				style=style_labelref;
			}
		} else if (c===58) {
			//Lone label declaration.
			NEXT();
			style=style_labeldec;
		} else {
			//Unknown
			NEXT();
			style=style_default;
		}
		if (prevstyle!==style) {
			//Extract the highlighted substring and convert it to HTML friendly text.
			if (prevstyle!==null) {
				var sub=str.substring(j0,j1);
				htmlconvert.innerText=sub;
				sub=htmlconvert.innerHTML;
				ret+='<span style="color:#'+prevstyle+'">'+sub+'</span>';
				j0=j1;
			}
			prevstyle=style;
		}
	}
	if (prevstyle!==null) {
		var sub=str.substring(j0,i);
		htmlconvert.innerText=sub;
		sub=htmlconvert.innerHTML;
		ret+='<span style="color:#'+prevstyle+'">'+sub+'</span>';
	}
	return ret;
}

function style_highlight(classname,func) {
	//Replace innerHTML with highlighted text.
	var elems=document.getElementsByClassName(classname);
	for (var i=0;i<elems.length;i++) {
		var elem=elems[i];
		elem.innerHTML=func(elem.innerText);
	}
}

function style_footer() {
	//De-obfuscate the email address in the footer to allow the email to work with
	//ctrl+f.
	var foot=document.getElementById("footer");
	var text=foot.innerHTML;
	foot.innerHTML=text.replace(new RegExp("\\<b\\>.*?\\<\\/b\\>","g"),"");
}

function screen_reader() {
	//Screen readers have trouble handling plaintext pages with no formatting, so
	//mark paragraphs with <p> tags.
	var elems=document.getElementsByClassName("content");
	for (var e=0;e<elems.length;e++) {
		var elem=elems[e];
		var text=elem.innerHTML;
		var regeol=new RegExp("((\\n\\n)|(\\r\\n\\r\\n)|$)");
		var strdiv="\\<div[\\s\\S]*?(\\/div\\s*\\>|$)";
		var strimg="\\<img[\\s\\S]*?(\\>|$)";
		var strsvg="\\<svg[\\s\\S]*?(\\/svg\\s*\\>|$)";
		var regblock=new RegExp("\\s*("+strdiv+"|"+strimg+"|"+strsvg+")");
		var ret="<style>p {display:inline-block;width:100%;}</style>";
		while (text.length>0) {
			//If we can't find a block at the beginning of the text, add a paragraph.
			var s=text.match(regblock);
			if (s===null || s.index>0) {
				s=text.match(regeol);
				ret+="<p>"+text.substring(0,s.index)+"</p>";
			}
			ret+=s[0];
			text=text.substring(s.index+s[0].length);
		}
		elem.innerHTML=ret;
	}
}

function style_onload() {
	//var time=performance.now();
	//screen_reader();
	style_footer();
	style_highlight("langpython",python_highlight);
	style_highlight("langunileq",unileq_highlight);
	//console.log("Time: "+(performance.now()-time));
	//55 ms
}

window.addEventListener("load",style_onload,true);
