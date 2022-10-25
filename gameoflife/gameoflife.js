/*------------------------------------------------------------------------------


gameoflife.js - v1.01

Copyright 2020 Alec Dee - MIT license - SPDX: MIT
alecdee.github.io - akdee144@gmail.com


--------------------------------------------------------------------------------
TODO


When we hit "run", store the current state+view. When we hit "reset", go
back to the stored state.


*/
/* jshint bitwise: false */
/* jshint eqeqeq: true   */
/* jshint curly: true    */


//---------------------------------------------------------------------------------
// Game of Life Engine
//---------------------------------------------------------------------------------

function life_create() {
	// Conway's Game of Life
	// Rules:
	// A live cell with fewer than 2 live neighbors dies by underpopulation.
	// A live cell with greater than 3 live neighbors dies by overpopulation.
	// A dead cell with 3 live neighbors becomes alive by reproduction.
	// All other cells stay the same.
	//
	// Cells are added to the processing queue if their state has changed.
	//
	// Cell state queries are sped up by using coordinate hashing with a hash table of
	// linked lists.
	//
	// Cell states are stored in a single integer so we can advance their state with a
	// single table lookup. Their format is:
	//
	//      state=[3-6:count][2:in queue][1:prev][0:alive]
	var life=new Object();
	// Processing queue and coordinate hash table.
	life.queue=null;
	life.deleted=null;
	life.hashtable=new Array(65536);
	// Neighbors that contribute to a cell's count.
	life.neighbors=[[-1,-1],[0,-1],[1,-1],[-1,0],[1,0],[-1,1],[0,1],[1,1]];
	// mnrule is used to manage whether to queue or delete the cell and set
	// prev=alive. We want the queue bit to be 0 as often as possible to avoid
	// requeuing cells. carule is the cellular automata rule.
	life.mnrule=[
		0,3,0,3,0,7,0,7,8,11,8,11,8,15,8,15,16,19,16,19,16,19,16,19,24,27,24,27,
		28,27,28,27,32,35,32,35,32,39,32,39,40,43,40,43,40,47,40,47,48,51,48,51,
		48,55,48,55,56,59,56,59,56,63,56,63,64,67,64,67,64,71,64,71
	];
	life.carule=[
		0,2,0,2,4,6,4,6,8,10,8,10,12,14,12,14,16,19,16,19,20,23,20,23,25,27,25,
		27,29,31,29,31,32,34,32,34,36,38,36,38,40,42,40,42,44,46,44,46,48,50,48,
		50,52,54,52,54,56,58,56,58,60,62,60,62,64,66,64,66,68,70,68,70
	];
	life.clear=function() {
		// Clears the grid.
		life.queue=null;
		// life.deleted=null;
		var hashtable=life.hashtable;
		for (var i=0;i<65536;i++) {hashtable[i]=null;}
	};
	life.hashcoords=function(x,y) {
		// Hash the coordinates to a single integer.
		var m=0xffff;
		var h=0x526f;
		h=((h^(x&m))+0xaaab)&m;
		h=((h>>3)|(h<<13))&m;
		h^=h>>3;
		h=(h*0xfaab)&m;
		h^=y&m;
		return h;
	};
	life.makecell=function(x,y) {
		// Return the cell at the given coordinates, or make a new one.
		var hash=life.hashcoords(x,y);
		var hashtable=life.hashtable;
		var next=hashtable[hash];
		var cell=next;
		while (cell!==null && (cell.x!==x || cell.y!==y)) {
			cell=cell.next;
		}
		if (cell===null) {
			// Make a new cell. Use a previously deleted one if possible.
			cell=life.deleted;
			if (cell!==null) {life.deleted=cell.queue;}
			else {cell=new Object();}
			cell.x=x;
			cell.y=y;
			cell.state=0;
			// Queue for state processing.
			cell.queue=null;
			// Doubly linked pointers for the hash table.
			cell.hash=hash;
			cell.prev=null;
			cell.next=next;
			if (next!==null) {next.prev=cell;}
			hashtable[hash]=cell;
		}
		// If it's not queued, add it.
		if ((cell.state&4)===0) {
			cell.state|=4;
			cell.queue=life.queue;
			life.queue=cell;
		}
		return cell;
	};
	life.advance=function(generations) {
		// Advance the state by a given number of generations.
		if (generations===undefined) {generations=1;}
		var hashtable=life.hashtable,makecell=life.makecell;
		var neighbors=life.neighbors;
		var neighlen=neighbors.length;
		while (generations>0) {
			generations-=1;
			// Management loop. If a cell has been updated, update its neighbors. Also check if
			// the cell should be requeued or deleted.
			var rule=life.mnrule;
			var cell=life.queue;
			life.queue=null;
			while (cell!==null) {
				var state=rule[cell.state];
				var inc=((state|4)-cell.state)<<2;
				cell.state=state;
				// Update neighbors.
				if (inc!==0) {
					var x=cell.x,y=cell.y,n;
					for (var i=0;i<neighlen;i++) {
						n=neighbors[i];
						makecell(x+n[0],y+n[1]).state+=inc;
					}
				}
				// Delete or requeue cell.
				var qnext=cell.queue;
				if (state===0) {
					var prev=cell.prev,next=cell.next;
					if (prev!==null) {prev.next=next;}
					else { hashtable[cell.hash]=next;}
					if (next!==null) {next.prev=prev;}
					cell.queue=life.deleted;
					life.deleted=cell;
				} else if (state&4) {
					cell.queue=life.queue;
					life.queue=cell;
				}
				cell=qnext;
			}
			// Cellular automata loop.
			rule=life.carule;
			cell=life.queue;
			while (cell!==null) {
				cell.state=rule[cell.state];
				cell=cell.queue;
			}
		}
	};
	life.setcell=function(xy,state) {
		// Set a cell to the given state.
		state=state?1:0;
		if (life.getcell(xy)!==state) {
			life.makecell(xy[0],xy[1]).state^=1;
		}
	};
	life.getcell=function(xy) {
		// Get the state of given cell.
		var x=xy[0],y=xy[1];
		var hash=life.hashcoords(x,y);
		var cell=life.hashtable[hash];
		while (cell!==null && (cell.x!==x || cell.y!==y)) {
			cell=cell.next;
		}
		return cell!==null?cell.state&1:0;
	};
	life.setcells=function(pat,xy,fmt) {
		// Draw a pattern on the grid.
		//
		// trans values: 0-3=rotate, 4=flip horizontally, 8=flip vertically.
		//
		// fmt   values: points, plaintext, lif, rle, file, and None.
		// If fmt=None, the format will be guessed.
		var trans=0;
		if (fmt===undefined) {
			// Guess what format we're using. Never guess "file".
			for (var i=0;i<4;i++) {
				try
				{
					fmt=["rle","lif","plaintext","points"][i];
					return life.setcells(pat,xy,fmt);
				}
				catch(e) {}
			}
			throw "Unable to determine pattern type";
		}
		var points=[];
		if (fmt==="points") {
			// An array of living cell coordinates.
			var a=1,b=0,c=0,d=1;
			if (trans&4) {a=-1;}
			if (trans&8) {d=-1;}
			while (trans&3) {
				trans-=1;
				var t;
				t=a;a=-c;c=t;
				t=b;b=-d;d=t;
			}
			var x=xy[0],y=xy[1];
			x+=a<b?a:b;
			y+=c<d?c:d;
			try
			{
				var len=pat.length;
				for (var i=0;i<len;i++) {
					var p=pat[i];
					if (p.length!==2 || (typeof p[0])!=="number" || (typeof p[1])!=="number") {
						throw "";
					}
					var px=x+a*p[0]+b*p[1];
					var py=y+c*p[0]+d*p[1];
					points.push([px,py]);
				}
			}
			catch(e) {throw "Not an array of points";}
			// Plot the points.
			var setcell=life.setcell;
			var len=points.length;
			for (var i=0;i<len;i++) {setcell(points[i],1);}
			return null;
		}
		if ((typeof pat)!=="string") {
			throw "Pattern must be a string";
		}
		var lines=pat.split("\n");
		var len=lines.length;
		if (fmt==="plaintext") {
			// A plaintext grid of cells. !=comment, .=dead, O=alive
			var dy=0;
			for (var i=0;i<len;i++) {
				var s=lines[i].replace(/\s/g,"");
				if (s==="" || s[0]==="!") {continue;}
				var dx=0,slen=s.length;
				for (var j=0;j<slen;j++) {
					var c=s[j];
					if (c==="O") {points.push([dx,dy]);}
					else if (c!==".") {throw "Invalid plaintext character";}
					dx+=1;
				}
				dy+=1;
			}
		} else if (fmt==="lif") {
			// Life 1.06 file format.
			if (len===0 || lines[0]!=="#Life 1.06") {
				throw "Invalid Life 1.06 header";
			}
			for (var i=1;i<len;i++) {
				if (lines[i]==="") {continue;}
				var coord;
				try
				{
					coord=lines[i].split();
					coord=[parseInt(coord[0]),parseInt(coord[1])];
					if (isNaN(coord[0]) || isNaN(coord[1])) {throw "";}
				}
				catch(e) {throw "Unable to parse life 1.06 pattern";}
				points.push(coord);
			}
		} else if (fmt==="rle") {
			// Run length encoding.
			var head="",data="";
			for (var i=0;i<len;i++) {
				var line=lines[i].replace(/\s/g,"");
				if    (line.length===0) {continue;}
				else if (line[0]==="x") {head=line.toLowerCase();}
				else if (line[0]!=="#") {data+=line;}
			}
			var w=null,h=null;
			try
			{
				var arr=head.split(",");
				w=parseInt(arr[0].substr(2));
				h=parseInt(arr[1].substr(2));
			}
			catch(e) {w=h=null;}
			if (head!=="x="+w+",y="+h+",rule=b3/s23") {
				throw "Unable to parse RLE header";
			}
			var dx=0,dy=0,num=0;
			len=data.length;
			for (var i=0;i<len;i++) {
				var c=data[i];
				if (c==="o" || c==="b") {
					num+=(num===0)+dx;
					while (dx<num) {
						if (c==="o") {points.push([dx,dy]);}
						dx+=1;
					}
				} else if (c==="$" || c==="!") {
					dx=0;dy+=num+(num===0);
					if (c==="!") {break;}
				} else if (!isNaN(c)) {
					num=num*10+c.charCodeAt(0)-48;
					continue;
				} else {
					throw "Unrecognized character in RLE data";
				}
				num=0;
			}
		} else {
			throw "Format "+fmt+" unrecognized";
		}
		return life.setcells(points,xy,"points");
	};
	life.getcells=function(xy,wh,fmt) {
		// Return the living cells in a given area. If xy or wh are None, return
		// all cells. Allowed formats are: points, plaintext, lif, and rle.
		var x=0,y=0,w=0,h=0,f=0;
		if (xy===undefined || wh===undefined) {
			for (var i=0;i<65536;i++) {
				var cell=life.hashtable[i];
				while (cell!==null) {
					if (cell.state&1) {
						var px=cell.x,py=cell.y;
						if (f===0) {x=w=px;y=h=py;f=1;}
						x=x<px?x:px;y=y<py?y:py;
						w=w>px?w:px;h=h>py?h:py;
					}
					cell=cell.next;
				}
			}
			w-=x-f;
			h-=y-f;
		} else {
			x=xy[0];y=xy[1];
			w=wh[0];h=wh[1];
		}
		// Retrieve an array coordinates for all living cells.
		var points=[];
		var getcell=life.getcell;
		var p=[0,0],dx,dy;
		for (dy=0;dy<h;dy++) {
			for (dx=0;dx<w;dx++) {
				p[0]=x+dx;p[1]=y+dy;
				if (getcell(p)) {points.push([dx,dy]);}
			}
		}
		var len=points.length;
		if (fmt==="points") {
			// A list of points.
			return points;
		} else if (fmt==="plaintext" || fmt===undefined) {
			// A plaintext grid of cells. !=comment, .=dead, O=alive
			w+=1;
			h*=w;
			var ret=new Array(h);
			for (var i=0;i<h;i++) {ret[i]=".";}
			for (var i=w-1;i<h;i+=w) {ret[i]="\n";}
			for (var i=0;i<len;i++) {p=points[i];ret[p[1]*w+p[0]]="O";}
			return ret.join("");
		} else if (fmt==="lif") {
			// Life 1.06 file format.
			var ret="#Life 1.06\n";
			for (var i=0;i<len;i++) {
				ret+=points[i].join(" ")+"\n";
			}
			return ret;
		} else if (fmt==="rle") {
			// Run length encoding.
			var ret="x = "+w+", y = "+h+", rule = B3/S23\n";
			var eol=ret.length;
			var lx=0,ly=0,cnt=0;
			var addnum=function(num,t) {
				if (num>1) {ret+=num;}
				if (num>0) {ret+=t;}
				if (ret.length-eol>69) {ret+="\n";eol=ret.length;}
			};
			for (var i=0;i<len;i++) {
				x=points[i][0];y=points[i][1];
				dx=x-lx;dy=y-ly;
				if (dx || dy) {addnum(cnt,"o");cnt=0;}
				if (dy) {dx=w-lx;}
				addnum(dx,"b");
				addnum(dy,"$");
				if (dy) {addnum(x,"b");}
				lx=x+1;ly=y;
				cnt+=1;
			}
			addnum(cnt,"o");
			return ret+"!\n";
		}
		throw "Format "+fmt+" unrecognized";
	};
	life.clear();
	return life;
}

