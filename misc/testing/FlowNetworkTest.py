"""
FlowNetworkTest.py - v1.01

Copyright (C) 2020 by Alec Dee - alecdee.github.io - akdee144@gmail.com

Permission is hereby granted, free of charge, to any person obtaining a copy of
this software and associated documentation files (the "Software"), to deal in
the Software without restriction, including without limitation the rights to
use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies
of the Software, and to permit persons to whom the Software is furnished to do
so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS
FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR
COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER
IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN
CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
"""

from time import time
import sys

"""
Dinic BFS
def dfs(self,src,flow):
	if self.sink is src:
		return flow
	while src.work:
		e=src.work
		dst=e.dst
		if e.res>0 and src.level+1==dst.level:
			df=self.dfs(dst,min(flow,e.res))
			if df>0:
				e.res-=df
				e.flow=e.cap-e.res
				return df
		src.work=e.next
	return 0
"""

class Twister(object):
	def __init__(self):
		self.pos=624
		self.state=list(range(624))

	def rand(self,n):
		state=self.state
		pos=self.pos
		if pos>=624:
			pos=0
			for i in range(624):
				y=(state[i]&0x80000000)|(state[(i+1)%624]&0x7fffffff)
				state[i]=state[(i+397)%624]^(y>>1)^(0x9908b0df&-(y&1))
		ret=state[pos]
		self.pos=pos+1
		ret^=ret>>11
		ret^=(ret<<7)&0x9d2c5680
		ret^=(ret<<15)&0xefc60000
		ret^=ret>>18
		return ret%n

def FlowTestSmall(network):
	#Given the following flow network with source S, sink T, and flow rates 0-5, find
	#the maximum flow from S to T. Note that there is no vertex connecting edges 0
	#and 5.
	#
	#                 1
	#                 *
	#               .'|'.
	#             .'  |  '.
	#         1 .'    |    '. 2
	#         .'      |5     '.
	#       .'        |        '.
	#     .'      0   |          '.
	# S0 *------------+------------* T2
	#     '.          |          .'
	#       '.        |        .'
	#         '.      |      .'
	#         4 '.    |    .' 3
	#             '.  |  .'
	#               '.|.'
	#                 *
	#                 3
	#
	#f12=min(f1,f2)
	#f43=min(f4,f3)
	#p1=f1-f12
	#p4=f4-f43
	#r2=f2-f12
	#r3=f3-f43
	#f153=min(f5,p1,r3)
	#f452=min(f5,p4,r2)
	#f=f0+f12+f43+f153+f452
	#
	#Since p1=0 and/or r2=0 and p4=0 and/or r3=0.
	#p=f1-f12+f4-f43
	#r=f2-f12+f3-f43
	#p5=min(f5,p,r)
	#f=f0+f12+f43+p5
	print("small flow test for "+network.__name__)
	t0=time()
	rnd=Twister()
	trials=10000
	maxverts=4
	maxedges=maxverts*(maxverts-1)/2
	maxcap=20
	for trial in range(trials):
		usevert=[1,rnd.rand(2),1,rnd.rand(2)]
		verts=0
		usemap=[0]*4
		for i in range(4):
			usemap[i]=verts
			verts+=usevert[i]
		useedge=[0]*6
		edgevert=((0,2),(0,1),(1,2),(3,2),(0,3),(1,3))
		edgecap=[0]*6
		for i in range(6):
			useedge[i]=rnd.rand(2) and usevert[edgevert[i][0]] and usevert[edgevert[i][1]]
			edgecap[i]=(0,rnd.rand(maxcap+1))[useedge[i]]
		#Manually calculate the maximum flow.
		f12=min(edgecap[1],edgecap[2])
		f43=min(edgecap[4],edgecap[3])
		p=edgecap[1]-f12+edgecap[4]-f43
		r=edgecap[2]-f12+edgecap[3]-f43
		p5=min(edgecap[5],p)
		p5=min(p5,r)
		f=edgecap[0]+f12+f43+p5
		#Create the flow network.
		fn=network(verts,10)
		fn.setsource(usemap[0])
		fn.setsink(usemap[2])
		for i in range(6):
			if useedge[i]:
				fn.addedge(usemap[edgevert[i][0]],usemap[edgevert[i][1]],edgecap[i])
				if rnd.rand(2) or i==5:
					fn.addedge(usemap[edgevert[i][1]],usemap[edgevert[i][0]],edgecap[i])
		max=fn.maxflow()
		if max!=f:
			print("incorrect max flow: ",max,f)
			exit()
	print(time()-t0)
	print("passed")

