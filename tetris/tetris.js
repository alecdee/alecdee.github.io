/*------------------------------------------------------------------------------


tetris.js - v1.05

Copyright 2020 Alec Dee - MIT license - SPDX: MIT
alecdee.github.io - akdee144@gmail.com


--------------------------------------------------------------------------------
TODO


*/
/* jshint bitwise: false */
/* jshint eqeqeq: true   */
/* jshint curly: true    */


//---------------------------------------------------------------------------------
// Tetris Engine
//---------------------------------------------------------------------------------

var TETRIS_EASY    =1<<0;
var TETRIS_MEDIUM  =1<<1;
var TETRIS_HARD    =1<<2;
var TETRIS_GAMEOVER=1<<3;
var TETRIS_SPAWNING=1<<4;
var TETRIS_SPAWNED =1<<5;
var TETRIS_DROPPING=1<<6;
var TETRIS_CLEARING=1<<7;
var TETRIS_SCANNED =1<<8;
var TETRIS_CLEARED =1<<9;
var TETRIS_MOVING  =1<<10;

var TETRIS_MOVES   =8;
var TETRIS_NOMOVE  =0;
var TETRIS_LEFT    =1;
var TETRIS_RIGHT   =2;
var TETRIS_DOWN    =3;
var TETRIS_ROTL    =4;
var TETRIS_ROTR    =5;
var TETRIS_SOFTDROP=6;
var TETRIS_HARDDROP=7;

// This holds the rotated forms of the various tetris pieces. Rotations are listed
// clockwise. For the I piece, the blocks are ordered to be reused for kick values.
// For all pieces, the blocks are ordered to align spawning positions.
var TETRIS_I=0;
var TETRIS_O=1;
var TETRIS_T=2;
var TETRIS_L=3;
var TETRIS_J=4;
var TETRIS_S=5;
var TETRIS_Z=6;
var TETRIS_PIECE=[
	// I
	[ 0, 0, 1, 0, 2, 0,-1, 0],
	[ 0, 0, 0, 1, 0,-1, 0,-2],
	[ 0, 0, 1, 0,-1, 0,-2, 0],
	[ 0, 0, 0, 1, 0, 2, 0,-1],
	// O
	[ 0,-1, 1, 0, 1,-1, 0, 0],
	[ 0,-1, 1, 0, 1,-1, 0, 0],
	[ 0,-1, 1, 0, 1,-1, 0, 0],
	[ 0,-1, 1, 0, 1,-1, 0, 0],
	// T
	[ 0,-1, 0, 0, 1, 0,-1, 0],
	[ 0,-1, 0, 1,-1, 0, 0, 0],
	[-1, 0, 0, 0, 0, 1, 1, 0],
	[ 0, 1, 0, 0, 1, 0, 0,-1],
	// L
	[-1,-1, 0, 0, 1, 0,-1, 0],
	[ 0, 0, 0, 1, 0,-1,-1, 1],
	[-1, 0, 0, 0, 1, 0, 1, 1],
	[ 0, 1, 0, 0, 0,-1, 1,-1],
	// J
	[ 0, 0, 1, 0, 1,-1,-1, 0],
	[ 0, 0, 0, 1, 0,-1,-1,-1],
	[-1, 1,-1, 0, 0, 0, 1, 0],
	[ 0, 0, 1, 1, 0,-1, 0, 1],
	// S
	[ 0,-1, 0, 0, 1, 0,-1,-1],
	[ 0, 0,-1, 1, 0,-1,-1, 0],
	[ 0,-1, 0, 0, 1, 0,-1,-1],
	[ 0, 0,-1, 1, 0,-1,-1, 0],
	// Z
	[ 0,-1, 0, 0, 1,-1,-1, 0],
	[-1, 0, 0, 1,-1,-1, 0, 0],
	[ 0,-1, 0, 0, 1,-1,-1, 0],
	[-1, 0, 0, 1,-1,-1, 0, 0]
];

