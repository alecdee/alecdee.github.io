//Author  : Alec Dee, akdee144@gmail.com.
//Modified: 17 Jul 2021
/*jshint bitwise: false*/
/*jshint eqeqeq: true*/

function InitInterpreter() {
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
		//Clear the output buffer if it gets full.
		if (output!==null && output.value.length>=10000) {
			output.value="";
		}
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
		loadfile(select.value);
	};
	//Parse arguments.
	var regex=/.*?\?(file|demo|source)=(.*)/g;
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
}

window.addEventListener("load",InitInterpreter,true);