/*
Author  : Alec Dee, akdee144@gmail.com
Modified: 2 Oct 2021

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
	var select=document.getElementById("unileq_demo");
	var advanced=document.getElementById("unileq_advanced");
	var menu=document.getElementById("unileq_menu");
	var keygrab=document.getElementById("unileq_keyboard");
	var unl=UnlCreate(output);
	var running=0;
	var frametime=0;
	function update() {
		if (running===1) {
			setTimeout(update,16);
		}
		//There's no good unicode character for a pause button, so use 2 vertical bars
		//instead.
		var text="<span style='font-size:60%;vertical-align:middle'>&#9616;&#9616;</span>&nbsp;&nbsp;&nbsp;Pause";
		if (unl.state!==UNL_RUNNING) {
			running=0;
			text="&#9654;&nbsp;&nbsp;&nbsp;Run";
			if (unl.state!==UNL_COMPLETE) {
				unl.Print(unl.statestr);
			}
		} else if (running===0) {
			text="&#9654;&nbsp;&nbsp;&nbsp;Resume";
		}
		if (runbutton.innerHTML!==text) {
			runbutton.innerHTML=text;
		}
		if (running===1) {
			//Instructions per frame is hard to time due to browser timer inconsistencies.
			//250k instructions per frame at 60fps seems to work well across platforms.
			unl.Run(0.015);
		}
	}
	//Setup the run button.
	runbutton.onclick=function() {
		if (unl.state===UNL_RUNNING) {
			running=1-running;
		} else {
			unl.ParseStr(input.value);
			running=1;
		}
		if (running===1) {
			frametime=performance.now()-17;
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
	//Parse arguments.
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
	var updatetext=function() {
		highlight.innerHTML=HighlightUnileq(input.value);
	};
	var updateposition=function() {
		container.style.width=input.style.width;
		container.style.height=input.style.height;
		highlight.style.left=(-input.scrollLeft)+"px";
		highlight.style.top=(-input.scrollTop)+"px";
		highlight.style.width=(input.clientWidth+input.scrollLeft)+"px";
		highlight.style.height=(input.clientHeight+input.scrollTop)+"px";
	};
	if (window.navigator.userAgent.match("(MSIE\\s|Trident/)")) {
		//If we're using IE, fix text wrapping and tab sizes.
		input.wrap="off";
		var tabs=new RegExp("\t","g");
		updatetext=function() {
			var text=input.value.replace(tabs,"        ");
			highlight.innerHTML=HighlightUnileq(text);
		};
	} else {
		//Enable resizing.
		new ResizeObserver(updateposition).observe(input);
	}
	input.oninput=updatetext;
	input.onscroll=updateposition;
	updatetext();
	updateposition();
	loadfile("./perftest.unl");
}

window.addEventListener("load",UnlInitEditor,true);