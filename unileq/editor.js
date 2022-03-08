/*
Author  : Alec Dee, akdee144@gmail.com
Modified: 6 Mar 2022

TODO:
Find out if Firefox fixed the textarea padding bug:
https://bugzilla.mozilla.org/show_bug.cgi?id=748518
*/
/*jshint bitwise: false*/
/*jshint eqeqeq: true  */
/*jshint curly: true   */

function UnlInitEditor() {
	var runbutton=document.getElementById("unileq_run");
	var resetbutton=document.getElementById("unileq_reset");
	var input=document.getElementById("unileq_editor");
	var output=document.getElementById("unileq_output");
	var graphics=document.getElementById("unileq_canvas");
	var select=document.getElementById("unileq_demo");
	var advanced=document.getElementById("unileq_advanced");
	var menu=document.getElementById("unileq_menu");
	var keygrab=document.getElementById("unileq_keyboard");
	var unl=UnlCreate(output,graphics);
	var running=0;
	function update() {
		//Our main event loop. Run the main unileq loop for 15ms and queue the next
		//update for 12ms in the future. This will give the browser time to handle events
		//and spend most of our time executing unileq instructions.
		var runtext;
		if (unl.state!==UNL_RUNNING) {
			running=0;
			runtext="&#9654;&nbsp;&nbsp;&nbsp;Run";
			if (unl.state!==UNL_COMPLETE) {
				unl.Print(unl.statestr);
			}
		} else if (running===1) {
			//There's no good unicode character for a pause button, so use 2 vertical bars
			//instead.
			runtext="<span style='font-size:60%;vertical-align:middle'>&#9616;&#9616;</span>&nbsp;&nbsp;&nbsp;Pause";
		} else {
			runtext="&#9654;&nbsp;&nbsp;&nbsp;Resume";
		}
		if (runbutton.innerHTML!==runtext) {
			runbutton.innerHTML=runtext;
		}
		if (running===1) {
			//Put the next update on the event queue before running our main loop.
			setTimeout(update,12);
			unl.Run(performance.now()+15);
		}
	}
	//Setup the run button.
	runbutton.onclick=function() {
		if (unl.state===UNL_RUNNING) {
			running=1-running;
		} else {
			unl.ParseAssembly(input.value);
			running=1;
		}
		if (running===1) {
			setTimeout(update,0);
		}
	};
	runbutton.innerHTML="&#9654;&nbsp;&nbsp;&nbsp;Resume&nbsp;";
	runbutton.style.width=runbutton.clientWidth.toString()+"px";
	runbutton.innerHTML="&#9654;&nbsp;&nbsp;&nbsp;Run";
	//Setup the reset button.
	resetbutton.onclick=function() {
		unl.Clear();
		running=0;
		setTimeout(update,0);
	};
	//Setup the advanced menu.
	advanced.onclick=function() {
		if (menu.style.display==="none") {
			menu.style.display="block";
		} else {
			menu.style.display="none";
		}
	};
	var inputgrab=function(e) {
		var code=e.keyCode;
		if (code===9 || (code>=120 && code<=122)) {
			e.preventDefault();
			if (code===9) {
				//Tab
				document.execCommand("insertText",false,"\t");
			} else if (code===120) {
				//F9
				runbutton.onclick();
			} else if (code===121) {
				//F10
				resetbutton.onclick();
			} else if (code===122) {
				//F11
				keygrab.checked=false;
				keygrab.onchange();
			}
		}
	};
	keygrab.onchange=function() {
		if (keygrab.checked) {
			input.onkeydown=inputgrab;
		} else {
			input.onkeydown=null;
		}
	};
	keygrab.onchange();
	//Helper function to load files.
	function loadfile(path) {
		var xhr=new XMLHttpRequest();
		xhr.onreadystatechange=function(){
			if (xhr.readyState===4) {
				unl.Clear();
				running=0;
				setTimeout(update,0);
				if (xhr.status===200) {
					var name=path.split("/");
					input.value=xhr.response;
					unl.Print("Loaded "+name[name.length-1]+"\n");
					updatetext();
				} else {
					unl.Print("Unable to open "+path+"\n");
				}
			}
		};
		xhr.open("GET",path,true);
		xhr.send();
	}
	//Setup the example select menu.
	select.onchange=function() {
		if (select.value==="") {
			unl.Clear();
			input.value="";
			updatetext();
		} else {
			loadfile(select.value);
		}
	};
	//Parse URL arguments.
	var regex=new RegExp(".*?\\?(file|demo|source)=(.*)","g");
	var match=regex.exec(decodeURI(window.location.href));
	if (match!==null) {
		var type=match[1];
		var arg=match[2];
		if (type==="file") {
			loadfile(arg);
		} else if (type==="demo") {
			for (var i=0;i<select.length;i++) {
				var option=select[i];
				if (option.innerText===arg) {
					select.value=option.value;
					loadfile(option.value);
				}
			}
		} else if (type==="source") {
			unl.Clear();
			input.value=arg;
		}
	}
	//If we're using IE, avoid text highlighting.
	if (window.navigator.userAgent.match("(MSIE\\s|Trident/)")) {
		return;
	}
	//Setup editor highlighting. We do this by creating a textarea and then displaying
	//a colored div directly under it.
	var container=document.createElement("div");
	var highlight=document.createElement("div");
	input.parentNode.replaceChild(container,input);
	container.appendChild(highlight);
	container.appendChild(input);
	//Copy the textarea attributes to the container div. We need to do this before
	//changing the input attributes.
	var inputstyle=window.getComputedStyle(input);
	var allow=new RegExp("(background|border|margin)","i");
	for (var i=0;i<inputstyle.length;i++) {
		var key=inputstyle[i];
		if (key.match(allow)) {
			container.style[key]=inputstyle[key];
		}
	}
	container.style.position="relative";
	container.style.overflow="hidden";
	//Set the textarea to absolute positioning within the container and remove all
	//decorations.
	var caretcolor=inputstyle["caret-color"];
	input.style.position="absolute";
	input.style.left="0";
	input.style.top="0";
	input.style.margin="0";
	input.style.border="none";
	input.style.background="none";
	//Copy the textarea attributes to the highlight div.
	inputstyle=window.getComputedStyle(input);
	var block=new RegExp("color","i");
	for (var i=0;i<inputstyle.length;i++) {
		var key=inputstyle[i];
		if (key.match(allow) || !key.match(block)) {
			highlight.style[key]=inputstyle[key];
		}
	}
	highlight.style.resize="none";
	highlight.style.overflow="hidden";
	//Make the textarea text invisible, except for the caret.
	input.style.color="rgba(0,0,0,0)";
	input.style["caret-color"]=caretcolor;
	var updateposition=function() {
		container.style.width=input.style.width;
		container.style.height=input.style.height;
		highlight.style.left=(-input.scrollLeft)+"px";
		highlight.style.top=(-input.scrollTop)+"px";
		highlight.style.width=(input.clientWidth+input.scrollLeft)+"px";
		highlight.style.height=(input.clientHeight+input.scrollTop)+"px";
	};
	var updatetext=function() {
		updateposition();
		highlight.innerHTML=UnlHighlightScroll(input);
	};
	new ResizeObserver(updatetext).observe(input);
	input.oninput=updatetext;
	input.onscroll=updatetext;
	updatetext();
}