//---------------------------------------------------------------------------------
// Game of Life GUI
//---------------------------------------------------------------------------------

// ratio, scale, menu, reset, speed, pos, seed, run
// seed=[[x0,y0,pat0],[x1,y1,pat1],...]

function gol_gui(parent,gw,gh,args) {
	// Initialize the game of life GUI and simulator.
	var gui=new Object();
	gui.parent=parent;
	gui.life=life_create();
	gui.initw=gw;
	gui.inith=gh;
	gui.vieww=gw;
	gui.viewh=gh;
	gui.scale=0;
	gui.genreset=Infinity;
	if ("reset" in args) {gui.genreset=args["reset"];}
	gui.menu=0;
	if (args["menu"]!==0 && gui.genreset===Infinity) {gui.menu=1;}
	gui.initspeed=1.0;
	if ("speed" in args) {gui.initspeed=args["speed"];}
	gui.initx=0;
	gui.inity=0;
	if ("pos" in args) {
		var arr=args["pos"];
		gui.initx=arr[0];
		gui.inity=arr[1];
	}
	gui.seed=[];
	if ("seed" in args) {gui.seed=args["seed"];}
	gui.running=1;
	if ("run" in args) {gui.running=args["run"];}
	gui.redraw=1;
	var canvas=document.createElement("canvas");
	gui.drawctx=canvas.getContext("2d");
	parent.style.height="auto";
	parent.appendChild(canvas);
	var arrequal=function(a,b) {
		// Helper function to compare arrays.
		try
		{
			var i=0,l=a.length;
			if (l!==b.length) {return false;}
			while (i<l && a[i]===b[i]) {i++;}
			return i===l;
		} catch(e) {}
		return false;
	};
	gui.reset=function() {
		if (gui.menu!==0) {gui.running=0;}
		gui.gen=0;
		gui.drawrem=1.0;
		gui.drawspeed=gui.initspeed;
		gui.viewx=gui.initx;
		gui.viewy=gui.inity;
		gui.vieww=gui.initw;
		gui.viewh=gui.inith;
		gui.life.clear();
		var len=gui.seed.length;
		for (var i=0;i<len;i++) {
			var xyp=gui.seed[i];
			gui.life.setcells(xyp[2],[xyp[0],xyp[1]]);
		}
		gui.calcview();
	};
	gui.calcview=function() {
		// Recalculate viewing constants and signal to redraw.
		var scale=gui.scale;
		gui.linepix=Math.floor(0.2*scale);
		gui.rectpix=scale-gui.linepix;
		gui.viewoffx=Math.floor(gui.viewx);
		gui.viewoffy=Math.floor(gui.viewy);
		gui.drawoffx=Math.floor((gui.viewx-gui.viewoffx)*scale);
		gui.drawoffy=Math.floor((gui.viewy-gui.viewoffy)*scale);
		gui.redraw=1;
	};
	gui.gridtoscreen=function(p) {
		var x=(p[0]+gui.viewoffx)*gui.scale+gui.drawoffx;
		var y=(p[1]+gui.viewoffy)*gui.scale+gui.drawoffy;
		return [x,y];
	};
	gui.screentogrid=function(p) {
		var line=gui.linepix*0.5;
		var x=Math.floor((p[0]-gui.drawoffx+line)/gui.scale-gui.viewoffx);
		var y=Math.floor((p[1]-gui.drawoffy+line)/gui.scale-gui.viewoffy);
		return [x,y];
	};
	gui.render=function() {
		var ctx=gui.drawctx;
		var vieww=gui.vieww;
		var viewh=gui.viewh;
		var draww=gui.draww;
		var drawh=gui.drawh;
		var scale=Math.floor(gui.parent.offsetWidth/vieww);
		scale=scale>1?scale:1;
		// Resize if the parent size has changed too much.
		if (gui.scale!==scale) {
			gui.scale=scale;
			draww=Math.floor(vieww*scale);
			drawh=Math.floor(viewh*scale);
			var canvas=ctx.canvas;
			canvas.width=draww;
			canvas.height=drawh;
			gui.draww=draww;
			gui.drawh=drawh;
			if (gui.menu!==0) {
				gui.menubar.style.width=draww+"px";
			}
			gui.calcview();
		}
		if (gui.redraw!==0) {
			gui.redraw=0;
			var rectpix=gui.rectpix;
			var viewoffx=gui.viewoffx,viewoffy=gui.viewoffy;
			var drawoffx=gui.drawoffx,drawoffy=gui.drawoffy;
			// Clear the drawing area.
			ctx.fillStyle="#000000";
			ctx.fillRect(0,0,draww,drawh);
			// Draw grid lines.
			if (gui.linepix!==0) {
				var linepix=gui.linepix;
				ctx.fillStyle="#202040";
				for (var x=-scale+drawoffx-linepix;x<draww;x+=scale) {
					ctx.fillRect(x,0,linepix,drawh);
				}
				for (var y=-scale+drawoffy-linepix;y<drawh;y+=scale) {
					ctx.fillRect(0,y,draww,linepix);
				}
			}
			// Fill living cells.
			ctx.fillStyle="#ffffff";
			var getcell=gui.life.getcell;
			var p=[0,0];
			for (var x0=-1;x0<vieww;x0++) {
				for (var y0=-1;y0<viewh;y0++) {
					p[0]=x0-viewoffx;p[1]=y0-viewoffy;
					if (getcell(p)) {
						ctx.fillRect(x0*scale+drawoffx,y0*scale+drawoffy,rectpix,rectpix);
					}
				}
			}
		}
	};
	gui.update=function() {
		// Update the life state.
		if (gui.gen>=gui.genreset) {
			gui.reset();
		} else if (gui.running) {
			gui.drawrem-=gui.drawspeed;
			while (gui.drawrem<1.0) {
				gui.drawrem+=1.0;
				gui.life.advance();
				gui.gen+=1;
				gui.redraw=1;
			}
		}
		gui.render();
		if (gui.menu!==0) {
			// Update the start button if we're running or stopping.
			if (gui.runprev!==gui.running) {
				gui.runprev=gui.running;
				gui.runbut.innerHTML=gui.running?"&#11036; stop":"&#9654; start";
			}
			var drop=gui.dropmenu;
			var dropval=drop.options[drop.selectedIndex].value;
			var style=gui.drawctx.canvas.style;
			// Change the mouse cursor depending on the mode we're in.
			if (gui.dropval!==dropval) {
				gui.dropval=dropval;
				if (dropval==="move") {style.cursor="move";}
				else if (dropval==="zoom in") {style.cursor="zoom-in";}
				else if (dropval==="zoom out") {style.cursor="zoom-out";}
				else {style.cursor="default";}
			}
			var clicked=gui.mousedown&~gui.mouseclick;
			gui.mouseclick=gui.mousedown;
			var scale=gui.scale;
			var mousex=gui.mousex;
			var mousey=gui.mousey;
			if (dropval==="toggle" || dropval==="cell on" || dropval==="cell off") {
				// Set the state of the cell the mouse is currently over.
				if (gui.mouseover!==0) {
					var grid=gui.screentogrid([mousex,mousey]);
					var cell=gui.gridtoscreen(grid);
					var state=gui.life.getcell(grid);
					var next=(dropval==="cell on" || (dropval==="toggle" && state===0))?1:0;
					var r=Math.floor(64+state*127).toString(16).slice(-2);
					var g=Math.floor(96+state*127).toString(16).slice(-2);
					var ctx=gui.drawctx;
					ctx.fillStyle="#"+r+r+g;
					ctx.fillRect(cell[0],cell[1],gui.rectpix,gui.rectpix);
					gui.redraw=1;
				}
				if (gui.mousedown===0 || gui.mouseover===0) {
					gui.mousegrid=null;
				} else if (arrequal(gui.mousegrid,grid)===false) {
					gui.mousegrid=grid;
					gui.life.setcell(grid,next);
				}
			} else if (dropval==="move") {
				// Grab an drag the viewing area.
				var grabbing=gui.mousedown&gui.mouseover;
				if (gui.mousegrab!==grabbing) {
					gui.mousegrab=grabbing;
				} else if (gui.mousegrab!==0) {
					gui.viewx+=(mousex-gui.mousegrabx)/scale;
					gui.viewy+=(mousey-gui.mousegraby)/scale;
					gui.calcview();
				}
				gui.mousegrabx=mousex;
				gui.mousegraby=mousey;
			} else if (clicked!==0) {
				// Zoom in/out and re-center the view around the mouse position.
				// Stop zooming out when scale=1.
				var mul=dropval==="zoom in"?0.8:1.25;
				if (scale===1 && mul>1) {mul=1;}
				gui.vieww*=mul;
				// Stop zooming in at 1 cell.
				if (gui.vieww<1) {gui.vieww=1;}
				gui.viewh=gui.vieww*(gui.inith/gui.initw);
				var mx=mousex/scale-gui.viewx;
				var my=mousey/scale-gui.viewy;
				gui.viewx=-mx+gui.vieww*0.5;
				gui.viewy=-my+gui.viewh*0.5;
				gui.calcview();
			}
		}
	};
	if (gui.menu!==0) {
		// Set up the control menu.
		// start, stop, step, reset, clear, zoom -+, mouse
		// mouse: drag, toggle, cell on, cell off
		var menubar=document.createElement("div");
		menubar.className="menu";
		gui.menubar=menubar;
		parent.appendChild(menubar);
		var runbut=document.createElement("button");
		runbut.innerHTML="&#11036; stop";
		runbut.onclick=function(){gui.running^=1;};
		menubar.appendChild(runbut);
		gui.runbut=runbut;
		gui.runprev=-1;
		var obj=document.createElement("button");
		obj.innerHTML="step";
		obj.onclick=function(){gui.running=0;gui.redraw=1;gui.life.advance();};
		menubar.appendChild(obj);
		obj=document.createElement("button");
		obj.innerHTML="reset";
		obj.onclick=gui.reset;
		menubar.appendChild(obj);
		obj=document.createElement("button");
		obj.innerHTML="&#10006; clear";
		obj.onclick=function(){gui.running=0;gui.redraw=1;gui.life.clear();};
		menubar.appendChild(obj);
		obj=document.createElement("p");
		obj.innerHTML="mouse: ";
		menubar.appendChild(obj);
		var drop=document.createElement("select");
		var arr=["toggle","cell on","cell off","move","zoom in","zoom out"];
		for (var i=0;i<6;i++) {
			var opt=document.createElement("option");
			opt.value=opt.text=arr[i];
			drop.appendChild(opt);
		}
		gui.dropmenu=drop;
		gui.dropval="";
		menubar.appendChild(drop);
		// Set up mouse listeners.
		gui.mousex=0;
		gui.mousey=0;
		gui.mouseover=0;
		gui.mousedown=0;
		gui.mouseclick=0;
		gui.mousegrab=0;
		gui.mousegrabx=0;
		gui.mousegraby=0;
		gui.mousegrid=null;
		canvas.onmouseover=function(){gui.mouseover=1;};
		canvas.onmouseout=function(){gui.mouseover=0;};
		canvas.onmousedown=function(){gui.mousedown=1;};
		canvas.onmouseup=function(){gui.mousedown=0;};
		canvas.onmousemove=function(evt) {
			gui.mousex=evt.pageX-canvas.offsetLeft-canvas.clientLeft;
			gui.mousey=evt.pageY-canvas.offsetTop-canvas.clientTop;
		};
	}
	gui.reset();
	gui.render();
	setInterval(gui.update,1000.0/30.0);
	return gui;
}

function gol_onload(index,w,h,args) {
	var elem=document.getElementsByClassName("gameoflife")[index];
	elem.innerHTML="";
	return gol_gui(elem,w,h,args);
}
