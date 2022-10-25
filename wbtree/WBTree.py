"""

WBTree.py - v1.01

Copyright 2022 Alec Dee - MIT license - SPDX: MIT
alecdee.github.io - akdee144@gmail.com


--------------------------------------------------------------------------------
Notes


A weight balanced search tree implementation.

Balancing is performed by keeping the weights of children within a ratio of 2.5.

Because weights are used, we can lexicographically index nodes. Ex: tree[0] will
return the smallest node in the tree.

Adding and removing values are stable with respect to sorting.

weight(null) = 0

Tree height < 2.07 * log2(nodes+1)


--------------------------------------------------------------------------------
TODO


Bulk operations.
Set theory operations.
See if there's better criteria for double rotations.


"""


class WBTree(object):
	# Searching constants.
	EQ,EQG,LT,LE,GT,GE=0,1,2,3,4,5


	class Node(object):
		def __init__(self,value):
			self.weight=1
			self.parent=None
			self.left=None
			self.right=None
			self.value=value


		def next(node):
			# Given a node N, find the next ordered node. Ex: next(3)=4.
			#
			#            4
			#           / \
			#          /   \
			#         2     6
			#        / \   / \
			#       1   3 5   7
			#
			# If N has a right child, R, the left-most child of R is the next node.
			# Otherwise, the nearest parent of N with N on the left is the next node.
			child=node.right
			if child:
				while child: node,child=child,child.left
			else:
				while node and node.right is child:
					child,node=node,node.parent
			return node


		def prev(node):
			# Given a node N, find the previous ordered node. Ex: prev(5)=4.
			#
			#            4
			#           / \
			#          /   \
			#         2     6
			#        / \   / \
			#       1   3 5   7
			#
			# If N has a left child, L, the right-most child of L is the next node.
			# Otherwise, the nearest parent of N with N on the right is the next node.
			child=node.left
			if child:
				while child: node,child=child,child.right
			else:
				while node and node.left is child:
					child,node=node,node.parent
			return node


		def rotleft(a):
			# Raise z, lower x, and maintain the sorted order of the nodes.
			#
			#        A                B
			#       / \              / \
			#      x   B     ->     A   z
			#         / \          / \
			#        y   z        x   y
			#
			b=a.right
			r=b.left
			b.parent=a.parent
			b.left=a
			a.parent=b
			a.right=r
			if r: r.parent=a
			a.calcweight()
			b.calcweight()
			return b


		def rotright(a):
			# Raise x, lower z, and maintain the sorted order of the nodes.
			#
			#          A            B
			#         / \          / \
			#        B   z   ->   x   A
			#       / \              / \
			#      x   y            y   z
			#
			b=a.left
			l=b.right
			b.parent=a.parent
			b.right=a
			a.parent=b
			a.left=l
			if l: l.parent=a
			a.calcweight()
			b.calcweight()
			return b


		def calcweight(self):
			l,r,weight=self.left,self.right,1
			if l: weight+=l.weight
			if r: weight+=r.weight
			self.weight=weight


		def index(node):
			# Returns the node's index within the tree. Ex: tree[node.index()]=node.
			i=-1
			prev=node.right
			while node:
				if node.right is prev:
					i+=node.left.weight+1 if node.left else 1
				prev=node
				node=node.parent
			return i


	def __init__(self,cmp=None,unique=False):
		# cmp(l,r) is expected to be a function where
		#
		#      cmp(l,r)<0 if l<r
		#      cmp(l,r)=0 if l=r
		#      cmp(l,r)>0 if l>r
		#
		# If unique is True, then duplicate values will overwrite eachother.
		def defcmp(l,r):
			if l<r: return -1
			if l>r: return 1
			return 0
		self.cmp=defcmp if cmp is None else cmp
		self.unique=unique
		self.root=None


	def clear(self):
		self.root=None


	def __len__(self):
		# Return the number of nodes in the tree.
		return self.root.weight if self.root else 0


	def __getitem__(self,i):
		# Index nodes like an array.
		node=self.root
		weight=node.weight if node else 0
		if i<0: i+=weight
		if i<0 or i>=weight: return None
		while True:
			left=node.left
			lw=left.weight if left else 0
			if i>lw:
				i-=lw+1
				node=node.right
			elif i==lw:
				break
			else:
				node=left
		return node


	def __iter__(self):
		# Iterate over all nodes in ascending order.
		node=self.first()
		while node:
			yield node
			node=node.next()


	def first(self):
		# Return the smallest node in the tree.
		node,ret=self.root,None
		while node: ret,node=node,node.left
		return ret


	def last(self):
		# Return the greatest node in the tree.
		node,ret=self.root,None
		while node: ret,node=node,node.right
		return ret


	def find(self,value,mode=EQ):
		# Search for a specific value or inequality.
		#
		#      EQ : Return the least    node=value.
		#      EQG: Return the greatest node=value.
		#      LT : Return the greatest node<value.
		#      LE : Return the greatest node<=value.
		#      GT : Return the least    node>value.
		#      GE : Return the least    node>=value.
		#
		node,ret=self.root,None
		unique,cmp=self.unique,self.cmp
		lset  =(False,False,True ,True ,False,False)[mode]
		rset  =(False,False,False,False,True ,True )[mode]
		eset  =(True ,True ,False,True ,False,True )[mode]
		eright=(False,True ,False,True ,True ,False)[mode]
		while node:
			c=cmp(node.value,value)
			if c<0:
				if lset: ret=node
				node=node.right
			elif c>0:
				if rset: ret=node
				node=node.left
			else:
				if eset:
					ret=node
					if unique: break
				node=node.right if eright else node.left
		return ret


	def add(self,value):
		# Find a leaf node to add the new value to. Then rebalance from the new node on
		# up. By traversing right when cmp<=0, this algorithm is stable.
		prev,node=None,self.root
		unique=0 if self.unique else None
		c,cmp=0,self.cmp
		while node:
			c=cmp(node.value,value)
			if c==unique:
				node.value=value
				return node
			prev=node
			if c<=0: node=node.right
			else   : node=node.left
		node=self.Node(value)
		node.parent=prev
		if prev is None:
			self.root=node
		else:
			if c<=0: prev.right=node
			else   : prev.left=node
			self.rebalance(prev)
		return node


	def remove(self,value):
		# Remove a node given a value.
		node=self.find(value)
		if node is None: raise KeyError("Value not in tree: "+str(value))
		self.removenode(node)
		return node


	def removenode(self,node):
		# Remove a specific node. We can remove a node by swapping it with its successor
		# to maintain order and stability sorting-wise. Then, rebalance from the successor
		# on up.
		#
		#           Case 1          |          Case 2           |          Case 3
		#                           |                           |
		#   N has no right child.   |  X is the right child of  |  X is a distant child of
		#   Balance from D up.      |  N. Balance from X up.    |  N. Balance from C up.
		#                           |                           |
		#     B              B      |     N              X      |    N              X
		#    / \            / \     |    / \            / \     |   / \            / \
		#   A   D     ->   A   D    |   A   X     ->   A   B    |  A   C          A   C
		#      / \            / \   |      / \                  |     / \    ->      / \
		#     C   N          C   X  |     *   B                 |    X   D          B   D
		#        / \                |                           |   / \
		#       X   *               |                           |  *   B
		#
		p=node.parent
		l,r=node.left,node.right
		if r is None:
			# Case 1
			bal,next,l=p,l,None
		elif r.left:
			# Case 3
			next=r
			while next.left: bal,next=next,next.left
			c=next.right
			bal.left=c
			if c: c.parent=bal
		else:
			# Case 2
			bal,next,r=r,r,None
		# Replace node with next.
		if p is None: self.root=next
		elif p.left is node: p.left=next
		else: p.right=next
		if next:
			next.parent=p
			if l: next.left,l.parent=l,next
			if r: next.right,r.parent=r,next
		self.rebalance(bal)


	def rebalance(self,next):
		# Rebalance from next upward. If 2 children differ in weight by a ratio of 2.5 or
		# more, we can rotate to rebalance.
		def Weight(n): return n.weight if n else 0
		while next:
			node,orig=next,next
			next=node.parent
			l,r=node.left,node.right
			lw,rw=Weight(l),Weight(r)
			if rw*5+2<lw*2:
				# Leaning to the left.
				if Weight(l.left)*5<lw*2: node.left=l.rotleft()
				node=node.rotright()
			elif lw*5+2<rw*2:
				# Leaning to the right.
				if Weight(r.right)*5<rw*2: node.right=r.rotright()
				node=node.rotleft()
			else:
				# Balanced.
				node.weight=lw+rw+1
				continue
			if next is None: self.root=node
			elif next.left is orig: next.left=node
			else: next.right=node


if __name__=="__main__":
	# Example usage.

	tree=WBTree()
	tree.add((5,"Friday"))
	tree.add((3,"Wednesday"))
	tree.add((1,"Monday"))
	tree.add((6,"Saturday"))
	tree.add((2,"Tuesday"))
	tree.add((4,"Thursday"))
	tree.remove((6,"Saturday"))

	print("Iterate:")
	for node in tree:
		print("{0}: {1}".format(*node.value))

	print("Index:")
	for i in range(len(tree)):
		node=tree[i]
		print("{0}: {1}".format(*node.value))

