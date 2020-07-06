#Logging
"""
def tetlog(s):
	try:
		tetlog.cnt+=1
	except AttributeError:
		tetlog.cnt=0
		tetlog.disp=["None"]*40
	tetlog.disp[tetlog.cnt%40]=str(tetlog.cnt)+": "+str(s)
	tetlogdisp()

def tetlogdisp():
	#return
	for i in range(40):
		tetlog.con.settext(0,i,tetlog.disp[i])

tetlog.con=con
tetlog("start")
"""

"""
class Profiler(object):
	class Timer(object):
		def __init__(self):
			self.time=0.0
			self.count=0
			self.mark=0
		def start(self):
			self.mark=time.time()
		def stop(self):
			self.time+=time.time()-self.mark
			self.count+=1

	def __init__(self):
		self.timearr=[Profiler.Timer() for i in range(100)]
		self.loops=0
	def loop(self):
		self.loops+=1
		return self.loops
	def stats(self):
		print("Profiling stats")
		timearr=self.timearr
		for i in range(len(timearr)):
			timer=timearr[i]
			if timer.count:
				print("{0:02d}: {1:>12f}".format(i,timer.time/timer.count))
	def reset(self):
		for timer in self.timearr:
			timer.time=0.0
			timer.count=0
		self.loops=0
	def __getitem__(self,i):
		return self.timearr[i]

prof=Profiler()
"""

import sys,time,random
randrange=random.randrange
#import itertools
if sys.version_info[0]<=2:
	range=xrange
	input=raw_input
sys.path.insert(0,"../")
from Tetris import Tetris

def tetrisprint(tet):
	#Print the tetris grid so it may be reconstructed later.
	tdict=tet.__dict__
	fields=("width","height","drop","dropx","dropy",
	        "spawnframes","lockframes","clearframes",
	        "gravity","ailagframes")
	for name in fields:
		print("tet.{0}={1}".format(name,tdict[name]))
	print("tet.grid=[")
	for y in range(tet.height):
		last="],"[:1+(y+1<tet.height)]
		print("\t["+",".join(map(str,tet.grid[y]))+last)
	print("]\ntet.linecount=["+",".join(map(str,tet.linecount))+"]")

def piecelayouttest():
	print("testing piece layout")
	def printerr(msg):
		print(msg)
		print("{0} {1}".format(width,spawn))
		exit()
	height=20
	for width in range(21):
		for spawn in range(7):
			#Force the grid to spawn our test piece.
			tet=Tetris(width,height)
			tet.next=spawn*4
			tet.advance()
			if tet.drop//4!=spawn:
				printerr("piece changed")
			#Spawning should only fail for small grids.
			if width<=0 or (width==1 and spawn!=Tetris.I):
				if (tet.state&Tetris.GAMEOVER)==0:
					printerr("should be gameover")
				continue
			if (tet.state&Tetris.GAMEOVER)!=0:
				printerr("should not be gameover")
			#The drop coordinates should always be in bounds.
			dropx,dropy=tet.dropx,tet.dropy
			if dropx<0 or dropx>=width or dropy<0 or dropy>=height:
				printerr("drop oob: {0}, {1}".format(dropx,dropy))
			#Get the piece bounding box.
			piece=tet.PIECE[tet.drop]
			minx,maxx=width,0
			miny,maxy=tet.height,0
			for i in range(0,8,2):
				x=piece[i+0]+dropx
				y=piece[i+1]+dropy
				minx=min(minx,x)
				maxx=max(maxx,x)
				miny=min(miny,y)
				maxy=max(maxy,y)
			#Make sure the entire piece is in bounds.
			if minx<0 or maxx>=width or miny<0 or maxy>=height:
				printerr("block oob")
			#The piece should be centered and flush with the ceiling.
			if maxy!=height-1:
				printerr("not aligned top")
			left=minx
			right=width-1-maxx
			if left!=right and left+1!=right:
				printerr("not centered: {0}, {1}".format(left,right))
	print("passed")

def heaptest():
	print("testing tetris AI heap")
	class Node(object):
		def __init__(self,val):
			self.sort=val
	trials=1000
	objtrials=1000
	objrate=16
	for trial in range(trials):
		#Set up the heap.
		tet=Tetris()
		tet.aimakecopy()
		tet=tet.aicopy
		heappush=tet.aiheappush
		heappop=tet.aiheappop
		arr=[]
		for objtrial in range(objtrials):
			count=len(arr)
			if tet.aiheap!=count:
				print("bad counts")
				exit()
			#Test the top values.
			if count:
				i=0
				for j in range(1,count):
					if arr[i]>arr[j]: i=j
				val=arr[i]
				top=tet.aitmp[0]
				if top.sort!=val:
					print("top!=val: {0}, {1}".format(top.sort,val))
					exit()
			#Add or remove a value.
			if randrange(10)==0: objrate=randrange(33)
			if randrange(32)<objrate:
				val=randrange(100)
				arr.append(val)
				heappush(Node(val))
			elif count:
				del arr[i]
				if top is not heappop():
					print("pop!=top")
					exit()
	print("passed")

