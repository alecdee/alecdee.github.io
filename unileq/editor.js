//Author  : Alec Dee, akdee144@gmail.com.
//Modified: 17 Jul 2021
/*jshint bitwise: false*/
/*jshint eqeqeq: true*/

function init_editor() {
	var runbutton=document.getElementById("unileq_run");
	var resetbutton=document.getElementById("unileq_reset");
	var input=document.getElementById("unileq_editor");
	var output=document.getElementById("unileq_output");
	var select=document.getElementById("unileq_demo");
	var unl=unlcreate(output);
	var running=0;
	var frametime=0;
	function loadfile(path) {
		var xhr=new XMLHttpRequest();
		xhr.onreadystatechange=function(){
			if (xhr.readyState===4) {
				unlclear(unl);
				running=0;
				setTimeout(update,0);
				if (xhr.status===200) {
					var name=path.split("/");
					input.value=xhr.response;
					output.value="Loaded "+name[name.length-1];
					update_text();
				} else {
					output.value="Unable to open "+path;
				}
			}
		};
		xhr.open("GET",path,true);
		xhr.send();
	}
	function update() {
		var time=performance.now();
		var rem=frametime-time+16.666667;
		if (rem>1.0) {
			setTimeout(update,1);
			return;
		}
		rem=rem>-16.0?rem:-16.0;
		frametime=time+rem;
		//There's no good unicode character for a pause button, so use 2 vertical bars
		//instead.
		var text="<span style='font-size:60%;vertical-align:middle'>&#9616;&#9616;</span>&nbsp;&nbsp;&nbsp;Pause";
		if (unl.state!==UNL_RUNNING) {
			running=0;
			text="&#9654;&nbsp;&nbsp;&nbsp;Run";
			if (unl.state!==UNL_COMPLETE && output!==null) {
				output.value+=unl.statestr;
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
			unlrun_fast(unl,250000);
			setTimeout(update,0);
		}
	}
	//Setup the run button.
	runbutton.onclick=function() {
		if (unl.state===UNL_RUNNING) {
			running=1-running;
		} else {
			unlparsestr(unl,input.value);
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
		unlclear(unl);
		running=0;
		setTimeout(update,0);
	};
	//Setup the example select menu.
	select.onchange=function() {
		if (select.value==="") {
			unlclear(unl);
			input.value="";
			update_text();
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
			input.value=arg;
			output.value="";
		}
	}
	//Setup editor highlighting. We do this by creating a textarea and then displaying
	//a colored div directly under it.
	var container=document.createElement("div");
	var highlight=document.createElement("div");
	input.parentNode.replaceChild(container,input);
	container.appendChild(highlight);
	container.appendChild(input);
	//Copy the textarea attributes to the container div.
	//We need to do this before changing the input attributes.
	var inputstyle=window.getComputedStyle(input);
	var valuelist=Object.values(inputstyle);
	var allow=new RegExp("(background|border|margin)","i");
	for (var i=0;i<valuelist.length;i++) {
		var name=valuelist[i];
		if (name.match(allow)) {
			container.style[name]=inputstyle[name];
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
	for (var i=0;i<valuelist.length;i++) {
		var name=valuelist[i];
		if (name.match(allow) || !name.match(block)) {
			highlight.style[name]=inputstyle[name];
		}
	}
	highlight.style.resize="none";
	highlight.style.overflow="hidden";
	//Make the textarea's text invisible, except for the caret.
	input.style.color="rgba(0,0,0,0)";
	input.style["caret-color"]=caretcolor;
	function update_text() {
		highlight.innerHTML=unileq_highlight(input.value);
	}
	function update_position() {
		container.style.width=input.style.width;
		container.style.height=input.style.height;
		highlight.style.left=(-input.scrollLeft).toString()+"px";
		highlight.style.top=(-input.scrollTop).toString()+"px";
		highlight.style.width=(input.clientWidth+input.scrollLeft).toString()+"px";
		highlight.style.height=(input.clientHeight+input.scrollTop).toString()+"px";
	}
	input.oninput=update_text;
	input.onscroll=update_position;
	new ResizeObserver(update_position).observe(input);
	update_text();
	update_position();
}

window.addEventListener("load",init_editor,true);