function tetris_create(width,height,flags) {
	if (flags===undefined) {flags=TETRIS_HARD;}
	var self=new Object();
	// state
	self.state=flags&(TETRIS_EASY|TETRIS_MEDIUM|TETRIS_HARD);
	self.stateframe=0;
	self.frameunit=60;
	self.spawnframes=0;
	self.lockframes=0;
	self.clearframes=0;
	self.gravityden=256;
	self.gravity=0;
	self.level=0;
	self.cleared=0;
	// playing grid
	self.width=width;
	self.height=height;
	self.grid=new Array(height);
	for (var i=0;i<height;i++) {self.grid[i]=new Array(width);}
	self.linecount=new Array(height);
	// piece randomizer
	self.randseed=0;
	self.randinc=0;
	self.bagsum=0;
	self.bagcnt=new Array(7);
	self.next=0;
	// current piece
	self.drop=0;
	self.dropx=0;
	self.dropy=0;
	self.droprem=0;
	// AI player. The grid holds all possible piece states for the AI.
	// ailagframes is the simulated reaction time of the AI. 0=instant.
	self.ailagframes=Math.floor(self.frameunit/4);
	self.aigrid=null;
	self.aitmp=null;
	self.aiheap=0;
	self.ailink=null;
	self.aicopy=null;
	self.reset=function() {
		// Reset to an empty grid with level=0. Set the first piece to not be S or Z.
		self.state=(self.state&(TETRIS_EASY|TETRIS_MEDIUM|TETRIS_HARD))|TETRIS_SPAWNING;
		self.stateframe=0;
		for (var y=0;y<self.height;y++) {
			var row=self.grid[y];
			for (var x=0;x<self.width;x++) {row[x]=0;}
			self.linecount[y]=0;
		}
		self.level=0;
		self.cleared=0;
		self.levelconstants();
		// Don't let S or Z be the first spawn.
		for (var i=0;i<7;i++) {self.bagcnt[i]=0;}
		self.bagsum=0;
		var next=TETRIS_S*4;
		while (next===TETRIS_S*4 || next===TETRIS_Z*4) {
			next=self.gennext();
		}
		self.next=next;
		self.drop=0;
		self.dropx=0;
		self.dropy=0;
		self.droprem=0;
	};
	self.levelconstants=function() {
		// Set the state frames and gravity based on the level and difficulty of the game.
		// As the level increases, scale the state frames to their minimum values and scale
		// the gravity to its maximum value. All numerators are over 256.
		var num=[128,128,256,480];
		if (self.state&TETRIS_MEDIUM) {num=[85,85,128,640];}
		if (self.state&TETRIS_HARD) {num=[64,64,85,960];}
		var max=999;
		var unit=self.frameunit;
		var level=self.level;
		if (level>max) {level=max;}
		var den=256*max;
		var inv=max-level;
		self.level=level;
		self.spawnframes=Math.floor((unit*(128*inv+num[0]*level))/den);
		self.lockframes=Math.floor((unit*(128*inv+num[1]*level))/den);
		self.clearframes=Math.floor((unit*(256*inv+num[2]*level))/den);
		self.gravity=Math.floor((self.gravityden*(240*inv+num[3]*level))/(den*unit));
	};
	self.gennext=function() {
		// Pick the next tetris piece from a bag of pieces. The bag has a count of how many
		// of each piece are in the bag. When a piece is picked, decrease its count.
		// bagcnt=-1=infinity.
		var bagsum=self.bagsum;
		var bagcnt=self.bagcnt;
		// If we have emptied the bag, refill it.
		if (bagsum===0) {
			for (var i=0;i<7;i++) {
				bagcnt[i]=3;
				bagsum+=bagcnt[i];
			}
		}
		var rand=Math.floor(Math.random()*bagsum);
		var next=0;
		while (bagcnt[next]<=rand) {
			rand-=bagcnt[next];
			next+=1;
		}
		// If there's a finite number of this piece, decrement its count.
		if (bagcnt[next]!==-1) {
			bagcnt[next]-=1;
			bagsum-=1;
		}
		self.bagsum=bagsum;
		// If the grid has width 1, only the I piece can possibly spawn.
		if (self.width<=1) {next=TETRIS_I;}
		// Format the piece for the piece array.
		return next*4;
	};
	self.advance=function(frames) {
		if (frames===undefined) {frames=1;}
		// Advance the state of the game by the number of frames given.
		var state=self.state;
		var stateframe=self.stateframe;
		while ((state&TETRIS_GAMEOVER)===0) {
			if ((state&TETRIS_SPAWNING)!==0) {
				// If this is the beginning of the spawn state, initialize a new piece.
				if ((state&TETRIS_SPAWNED)===0) {
					self.drop=self.next;
					self.next=self.gennext();
					self.droprem=0;
					// If the grid is too small, the piece may need to be rotated and shifted to be
					// spawnable.
					var piece=TETRIS_PIECE[self.drop];
					self.drop+=self.width<=piece[4]-piece[6];
					piece=TETRIS_PIECE[self.drop];
					self.dropx=Math.floor((self.width-1-piece[4]-piece[6])/2);
					self.dropy=self.height-1-piece[3];
					// Since we have a piece to control, allow movement. We need to set the tetris
					// state's actual state so move() knows we can move.
					state|=TETRIS_SPAWNED|TETRIS_MOVING;
					self.state=state;
					// Use a null move to test if any of the cells we are spawning on are already
					// filled. If any are filled, its game over.
					if (self.canmove(TETRIS_NOMOVE)===0) {
						state^=TETRIS_GAMEOVER^TETRIS_MOVING;
						break;
					}
				}
				if (stateframe>=self.spawnframes) {
					// We have finished spawning, so move on to dropping.
					state^=TETRIS_SPAWNING^TETRIS_SPAWNED^TETRIS_DROPPING;
					stateframe=0;
				} else if (frames>=1) {
					// Otherwise, advance by 1 frame.
					frames-=1;
					stateframe+=1;
				} else {
					break;
				}
			} else if ((state&TETRIS_DROPPING)!==0) {
				// Check if we can lock immediately. Specifically, if lockframes=0.
				var shift=self.canmove(TETRIS_DOWN);
				if (shift===0 && stateframe>=self.lockframes) {
					state^=TETRIS_DROPPING^TETRIS_CLEARING^TETRIS_MOVING;
					stateframe=0;
					continue;
				}
				// To actually fall, we need at least 1 frame.
				if (frames<1) {break;}
				frames-=1;
				stateframe+=1;
				// If the piece can fall.
				if (shift!==0) {
					// Add gravity to the fractional remainder we are falling by. If we have fallen,
					// move the piece down. Also, reset stateframe to prevent the piece from locking.
					self.droprem+=self.gravity;
					var fall=Math.floor(self.droprem/self.gravityden);
					self.droprem%=self.gravityden;
					while (fall>=1 && self.move(TETRIS_DOWN)!==0) {fall-=1;}
					stateframe=0;
				}
				// If we cannot fall, the fractional remainder we are falling by should be 0.
				self.droprem=self.canmove(TETRIS_DOWN)!==0?self.droprem:0;
			} else if ((state&TETRIS_CLEARING)!==0) {
				// Set the piece and check for cleared lines. If any lines were cleared, set the
				// cleared flag.
				var width=self.width;
				var grid=self.grid;
				var linecount=self.linecount;
				if ((state&TETRIS_SCANNED)===0) {
					state|=TETRIS_SCANNED;
					var piece=TETRIS_PIECE[self.drop];
					var color=Math.floor(self.drop/4)+1;
					var dropx=self.dropx;
					var dropy=self.dropy;
					for (var i=0;i<8;i+=2) {
						// Set the blocks of the piece.
						var y=piece[i+1]+dropy;
						var line=grid[y];
						line[piece[i]+dropx]=color;
						linecount[y]+=1;
						// If we have cleared a line, clear it, but don't shift the lines above it yet.
						if (linecount[y]===width) {
							state|=TETRIS_CLEARED;
							for (var x=0;x<width;x++) {line[x]=0;}
						}
					}
				}
				if ((state&TETRIS_CLEARED)===0 || stateframe>=self.clearframes) {
					// If we are done pausing for the cleared lines, move to spawning.
					state^=TETRIS_CLEARING^TETRIS_SCANNED^TETRIS_SPAWNING;
					stateframe=0;
					// If we have cleared lines, shift all non-empty lines down. Cleared lines are
					// marked by linecount=width.
					var cleared=0;
					if ((state&TETRIS_CLEARED)!==0) {
						state^=TETRIS_CLEARED;
						height=self.height;
						for (var y=0;y<height;y++) {
							var count=linecount[y];
							if (count!==width) {
								var dst=y-cleared;
								var line=grid[y];
								grid[y]=grid[dst];
								grid[dst]=line;
								linecount[y]=linecount[dst];
								linecount[dst]=count;
							} else {
								linecount[y]=0;
								cleared+=1;
							}
						}
					}
					// Advance the level by {0,1,2,4,6} for each line cleared, and +1 for the piece
					// that's about to spawn. Then recalculate level values.
					self.cleared+=cleared;
					self.level+=[1,2,3,5,7][cleared];
					self.levelconstants();
				} else if (frames>=1) {
					// We are paused for the cleared lines.
					frames-=1;
					stateframe+=1;
				} else {
					break;
				}
			} else {
				break;
			}
		}
		self.stateframe=stateframe;
		self.state=state;
	};
	//---------------------------------------------------------------------------------
	// Movement
	//---------------------------------------------------------------------------------
	self.canmove=function(move) {
		// Test if we can move the piece by moving the piece and discarding any changes.
		return self.move(move,true);
	};
	self.move=function(move,testing) {
		if (testing===undefined) {testing=false;}
		// Unified move command. Returns 1 if the move was successful, otherwise returns 0.
		// If testing=true, then only test if the move is possible.
		var state=self.state;
		if ((state&TETRIS_MOVING)===0) {
			return 0;
		}
		var overlap=function() {
			for (var i=0;i<8;i+=2) {
				var x=piece[i+0]+dropx;
				var y=piece[i+1]+dropy;
				if (x<0 || x>=width || y<0 || y>=height || grid[y][x]!==0) {
					return 1;
				}
			}
			return 0;
		};
		var width=self.width;
		var height=self.height;
		var grid=self.grid;
		var drop=self.drop;
		var dropx=self.dropx;
		var dropy=self.dropy;
		var piece=TETRIS_PIECE[drop];
		if (move<=TETRIS_DOWN) {
			// Test if the piece can shift in a specific direction.
			dropx+=[0,-1,1,0][move];
			dropy+=[0,0,0,-1][move];
			if (overlap()!==0) {return 0;}
		} else if (move<=TETRIS_ROTR) {
			// Rotate the piece.
			var dir=(move===TETRIS_ROTR)*2-1;
			drop=(drop&0x1c)|((drop+dir)&0x3);
			piece=TETRIS_PIECE[drop];
			// If we are kicking the I piece, pull the kick values from the block coordinates.
			var kick=[0,0,-1,0,1,0,0,-1,0,1];
			if (drop<4) {
				for (var i=0;i<8;i++) {
					kick[i+2]=-piece[i];
				}
			}
			// Try kicking. If we can kick, set the piece's orientation.
			for (var i=0;i<10;i+=2) {
				dropx=self.dropx+kick[i+0];
				dropy=self.dropy+kick[i+1];
				if (overlap()===0) {break;}
				if (i===8) {return 0;}
			}
		} else if (move<=TETRIS_HARDDROP) {
			// Drop the piece.
			dropy-=1;
			while (overlap()===0) {dropy-=1;}
			dropy+=1;
			if (move===TETRIS_SOFTDROP) {
				// If it can drop, advance to the beginning of the dropping state.
				if (dropy===self.dropy) {return 0;}
				state=(state&~(TETRIS_SPAWNING|TETRIS_SPAWNED))|TETRIS_DROPPING;
			} else {
				// Advance to the clearing state.
				state=(state&~(TETRIS_SPAWNING|TETRIS_SPAWNED|TETRIS_DROPPING|TETRIS_MOVING))|TETRIS_CLEARING;
			}
		}
		if (testing===false) {
			self.drop=drop;
			self.dropx=dropx;
			self.dropy=dropy;
			if (move===TETRIS_SOFTDROP || move===TETRIS_HARDDROP) {
				self.state=state;
				self.stateframe=0;
				self.droprem=0;
			}
		}
		return 1;
	};
	//---------------------------------------------------------------------------------
	// AI
	//---------------------------------------------------------------------------------
	// An AI player to suggest the next move given a valid board state.
	//
	// We use fitness instead of entropy to grade the grid. The next move we want may
	// not be to increase the "order" of the grid. For instance, we may want to perform
	// a 4-line clear or to build up a pattern.
	//
	// When using order-1 or higher moves, limit the initial moves as much as possible,
	// as the number of states will multiply.
	//
	// Performance at width=10 and height=20: ...
	function makecell(pos,width) {
		var cell=new Object();
		cell.drop=(pos>>1)&3;
		cell.dropx=(pos>>3)%width;
		cell.dropy=Math.floor((pos>>3)/width);
		cell.next=null;
		cell.nextmove=0;
		cell.state=0;
		cell.stateframe=0;
		cell.droprem=0;
		cell.link=null;
		cell.sort=0;
		return cell;
	}
	function makelink() {
		var link=new Object();
		link.link=null;
		link.prev=null;
		link.move=TETRIS_NOMOVE;
		return link;
	}
	// A binary heap to sort potential moves.
	self.aiheappush=function(val) {
		var heap=self.aitmp;
		var i=self.aiheap;
		self.aiheap+=1;
		// Heap up
		while (i!==0) {
			var j=(i-1)>>1;
			var next=heap[j];
			if (next.sort<val.sort) {break;}
			heap[i]=next;
			i=j;
		}
		heap[i]=val;
	};
	self.aiheappop=function() {
		self.aiheap-=1;
		var heap=self.aitmp;
		var count=self.aiheap;
		var ret=heap[0];
		var bot=heap[count];
		// Heap down.
		var i=0;
		while (true) {
			// Find the smallest child.
			var j=i*2+1;
			if (j+1<count && heap[j+1].sort<heap[j].sort) {
				j+=1;
			}
			if (j>=count || bot.sort<heap[j].sort) {
				break;
			}
			// Shift and continue the heap down.
			heap[i]=heap[j];
			i=j;
		}
		heap[i]=bot;
		return ret;
	};
	self.aimakecopy=function() {
		// Allocate the AI and determine if any changes have been made that require
		// remapping the optimal move path.
		var width=self.width;
		var aicopy=self.aicopy;
		if (aicopy===null || aicopy.width!==width || aicopy.height!==self.height) {
			aicopy=tetris_create(width,self.height);
			var aicells=width*self.height*8;
			var aigrid=new Array(aicells);
			for (var i=0;i<aicells;i++) {aigrid[i]=makecell(i,width);}
			aicopy.aigrid=aigrid;
			aicopy.aitmp=new Array(aicells);
			aicopy.aiheap=0;
			var ailinks=aicells*TETRIS_MOVES;
			var ailink=new Array(ailinks);
			for (var i=0;i<ailinks;i++) {ailink[i]=makelink();}
			aicopy.ailink=ailink;
		}
		self.aicopy=aicopy;
		// Check state value changes.
		var vallist=[
			["state",0],["stateframe",0],["frameunit",1],["spawnframes",1],["lockframes",1],
			["clearframes",1],["gravityden",1],["gravity",1],["level",0],["cleared",0],
			["width",1],["height",1],["bagsum",0],["next",1],["drop",0],["dropx",0],
			["dropy",0],["droprem",0],["ailagframes",1]
		];
		var remap=0;
		if ((aicopy.drop^self.drop)&0x1c) {remap=1;}
		var len=vallist.length;
		for (var i=0;i<len;i++) {
			var name=vallist[i][0];
			if (aicopy[name]!==self[name]) {
				aicopy[name]=self[name];
				remap|=vallist[i][1];
			}
		}
		// Check grid changes.
		var aicount=aicopy.linecount;
		var scount=self.linecount;
		var height=self.height;
		for (var y=0;y<height;y++) {
			var cnt=scount[y];
			if (aicount[y]===cnt && (cnt===0 || cnt===width)) {continue;}
			aicount[y]=cnt;
			var airow=aicopy.grid[y];
			var srow=self.grid[y];
			for (var x=0;x<width;x++) {
				if (airow[x]!==srow[x]) {
					airow[x]=srow[x];
					remap=1;
				}
			}
		}
		for (var i=0;i<7;i++) {
			aicopy.bagcnt[i]=self.bagcnt[i];
		}
		return remap;
	};
	self.aimapmoves=function(remap) {
		// Given a valid tetris state, find all possible moves. Will use a cached copy of
		// the grid unless changes are detected or remap=true.
		//
		// We differentiate every potential state of the current piece by x/y coordinates,
		// rotation, and if it is locked. Given the original state as a seed, we determine
		// the next state by shifting, rotating, and dropping the piece and letting the
		// state advance aiframes number of times. If this next state has not been arrived
		// at yet, add it to the list of potential states, marking the current state as its
		// prior state, and continue to the next state in the list. If a state is locked,
		// skip it, since we cannot move it. Continue in this way until all potential
		// states have been listed.
		//
		// Determine if we can use the current cached moves or if we need to remap them.
		if (remap===undefined) {remap=0;}
		remap|=self.aimakecopy();
		var aicopy=self.aicopy;
		var aigrid=aicopy.aigrid;
		var width=aicopy.width;
		var pos=((aicopy.dropy*width+aicopy.dropx)<<3)+((aicopy.drop&3)<<1)+((aicopy.state&TETRIS_MOVING)===0);
		var startcell=aigrid[pos];
		if (remap===0 && startcell.state!==0) {
			return startcell;
		}
		var aicells=width*aicopy.height*8;
		// Mark all of the states as unused.
		var drop=(aicopy.drop^aigrid[0].drop)&0x1c;
		for (var i=0;i<aicells;i++) {
			var cell=aigrid[i];
			cell.state=0;
			cell.next=null;
			cell.link=null;
			cell.drop^=drop;
		}
		// Add the original state to the list of potential states.
		startcell.state=aicopy.state;
		startcell.stateframe=aicopy.stateframe;
		startcell.droprem=aicopy.droprem;
		var ailink=aicopy.ailink;
		var ailinkpos=0;
		var aitmppos=0;
		var aitmplen=1;
		var aitmp=aicopy.aitmp;
		aitmp[0]=startcell;
		// Process all potential states.
		while (aitmppos<aitmplen) {
			var cell=aitmp[aitmppos];
			aitmppos+=1;
			if ((cell.state&TETRIS_MOVING)===0) {
				continue;
			}
			// Loop over all allowed moves.
			for (var move=0;move<TETRIS_MOVES;move++) {
				// Reset the tetris and piece state to the currently processing state, and shift,
				// rotate, or drop the piece.
				aicopy.state=cell.state;
				aicopy.stateframe=cell.stateframe;
				aicopy.drop=cell.drop;
				aicopy.dropx=cell.dropx;
				aicopy.dropy=cell.dropy;
				aicopy.droprem=cell.droprem;
				if (aicopy.move(move)===0) {
					continue;
				}
				// Because the AI has to wait in between movements, simulate how the main
				// loop will modify the tetris state and piece state while the AI is waiting.
				var state=aicopy.state;
				var stateframe=aicopy.stateframe;
				var droprem=aicopy.droprem;
				var frames=aicopy.ailagframes;
				while (true) {
					if ((state&TETRIS_SPAWNING)!==0) {
						if (stateframe>=aicopy.spawnframes) {
							state^=TETRIS_SPAWNING^TETRIS_SPAWNED^TETRIS_DROPPING;
							stateframe=0;
						} else if (frames>=1) {
							frames-=1;
							stateframe+=1;
						} else {
							break;
						}
					} else if ((state&TETRIS_DROPPING)!==0) {
						var shift=aicopy.canmove(TETRIS_NOMOVE);
						if (shift===0 && stateframe>=aicopy.lockframes) {
							state^=TETRIS_DROPPING^TETRIS_CLEARING^TETRIS_MOVING;
							stateframe=0;
							break;
						}
						if (frames<1) {
							break;
						}
						frames-=1;
						stateframe+=1;
						if (shift!==0) {
							droprem+=aicopy.gravity;
							var fall=Math.floor(droprem/aicopy.gravityden);
							droprem%=aicopy.gravityden;
							while (fall>=1 && aicopy.move(TETRIS_DOWN)!==0) {fall-=1;}
							stateframe=0;
						}
						droprem=aicopy.canmove(TETRIS_DOWN)!==0?droprem:0;
					} else {
						break;
					}
				}
				// Quantify the new state. If it is unused, add it as a potential state.
				pos=((aicopy.dropy*width+aicopy.dropx)<<3)+((aicopy.drop&3)<<1)+((state&TETRIS_MOVING)===0);
				var next=aigrid[pos];
				// if next is not cell or stateframe>cell.stateframe or droprem>cell.droprem:
				var link=ailink[ailinkpos];
				ailinkpos+=1;
				link.link=next.link;
				next.link=link;
				link.prev=cell;
				link.move=move;
				if (next.state===0) {
					aitmp[aitmplen]=next;
					aitmplen+=1;
					next.state=state;
					next.stateframe=stateframe;
					next.droprem=droprem;
				}
			}
		}
		// Sort all locked positions by their fitness.
		var heappush=aicopy.aiheappush;
		var heappop=aicopy.aiheappop;
		for (var i=0;i<aitmplen;i++) {
			var cell=aitmp[i];
			if ((cell.state&TETRIS_MOVING)===0) {
				aicopy.drop=cell.drop;
				aicopy.dropx=cell.dropx;
				aicopy.dropy=cell.dropy;
				cell.sort=aicopy.aifitness();
				heappush(cell);
			}
		}
		var fit=aicells;
		while (aicopy.aiheap) {
			fit-=1;
			aitmp[fit]=heappop();
		}
		// Map duplicate floating point fitness values to ordinal values. Processing all
		// positions at once prevents a particular orientation from overwriting equivalent
		// orientations.
		var height=aicopy.height;
		var maxdist=(width+height)*2;
		var sort=Infinity;
		var level=0;
		for (var f=fit;f<aicells;f++) {
			var cell=aitmp[f];
			if (sort-cell.sort>1e-6) {
				sort=cell.sort;
				level+=1;
			}
			cell.sort=(level*maxdist+0)*height-cell.dropy;
			heappush(cell);
		}
		// Process positions by their estimated sorting value.
		while (aicopy.aiheap) {
			var cell=heappop();
			sort=cell.sort+cell.dropy;
			// Process all predecessors. Add them to the heap if they haven't been added yet.
			var link=cell.link;
			while (link!==null) {
				var prev=link.prev;
				if (prev.next===null) {
					// prev.sort=(cell.ordinal*maxdist+prev.dist)*height-prev.dropy
					prev.sort=sort+height-prev.dropy;
					prev.next=cell;
					prev.nextmove=link.move;
					heappush(prev);
				}
				link=link.link;
			}
		}
		return startcell;
	};
	self.aifitness=function() {
		// Determine the fitness of the grid including the current piece. The higher the
		// fitness, the better the state. Variables are scaled so they are in units of
		// height. The variables we use are:
		//
		// sumholes: The count of all holes on the grid. A cell is a hole is it is empty
		// and a filled cell is above it. Needs to be scaled by width.
		//
		// sumheight: The sum of the column heights. Needs to be scaled by width.
		//
		// rowflip: The number of times neighboring cells flip between empty and filled
		// along a row. Needs to be scaled by width.
		//
		// colflip: The number of times neighboring cells flip between empty and filled
		// along a column. Needs to be scaled by width.
		//
		// pieceheight: The height of the top block of the most recently placed piece. Do
		// not take into account line clears. Do no scale.
		//
		// sumwell2: The sum of squared well heights. A well is an opening 1 cell wide,
		// which happens to function as a chokepoint. Needs to be scaled by width.
		var width=self.width;
		var height=self.height;
		var grid=self.grid;
		var linecount=self.linecount;
		// First lock in the piece.
		var dropx=self.dropx;
		var dropy=self.dropy;
		var piece=TETRIS_PIECE[self.drop];
		var pieceheight=0;
		for (var i=0;i<8;i+=2) {
			var y=piece[i+1]+dropy;
			grid[y][piece[i]+dropx]+=1;
			linecount[y]+=1;
			// Set the height the piece was placed at.
			pieceheight=pieceheight>y?pieceheight:y;
		}
		pieceheight+=1;
		// We can limit ourselves to only rows with filled cells, so find the highest
		// position with a filled cell.
		var cleared=0;
		var ymax=0;
		for (var y=0;y<height;y++) {
			if (linecount[y]===width) {cleared+=1;}
			else if (linecount[y]!==0) {ymax=y+1;}
		}
		// Find the stats of each column.
		// Since the left and right walls are considered filled cells, any empty lines will
		// have a row flip when the left-most and right-most cells are compared against
		// their respective walls.
		var sumholes=0;
		var sumheight=0;
		var rowflip=(height-ymax)*2;
		var colflip=0;
		var sumwell2=0;
		for (var x=0;x<width;x++) {
			var colheight=0;
			var wellheight=0;
			var covered=0;
			// When determining column flips, we compare the current row with the row above it.
			// If the grid is filled, but a line is going to be cleared, we know that the top
			// row should be 0 instead of whatever is there currently.
			var topcell=cleared===0?grid[height-1][x]!==0:0;
			for (var y=ymax-1;y>=0;y--) {
				// If the line is filled, ignore it.
				var c=0;
				if (linecount[y]!==width) {
					var line=grid[y];
					c=line[x]!==0;
					// If the cell is empty and there is a filled cell above, we have a hole.
					sumholes+=(c^1)&covered;
					// If the cell above is different, we have a column flip. Don't directly use
					// grid[y-1].
					colflip+=c^topcell;
					// If the cell to the left is different, we have a row flip. Ignore the cell when
					// x=0; it will be compared against the left wall later.
					rowflip+=c^(line[x-(x>0)]!==0);
					topcell=c;
					covered|=c;
					colheight+=covered;
					// If the cell is empty and we are already in a well, or the left and right
					// neighboring cells are filled, we are in a well.
					if (c===0 && (wellheight!==0 || ((x<=0 || line[x-1]!==0) && (x+1>=width || line[x+1]!==0)))) {
						wellheight+=1;
					}
				}
				// If we have reached the bottom row or a filled cell, the well has ended. Don't
				// directly use grid[y-1] to compare, as it may be a filled line.
				if (y<=0 || c!==0) {
					// Weight the well by the height squared. Testing with variable weights for each
					// height revealed values that converged around the square of the height.
					sumwell2+=wellheight*wellheight;
					wellheight=0;
				}
				// Compare the left-most and right-most cells with the left and right walls.
				rowflip+=(x===0 || x+1===width)?c^1:0;
			}
			// The bottom row needs to be compared against the bottom wall.
			colflip+=topcell^1;
			sumheight+=colheight;
		}
		// Remove the piece from the grid.
		for (var i=0;i<8;i+=2) {
			var y=piece[i+1]+dropy;
			grid[y][piece[i]+dropx]-=1;
			linecount[y]-=1;
		}
		// Given coefficients, determine the fitness of the grid. Normalize by the absolute
		// sum of the coefficients and the width of the grid. This will allow the fitnesses
		// of different grids to be compared. Do not scale by height.
		var w=width>1?1.0/width:1.0;
		var fitness=-0.2585706097*sumholes*w-0.0160887591*sumheight*w-0.1365051577*rowflip*w;
		fitness+=-0.4461359486*colflip*w-0.0232974547*pieceheight-0.1194020699*sumwell2*w;
		return fitness;
	};
	self.suggestmove=function() {
		// Return the optimal move to make.
		var cell=self.aimapmoves();
		return cell.nextmove;
	};
	self.suggestposition=function() {
		// Return the optimal position to place the piece.
		var cell=self.aimapmoves();
		while (cell.next!==null) {
			cell=cell.next;
		}
		return [cell.drop,cell.dropx,cell.dropy];
	};
	self.reset();
	return self;
}