def stresstest():
	print("tetris stress test")
	#Random frames.
	#advance by a non-integer number of frames
	#check for infinite loops
	#make sure suggestmoves leads to suggestposition
	#make sure no fields are added that aren't in __init__.
	trials=100
	samples=1000
	def clear(): sys.stdout.write("\r"+" "*25+"\r")
	def checknames(obj,valid):
		for name in dir(obj):
			if name[:2]!="__" and not name in valid:
				print("unrecognized field: "+name)
				exit()
	def checkfields(tet):
		if tet is None: return
		tetfields=(
			"AICell","AILink","CLEARED","CLEARING","DOWN","DROPPING","EASY",
			"GAMEOVER","HARD","HARDDROP","I","J","L","LEFT","MEDIUM","MOVES",
			"MOVING","NOMOVE","O","PIECE","RIGHT","ROTL","ROTR","S","SCANNED",
			"SOFTDROP","SPAWNED","SPAWNING","T","Z","advance","aicopy","aifitness",
			"aigrid","aiheap","ailagframes","ailink","aimakecopy","aimapmoves",
			"aitmp","aiheap","aiheappush","aiheappop","bagcnt","bagsum","canmove",
			"cleared","clearframes","drop","droprem","dropx","dropy","frameunit",
			"gennext","gravity","gravityden","grid","height","level",
			"levelconstants","linecount","lockframes","move","next","randinc",
			"randseed","reset","spawnframes","state","stateframe","suggestmove",
			"suggestposition","width"
		)
		cellfields=(
			"drop","dropx","dropy","next","nextmove","state","stateframe","droprem",
			"link","sort"
		)
		linkfields=(
			"link","prev","move"
		)
		checknames(tet,tetfields)
		if tet.aigrid:
			cell=tet.aigrid[randrange(len(tet.aigrid))]
			if cell: checknames(cell,cellfields)
		if tet.ailink:
			link=tet.ailink[randrange(len(tet.ailink))]
			if link: checknames(link,linkfields)
	for trial in range(trials):
		sys.stdout.write(str(trial))
		sys.stdout.flush()
		width,height=randrange(20),randrange(20)
		dif=(Tetris.EASY,Tetris.MEDIUM,Tetris.HARD)[randrange(3)]
		tet=Tetris(width,height,dif)
		def randomconstants():
			tet.spawnframes=randrange(20)
			tet.lockframes=randrange(20)
			tet.clearframes=randrange(20)
			tet.gravity=randrange(20)
			tet.ailagframes=randrange(20)
		if randrange(2):
			tet.levelconstants=randomconstants
		moves,maxmoves=0,100
		maxinterference=randrange(8)
		maxaimoves=randrange(5)+1
		advance=random.random()*5+1
		lastbag=-1
		for sample in range(samples):
			tet.advance(advance)
			if (tet.state&Tetris.GAMEOVER)!=0: break
			if lastbag!=tet.bagsum:
				lastbag=tet.bagsum
				moves=0
				interference=maxinterference
			while interference and randrange(2):
				interference-=1
				tet.move(randrange(4))
			if tet.ailagframes==0 and randrange(3)==0:
				drop,dropx,dropy=tet.suggestposition()
				while (tet.state&Tetris.MOVING)!=0:
					tet.move(tet.suggestmove())
				if drop!=tet.drop or dropx!=tet.dropx or dropy!=tet.dropy:
					print("couldn't follow path")
					tetrisprint(tet)
					exit()
			else:
				for i in range(maxaimoves):
					if i and randrange(2): break
					tet.move(tet.suggestmove())
			moves+=1
			if moves>=maxmoves:
				print("loop detected")
				tetrisprint(tet)
				exit()
		checkfields(tet)
		checkfields(tet.aicopy)
		clear()
	print("passed")

def linetest():
	#Count how many lines the AI can clear for grids of size (10,20).
	#Height is measured after placing a piece and clearing lines.
	trials=1
	def stats():
		print("Lines {0}, Time {1:>6f}".format(tet.cleared,time.time()-tstart))
		for i in range(21):
			print("{0:2d}: {1}".format(i,heightcount[i]))
		print("  = {0}".format(sum(heightcount)))
	heightcount=[0]*21
	for trial in range(trials):
		tet=Tetris(10,20,Tetris.HARD)
		tet.ailagframes=0
		tstart,tmark=time.time(),0
		mask=Tetris.MOVING|Tetris.GAMEOVER
		state=Tetris.CLEARING|Tetris.HARD
		height=0
		linecount=tet.linecount
		while (tet.state&Tetris.GAMEOVER)==0:
			#Advance the state and record the current height.
			while (tet.state&mask)==0:
				tet.advance()
			while height>0  and linecount[height-1]==0: height-=1
			while height<20 and linecount[height]!=0  : height+=1
			heightcount[height]+=1
			#Advance the AI.
			if (tet.state&Tetris.GAMEOVER)==0:
				tet.drop,tet.dropx,tet.dropy=tet.suggestposition()
				tet.state=state
			#Print progress.
			if tet.cleared>=tmark:
				tmark+=1024
				stats()
		stats()

#piecelayouttest()
#heaptest()
#stresstest()
linetest()
