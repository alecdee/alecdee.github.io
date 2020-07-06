"""
FlowNetwork.py - v1.02

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

--------------------------------------------------------------------------------
Uses Dinic's Blocking Flow.

If there are multiple sources, create a super source and connect it to every
original source with an edge of infinite capacity. The same can be done with
sinks.

If we have an environment where each node has its maximum output capped (a
vertex capacity), then split each vertex into an in-vertex and an out-vertex.
All in edges will point to the in-vertex and all out edges will stem from the
out-vertex. Create an edge from the in-vertex to the out-vertex with the
capacity of the vertex.
"""

class FlowNetwork(object):
	class Vert(object):
		def __init__(self):
			self.queue=None
			self.edge=None
			self.table={}
			self.work=None
			self.df=0
			self.level=0

	class Edge(object):
		def __init__(self):
			self.next=None
			self.src=None
			self.dst=None
			self.cap=0
			self.flow=0
			self.back=None

		@property
		def res(self):
			return self.back.flow

		@res.setter
		def res(self,flow):
			self.back.flow=flow

	def __init__(self,verts,edges=None):
		if edges==None:
			edges=verts*verts
		else:
			edges*=2
		self.vert=[FlowNetwork.Vert() for i in range(verts)]
		self.edge=[FlowNetwork.Edge() for i in range(edges)]
		self.verts=verts
		self.edges=0
		self.source=None
		self.sink=None

	def setsource(self,i):
		self.source=self.vert[i]

	def setsink(self,i):
		self.sink=self.vert[i]

	def getedge(self,src,dst):
		return self.vert[src].table.get(dst)

	def addedge(self,src,dst,cap):
		assert(src!=dst)
		if self.edges>=len(self.edge):
			self.edge.append(FlowNetwork.Edge())
		edge=self.edge[self.edges]
		self.edges+=1
		v=self.vert[src]
		edge.src=v
		edge.dst=self.vert[dst]
		edge.cap=cap
		edge.next=v.edge
		v.edge=edge
		#If we're not a back edge, create a back edge.
		if self.edges&1:
			back=self.addedge(dst,src,cap)
			edge.back=back
			back.back=edge
			v.table[dst]=back
		return edge

	def bfs(self):
		for v in self.vert:
			v.work=v.edge
			v.level=-1
			v.queue=None
		src=self.source
		src.level=0
		top=src
		while src:
			e=src.edge
			while e:
				dst=e.dst
				if e.res>0 and dst.level==-1:
					dst.level=src.level+1
					top.queue=dst
					top=dst
				e=e.next
			#Go to the next vertex. Reset the queue for use in DFS.
			next=src.queue
			src.queue=None
			src=next
		return self.sink.level!=-1

	def dfs(self):
		"""Non-recursive DFS."""
		#If we're using floating point values, we can increase numerical stability when
		#augmenting the path by taking taking res-=df;flow=cap-res;. Since df is capped
		#by res, the smallest res that limits the path will be set to res-df=0, and the
		#flow will correctly equal cap. If we instead took flow+=df;res=cap-flow; we may
		#have the case where df is small and flow is large. Thus flow+df might be rounded
		#down. If we instead took flow+=df;res-=df;, then differences in magnitude over
		#several operations may cause flow+res!=cap.
		sink=self.sink
		src=self.source
		src.df=0x7fffffff
		while src:
			if src is sink:
				#Hit the sink. Go up. Use continue here in case sink=source.
				src=src.queue
				continue
			e=src.work
			if not e:
				#No edges left. Go up.
				src.df=0
				src=src.queue
				continue
			dst=e.dst
			if dst.queue is src:
				#We have just returned up from dst.
				dst.queue=None
				if dst.df>0:
					e.res-=dst.df
					e.flow=e.cap-e.res
					src.df=dst.df
					src=src.queue
					continue
			elif e.res>0 and src.level+1==dst.level:
				#dfs down.
				dst.queue=src
				dst.df=min(src.df,e.res)#src.df if src is self.source or src.df<e.res else e.res#
				src=dst
				continue
			src.work=e.next
		return self.source.df

	def maxflow(self):
		for i in range(0,self.edges,2):
			edge=self.edge[i]
			edge.flow=0
			edge.res=edge.cap
		flow=0
		while self.bfs():
			df=1
			while df>0:
				df=self.dfs()
				flow+=df
		return flow