function UnlHighlightScroll(input) {
	//Highlighting the whole source code can be slow, so highlight only the portion
	//that we can see.
	var str=input.value;
	//Determine what lines are visible.
	var len=str.length,lines=1;
	for (var i=0;i<len;i++) {
		lines+=str.charCodeAt(i)===10;
	}
	var vismin=(input.scrollTop/input.scrollHeight)*lines-1;
	var vismax=vismin+(input.clientHeight/input.scrollHeight)*lines+2;
	//console.log(vismin,vismax);
	var comment=0;
	//Find where the first visible line starts, and if it's a block comment.
	var i=0,line=0,c;
	while (i<len && line<vismin) {
		c=str.charCodeAt(i++);
		if (c===10) {
			line++;
		} else if (comment===1) {
			if (c===124 && str.charCodeAt(i)===35) {
				i++;
				comment=0;
			}
		} else if (c===35) {
			if (str.charCodeAt(i)===124) {
				i++;
				comment=1;
			}
		}
	}
	if (line<2) {
		line=0;
		i=0;
		comment=0;
	}
	var pre="<br>".repeat(line-comment*2);
	//Find where the visible lines end.
	var j=i;
	while (j<len && line<=vismax) {
		if (str.charCodeAt(j++)===10) {
			line++;
		}
	}
	//Get the visible substring. If we're in a block comment, manually add a #| for
	//the highlighter.
	var sub=str.substring(i,j);
	if (comment===1) {sub="#|\n\n"+sub;}
	return pre+HighlightUnileq(sub);
}

window.addEventListener("load",UnlInitEditor,true);
