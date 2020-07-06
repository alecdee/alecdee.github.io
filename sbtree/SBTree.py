"""
SBTree.py - v1.06

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
A self balancing binary search tree implementation.

Notes:
     Adding and removing are stable with respect to sorting.
     Balancing is performed by keeping the heights of children within +-1 of
     eachother (AVL).
     height(null)=0
     tree height<1.440*log2(nodes+1)
"""

class SBTree(object):
	#Searching constants.
	EQ,EQL,EQG,LT,LE,GT,GE=0,1,2,3,4,5,6

	class Node(object):
		def __init__(self,key,value):
			self.key=key
			self.value=value
			self.parent=None
			self.left=None
			self.right=None
			self.height=0

		def next(node):
			#Given a node N, find the next ordered node. Ex: next(3)=4.
			#
			#           4
			#          / \
			#         /   \
			#        2     6
			#       / \   / \
			#      1   3 5   7
			#
			#If N has a right child, R, the left-most child of R is the next node.
			#Otherwise, the nearest parent of N with N on the left is the next node.
			child=node.right
			if child:
				while child: node,child=child,child.left
			else:
				while node and node.right is child:
					child,node=node,node.parent
			return node

		def prev(node):
			#Given a node N, find the previous ordered node. Ex: prev(5)=4.
			#
			#           4
			#          / \
			#         /   \
			#        2     6
			#       / \   / \
			#      1   3 5   7
			#
			#If N has a left child, L, the right-most child of L is the next node.
			#Otherwise, the nearest parent of N with N on the right is the next node.
			child=node.left
			if child:
				while child: node,child=child,child.right
			else:
				while node and node.left is child:
					child,node=node,node.parent
			return node

		def rotleft(a):
			#Raise z, lower x, and maintain the sorted order of the nodes.
			#
			#       A                B
			#      / \              / \
			#     x   B     ->     A   z
			#        / \          / \
			#       y   z        x   y
			#
			b=a.right
			a.right=b.left
			b.left=a
			b.parent=a.parent
			a.parent=b
			if a.right: a.right.parent=a
			a.calcheight()
			b.calcheight()
			return b

		def rotright(a):
			#Raise x, lower z, and maintain the sorted order of the nodes.
			#
			#         A            B
			#        / \          / \
			#       B   z   ->   x   A
			#      / \              / \
			#     x   y            y   z
			#
			b=a.left
			a.left=b.right
			b.right=a
			b.parent=a.parent
			a.parent=b
			if a.left: a.left.parent=a
			a.calcheight()
			b.calcheight()
			return b

		def calcheight(self):
			l,r=self.left,self.right
			lh=l.height if l else 0
			rh=r.height if r else 0
			self.height=(lh if lh>rh else rh)+1

	def __init__(self,unique=True,cmp=None):
		def defcmp(l,r):
			if r<l: return 1
			if l<r: return -1
			return 0
		self.cmp=cmp if cmp else defcmp
		self.unique=0 if unique else None
		self.root=None

	def find(self,key,flag=EQ):
		#Search for a specific value or inequality.
		#EQ : Return some node=key.
		#EQL: Return the least    node=key.
		#EQG: Return the greatest node=key.
		#LT : Return the greatest node<key.
		#LE : Return the greatest node<=key.
		#GT : Return the least    node>key.
		#GE : Return the least    node>=key.
		#
		#       break     set     right
		#cmp:  1  0 -1  1  0 -1  1  0 -1
		#--------------------------------
		#EQ :  0  1  0  0  1  0  0  0  1
		#EQF:  0  0  0  0  1  0  0  0  1
		#EQL:  0  0  0  0  1  0  0  1  1
		#LT :  0  0  0  0  0  1  0  0  1
		#LE :  0  0  0  0  1  1  0  1  1
		#GT :  0  0  0  1  0  0  0  1  1
		#GE :  0  0  0  1  1  0  0  0  1
		node,ret,cmp=self.root,None,self.cmp
		con=(145,17,19,9,27,35,49)[flag]
		while node:
			c=cmp(node.key,key)
			c=con>>((c>0)-(c<0)+1)
			if c&8:
				ret=node
				if c&64: break
			if c&1: node=node.right
			else  : node=node.left
		return ret

	def add(self,key,value=None):
		#Find a leaf node to add the new key to. Then rebalance from the new node on up.
		#By traversing left when cmp<0, this algorithm is stable.
		prev,node=None,self.root
		unique=self.unique
		c,cmp=0,self.cmp
		while node:
			prev=node
			c=cmp(key,node.key)
			if c==unique:
				node.value=value
				return node
			if c<0: node=node.left
			else  : node=node.right
		node=SBTree.Node(key,value)
		node.parent=prev
		if c<0: prev.left=node
		self.rebalance(node)
		return node

	def remove(self,key):
		#Remove a node given a key.
		node=self.find(key)
		if node is None: raise KeyError("Key not in tree")
		self.removenode(node)
		return node

	def removenode(self,node):
		#Remove a specific node. We can remove a node by swapping it with its successor
		#to maintain order and stability sorting-wise. Then, rebalance from the
		#successor on up.
		#
		#          Case 1          |          Case 2           |          Case 3
		#  N is the right-most     |  X is a distant child of  |  X is the right child of
		#  child in the tree.      |  N. Balance from C up.    |  N. Balance from X up.
		#  Balance from D up.      |                           |
		#                          |                           |
		#    B              B      |    N              X       |    N              X
		#   / \            / \     |   / \            / \      |   / \            / \
		#  A   D     ->   A   D    |  A   C          A   C     |  A   X     ->   A   B
		#     / \            / \   |     / \    ->      / \    |     / \
		#    C   N          C   X  |    X   D          B   D   |    *   B
		#       / \                |   / \                     |
		#      X   *               |  *   B                    |
		#
		p=node.parent
		l,r=node.left,node.right
		if r is None:
			#Case 1
			bal,next,l=p,l,None
		elif r.left:
			#Case 2
			next=r
			while next.left: bal,next=next,next.left
			c=next.right
			bal.left=c
			if c: c.parent=bal
			next.height=node.height
		else:
			#Case 3
			bal,next,r=r,r,None
			next.height=node.height
		#Replace node with next.
		if p is None: self.root=next
		elif p.left is node: p.left=next
		else: p.right=next
		if next:
			next.parent=p
			if l: next.left,l.parent=l,next
			if r: next.right,r.parent=r,next
		self.rebalance(bal)

	def rebalance(self,node):
		#Rebalance from node upward. If 2 children differ in height by 2 or more, we can
		#rotate to rebalance. If a node's height hasn't changed, we can stop balancing.
		def H(n): return n.height if n else 0
		while node:
			orig,p=node,node.parent
			l,r=node.left,node.right
			lh,rh,nh=H(l),H(r),node.height
			if rh+1<lh:
				if H(l.left)+1<lh: node.left=l.rotleft()
				node=node.rotright()
			elif lh+1<rh:
				if H(r.right)+1<rh: node.right=r.rotright()
				node=node.rotleft()
			else:
				node.height=(lh if lh>rh else rh)+1
			if p is None: self.root=node
			elif p.left is orig: p.left=node
			else: p.right=node
			if node.height==nh: break
			node=p

	def first(self):
		#Return the smallest node of the tree.
		node,ret=self.root,None
		while node: ret,node=node,node.left
		return ret

	def last(self):
		#Return the greatest node of the tree.
		node,ret=self.root,None
		while node: ret,node=node,node.right
		return ret

	def __iter__(self):
		#Iterate over all nodes.
		node=self.first()
		while node:
			yield node
			node=node.next()

if __name__=="__main__":
	#Example usage.
	tree=SBTree(unique=False)
	tree.add(6,"Friday")
	tree.add(3,"Wednesday")
	tree.add(1,"Monday")
	tree.add(5,"REMOVE")
	tree.add(2,"Tuesday")
	tree.add(3,"Thursday")
	tree.remove(5)
	for n in tree:
		print(str(n.key)+": "+str(n.value))