def FlowTestLarge(network):
	#Ford Fulkerson: 47.625132
	#Dinic         : 12.119000
	flow=(
		694629403, 159473617, 698968620, 135057049, 710345035, 1280017603, 992840084, 1349253074,
		182875265, 219643578, 525254913, 388379465, 251956994, 15087792, 27456380, 0, 267007219,
		186921927, 552826494, 713041130, 189483935, 703464884, 224622982, 730765034, 642858281,
		1714852710, 694126102, 1436385620, 43670785, 634315035, 312076134, 602573349, 376078443,
		278757189, 475439416, 267619735, 421876786, 1286439286, 445892841, 32159181, 8528586,
		696067828, 818662567, 423612308, 408654336, 1225442420, 59055066, 1318490560, 1119429071,
		32810537, 86728191, 135584636, 1042515815, 316635960, 76264766, 199742957, 17848540,
		276891698, 199743093, 174779932, 1036748803, 130469036, 849605862, 934328122, 18194315,
		1315983074, 232959904, 1368928937, 329437939, 48619406, 728915189, 133979080, 417896108,
		601601663, 399148250, 836949929, 290528661, 373064014, 234203823, 328561875, 15799709,
		23535624, 816666636, 89418106, 349871057, 537514000, 108155397, 236364044, 1676529926,
		942042252, 205146493, 41075454, 1125209458, 1560255847, 385311746, 67135774, 948469517,
		9713307, 1479637240, 209739418, 1474687987, 106552562, 142727028, 818236571, 859364363,
		718844784, 606826634, 191216467, 141294919, 1247270531, 155450758, 660912563, 392922974,
		864003981, 348627030, 1384917796, 1093821695, 121972496, 76680470, 0, 969510456, 1068872671,
		329548144, 973656444, 1152129984, 1204975143, 35430774, 540291739, 689481467, 178064515,
		101656195, 117942151, 66284213, 265752351, 422109901, 0, 968505398, 844265389, 273790037,
		438289239, 105333374, 152394300, 15984355, 267154710, 1130592019, 99749660, 93370916,
		1116834058, 961637537, 237252140, 541719009, 766940003, 431694830, 697727633, 137928618,
		586994551, 1092996799, 1152291016, 407998640, 67983311, 871386986, 255180503, 126214478,
		685774373, 44215259, 211223199, 548899829, 225305369, 3678437, 98403066, 50733562, 97354203,
		551529909, 52641074, 192456791, 42235809, 752863877, 1103260095, 313940183, 172202490,
		1282574887, 451907724, 451009158, 245002740, 75744192, 215115697, 673872968, 584535839,
		148147792, 214379679, 5960737, 546418156, 403942461, 1540125331, 259870443, 1217919199,
		974426499, 561551517, 126114164, 1328910482
	)
	print("large flow test for "+network.__name__)
	trials=200
	maxverts=400
	maxedges=maxverts*(maxverts-1)
	maxcap=10000000
	edgeord=[0]*maxedges
	rnd=Twister()
	t0=time()
	for trial in range(trials):
		#print(trial)
		verts=rnd.rand(maxverts-1)+2
		src=rnd.rand(verts)
		snk=rnd.rand(verts)
		if snk==src:
			snk=(snk+1)%verts
		edges=verts*(verts-1)
		for i in range(edges):
			swap=rnd.rand(i+1)
			edgeord[i]=edgeord[swap]
			edgeord[swap]=i
		edges=rnd.rand(edges+1)
		fn=network(verts,edges)
		fn.setsource(src)
		fn.setsink(snk)
		for i in range(edges):
			src=edgeord[i]//verts
			dst=edgeord[i]%verts
			if src==dst:
				src=verts-1
			fn.addedge(src,dst,rnd.rand(maxcap))
		calc=fn.maxflow()
		if calc!=flow[trial]:
			print("incorrect max flow:",calc,",",flow[trial])
			exit()
	print("#"+network.__name__+": "+str(time()-t0))
	print("passed")

sys.path.insert(0,"../")
from FlowNetwork import FlowNetwork as network
#from FordFulkerson import FordFulkerson as network
FlowTestSmall(network)
FlowTestLarge(network)