//---------------------------------------------------------------------------------
// Tetris GUI
//---------------------------------------------------------------------------------

function tetris_gui(parent) {
	// Initialize the game of life GUI and simulator.
	var self=new Object();
	self.parent=parent;
	self.keybuf=[];
	self.draww=-1;
	self.drawh=-1;
	self.aispeed=5;
	self.aimode=0;
	self.aiwait=0;
	self.paused=0;
	var tet=tetris_create(10,20);
	var prev=tetris_create(10,20);
	self.tet=tet;
	self.prev=prev;
	var canvas=document.createElement("canvas");
	self.canvas=canvas;
	self.ctx=canvas.getContext("2d");
	parent.style.height="auto";
	parent.appendChild(canvas);
	self.colormap=[
		"#000000","#00c0c0","#c0c000","#900090",
		"#c0d050","#5050c0","#00c000","#c00000",
		"#c4c4c4"
	];
	self.rescale=function() {
		var draww=self.parent.offsetWidth;
		if (draww<300) {draww=300;}
		if (self.draww===draww) {return false;}
		self.draww=draww;
		var tet=self.tet;
		var ctx=self.ctx;
		var scale=draww/100.0;
		var outer=0.5*scale;
		var inner=0.5*scale;
		var pad=2.4*scale;
		var gridx=Math.floor(outer+pad);
		var gridy=Math.floor(outer+pad);
		var gridw=Math.floor(62*scale);
		var blockpad=Math.max(Math.floor(0.5*scale),1);
		var block=Math.floor((gridw-blockpad*(tet.width-1))/tet.width);
		gridw=Math.floor(tet.width*block+(tet.width-1)*blockpad);
		var gridh=Math.floor(tet.height*block+blockpad*(tet.height-1));
		var textx=Math.floor(gridx+gridw+inner+pad);
		var textw=Math.floor(draww-textx-outer-pad);
		var nexty=Math.floor(outer+pad);
		var nexth=Math.floor(22*scale);
		var statey=Math.floor(nexty+nexth+pad+inner);
		var stateh=Math.floor(20*scale);
		var conty=Math.floor(statey+stateh+pad+inner);
		var conth=Math.floor(30*scale);
		var drawh=Math.floor(Math.max(gridy+gridh,conty+conth)+outer+pad);
		gridy=Math.floor((drawh-gridh)/2);
		outer=Math.floor(outer);
		inner=Math.floor(inner);
		self.canvas.width=draww;
		self.canvas.height=drawh;
		ctx.font="bold "+(scale*4).toString()+"px Monospace";
		self.titleheight=ctx.measureText("M").width*1.8;
		ctx.font=(scale*3).toString()+"px Monospace";
		self.draww=draww;self.drawh=drawh;
		self.scale=scale;self.outer=outer;self.inner=inner;
		self.gridx=gridx;self.gridy=gridy;self.gridw=gridw;self.gridh=gridh;
		self.block=block;self.blockpad=blockpad;
		self.textx=textx;self.textw=textw;
		self.nexty=nexty;self.nexth=nexth;
		self.statey=statey;self.stateh=stateh;
		self.conty=conty;self.conth=conth;
		self.blockoutline=Math.floor(Math.max(block/9,1));
		// preview
		var pvpad=Math.max(Math.floor(0.1*(textw-4*scale)/4),1);
		var pvblock=Math.floor((textw-4*scale-pvpad*3)/4);
		pvpad+=pvblock;
		self.pvlayout=new Array(7);
		for (var i=0;i<7;i++) {
			var orig=TETRIS_PIECE[i*4];
			var piece=new Array(8);
			self.pvlayout[i]=piece;
			var cen=[-0.5,-0.5,0,0,0,0,0];
			var x=Math.floor(textx+textw*0.5+cen[i]*pvpad-pvblock*0.5);
			var y=Math.floor(nexty+2*scale+self.titleheight);
			for (var j=0;j<8;j+=2) {
				piece[j+0]=x+orig[j+0]*pvpad;
				piece[j+1]=y-orig[j+1]*pvpad;
			}
		}
		self.pvblock=pvblock;
		return true;
	};
	self.keyhit=function() {
		var ret=null;
		var buf=self.keybuf;
		if (buf.length) {
			ret=buf[0];
			self.keybuf=buf.slice(0,buf.length-1);
		}
		return ret;
	};
	self.evkeydown=function(ev) {
		self.keybuf.push(ev.keyCode);
		return (ev.keyCode!==32);
	};
	self.drawbackground=function() {
		var draww=self.draww;
		var drawh=self.drawh;
		var outer=self.outer;
		var ctx=self.ctx;
		ctx.fillStyle="#8080ee";
		ctx.fillRect(0,0,draww,drawh);
		ctx.fillStyle="#5555aa";
		ctx.fillRect(outer,outer,draww-outer*2,drawh-outer*2);
	};
	self.drawarea=function(x,y,w,h,title) {
		var scale=self.scale;
		var inner=self.inner;
		var ctx=self.ctx;
		ctx.font="bold "+(scale*4).toString()+"px Monospace";
		ctx.fillStyle="#8080ee";
		ctx.fillRect(x-inner,y-inner,w+inner*2,h+inner*2);
		ctx.fillStyle="#000000";
		ctx.fillRect(x,y,w,h);
		ctx.fillStyle="#ffffff";
		var tw=ctx.measureText(title).width;
		var th=ctx.measureText("M").width;
		x+=1*scale+(w-2*scale-tw)/2.0;
		y+=1*scale+th*1.2;
		ctx.fillText(title,x,y);
		ctx.font=(scale*3).toString()+"px Monospace";
	};
	self.drawtext=function(y,line,text) {
		var scale=self.scale;
		var textx=self.textx;
		var textw=self.textw;
		var ctx=self.ctx;
		var th=ctx.measureText("M").width;
		var x=textx+1*scale;
		y+=self.titleheight+2*scale+th*line*1.8;
		ctx.fillStyle="#000000";
		ctx.fillRect(textx,y-th*0.2,textw,th*1.8);
		ctx.fillStyle="#ffffff";
		ctx.fillText(text,x,y+th*1.2);
	};
	self.drawpiece=function(drop,x,y,col) {
		if (col===undefined) {col=Math.floor(drop/4)+1;}
		col+=16;
		var piece=TETRIS_PIECE[drop];
		var grid=self.prev.grid;
		for (var i=0;i<8;i+=2) {
			grid[y+piece[i+1]][x+piece[i+0]]=col;
		}
	};
	self.drawpreview=function(drop,col) {
		if (col===undefined) {col=Math.floor(drop/4)+1;}
		var piece=self.pvlayout[drop/4];
		var block=self.pvblock;
		var ctx=self.ctx;
		ctx.fillStyle=self.colormap[col];
		for (var i=0;i<8;i+=2) {
			ctx.fillRect(piece[i+0],piece[i+1],block,block);
		}
	};
	self.drawgrid=function(redraw) {
		var tet=self.tet;
		var width=tet.width;
		var height=tet.height;
		var pgrid=self.prev.grid;
		var tgrid=tet.grid;
		var block=self.block;
		var blockpad=self.blockpad+block;
		var by=self.gridy;
		var ctx=self.ctx;
		var out=self.blockoutline;
		var colormap=self.colormap;
		var col=-1;
		for (var y=height-1;y>=0;y--) {
			var prow=pgrid[y];
			var trow=tgrid[y];
			var bx=self.gridx;
			for (var x=0;x<width;x++) {
				var pcol=prow[x];
				var tcol=trow[x];
				if (pcol>=16) {tcol=pcol-16;}
				if (pcol!==tcol || redraw) {
					prow[x]=tcol;
					if (col!==tcol) {
						col=tcol;
						ctx.fillStyle=colormap[col];
					}
					ctx.fillRect(bx,by,block,block);
					if (col===8) {
						col=0;
						ctx.fillStyle=colormap[col];
						ctx.fillRect(bx+out,by+out,block-out*2,block-out*2);
					}
				}
				bx+=blockpad;
			}
			by+=blockpad;
		}
	};
	self.update=function() {
		var tet=self.tet;
		var prev=self.prev;
		var aimode=self.aimode;
		var aiwait=self.aiwait;
		var paused=self.paused;
		// If the AI is playing and loses, reset.
		if (aimode===0 && (tet.state&TETRIS_GAMEOVER)!==0) {
			// tet.reset();
		}
		// Process user inputs.
		while (true) {
			var move=TETRIS_NOMOVE;
			var key=self.keyhit();
			if      (key===65) {move=TETRIS_LEFT;}
			else if (key===68) {move=TETRIS_RIGHT;}
			else if (key===83) {move=TETRIS_DOWN;}
			else if (key===32) {move=TETRIS_HARDDROP;}
			// rotation
			else if (key===74) {move=TETRIS_ROTL;}
			else if (key===75) {move=TETRIS_ROTR;}
			// state modifying keys
			else if (key===73) {aimode=(aimode+1)%3;}
			else if (key===82) {tet.reset();}
			else if (key===80) {paused^=1;}
			else {break;}
			if (aimode!==0 && paused===0) {
				tet.move(move);
			}
		}
		if (aimode===0 && paused===0) {
			aiwait+=1;
			if (aiwait>=self.aispeed) {
				aiwait=0;
				tet.move(tet.suggestmove());
			}
		}
		self.aiwait=aiwait;
		// Advance the tetris state.
		if (paused===0) {
			tet.advance();
		}
		// See if we need to redraw the HUD.
		var redraw=self.rescale();
		if (redraw) {
			self.drawbackground();
			var textx=self.textx;
			var textw=self.textw;
			var conty=self.conty;
			self.drawarea(self.gridx,self.gridy,self.gridw,self.gridh,"");
			self.drawarea(textx,self.nexty,textw,self.nexth,"NEXT");
			self.drawarea(textx,self.statey,textw,self.stateh,"STATE");
			self.drawarea(textx,conty,textw,self.conth,"CONTROLS");
			self.drawtext(conty,0,"    AI: I");
			self.drawtext(conty,1,"  move: A/S/D");
			self.drawtext(conty,2,"rotate: J/K");
			self.drawtext(conty,3,"  drop: SPACE");
			self.drawtext(conty,4," pause: P");
			self.drawtext(conty,5," reset: R");
			self.drawtext(conty,6,"  exit: ESCAPE");
		}
		// Draw the state variables.
		var statey=self.statey;
		var flag=(prev.state^tet.state)&TETRIS_GAMEOVER;
		if (redraw || self.paused!==paused || flag) {
			self.paused=paused;
			prev.state^=flag;
			var msg="running";
			if (paused) {msg="paused";}
			else if (prev.state&TETRIS_GAMEOVER) {msg="gameover";}
			self.drawtext(statey,0," state: "+msg);
		}
		if (redraw || self.aimode!==aimode) {
			self.aimode=aimode;
			self.drawtext(statey,1,"    AI: "+["takeover","guide","none"][aimode]);
		}
		if (redraw || prev.level!==tet.level) {
			prev.level=tet.level;
			self.drawtext(statey,2," level: "+prev.level.toString());
		}
		if (redraw || prev.cleared!==tet.cleared) {
			prev.cleared=tet.cleared;
			self.drawtext(statey,3," lines: "+prev.cleared.toString());
		}
		// Draw the preview piece.
		if (redraw || prev.next!==tet.next) {
			self.drawpreview(prev.next,0);
			prev.next=tet.next;
			self.drawpreview(prev.next);
		}
		// Draw the AI's suggested position.
		if (aimode===1 && (tet.state&TETRIS_MOVING)!==0) {
			var drop=tet.suggestposition();
			self.drawpiece(drop[0],drop[1],drop[2],8);
		}
		// Draw the falling piece.
		if ((tet.state&TETRIS_MOVING)!==0) {
			self.drawpiece(tet.drop,tet.dropx,tet.dropy);
		}
		self.drawgrid(redraw);
	};
	document.onkeydown=self.evkeydown;
	setInterval(self.update,1000.0/60.0);
	return self;
}

function tetris_onload(index) {
	var elem=document.getElementsByClassName("tetris")[index];
	elem.innerHTML="";
	return tetris_gui(elem);
}
