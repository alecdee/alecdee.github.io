"""
MatrixTest.py - v1.01

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

import sys
from math import sin,cos,acos,sqrt,atan2,pi
from random import randrange,random,seed
from time import time
sys.path.insert(0,"../")
from Matrix import Matrix,Vector
from IntMod import IntMod

#--------------------------------------------------------------------------------
#Matrix
#--------------------------------------------------------------------------------

"""
def findelemunit(self):
	#Returns (zero,one) in the units of the current elements.
	#Find the additive and multiplicative identities, 'zero' and 'one', for some
	#arbitrary type. If the values are already supplied, then we are done.
	zero,one=None,None
	srow,rows,cols=self.row,self.rows,self.cols
	#If we have no elements to loop through, we won't be able to know the desired
	#type, let alone the desired identities. Thus, give default values to zero and
	#one.
	if one==None and (rows==0 or cols==0 or type(srow[0][0]) in (int,bool,float)):
		one=1
	if one==None:
		for i in range(rows*cols):
			v=srow[i//cols][i%cols]
			#Calculate the multiplicative identity.
			#Want v*1=1*v=v and 1*0!=1 => 1-1!=1.
			try:
				one=v//v
				if v*one==v and one*v==v:
					break
			except ArithmeticError:
				pass
			try:
				one=v/v
				if v*one==v and one*v==v:
					break
			except ArithmeticError:
				pass
			try:
				one=v*(v**-1)
				if v*one==v and one*v==v:
					break
			except ArithmeticError:
				pass
			one=None
		if one==None:
			raise ZeroDivisionError("Could not find multiplicative unit.")
	if zero==None:
		zero=one-one
	#Return what we have.
	return (zero,one)
"""

def MatrixTest():
	print("Testing matrix operations.")
	trials=10000
	mod=107
	Matrix.setunit(IntMod(1,mod))
	maxsize=10
	zero,one=IntMod(0,mod),IntMod(1,mod)
	def randmod():
		return IntMod(randrange(mod),mod)
	def randmat(rows,cols):
		m=Matrix(rows,cols)
		for row in m.row:
			for c in range(cols):
				row[c]=randmod()
		return m
	def randtri(rows):
		m=Matrix(rows,rows)
		for r in range(rows):
			row=m.row[r]
			for c in range(rows):
				if c>=r:
					row[c]=randmod()
				else:
					row[c]=IntMod(0,mod)
		return m
	def randmix(m):
		for i in range(2*m.rows):
			j,k=i%m.rows,randrange(m.rows)
			if j==k:
				continue
			mul=randmod()
			j,k=m.row[j],m.row[k]
			for l in range(m.cols):
				j[l]+=k[l]*mul
	for trial in range(trials):
		rows,cols=randrange(maxsize+1),randrange(maxsize+1)
		a=randmat(rows,cols)
		b=randmat(rows,cols)
		c=a+b
		assert(c==b+a)
		c-=b
		assert(c==a)
		c+=b-a
		assert(c==b)
		c+=-b
		assert(c==a-a)
		ncols=randrange(maxsize+1)
		c=randmat(cols,ncols)
		d0=(a+b)*c
		d1=a*c+b*c
		assert(d0==d1 and d0.rows==rows and d0.cols==ncols)
		assert(a.T().T()==a)
		s=randmod()
		if s==zero: s=one
		assert(a/s==a*s.inv() and a//s==a*s.inv())
		tmp=Matrix(a)
		tmp/=s
		assert(tmp*s==a and tmp==a*s.inv())
		a=randtri(rows)
		b=randtri(rows)
		a0=IntMod(1,mod)
		b0=IntMod(1,mod)
		for i in range(rows):
			a0*=a[i][i]
			b0*=b[i][i]
		randmix(a)
		randmix(b)
		assert(a0==abs(a) and b0==abs(b))
		assert(a0*b0==abs(a*b) and b0*a0==abs(b*a))
		s=randmod()
		assert(abs(a*s)==(s**rows)*abs(a))
		id=Matrix(rows,rows)
		for r in range(rows):
			for c in range(rows):
				id[r][c]=(zero,one)[r==c]
		try:
			ai=a.inv()
			assert(a0!=zero)
			assert(a*ai==id and ai*a==id)
			assert(a/a==id and a//a==id)
		except ZeroDivisionError:
			ai=None
			assert(a0==zero)
		c=Matrix(a)
		exp=randrange(-16,17)
		e,mul=id,a
		if exp<0:
			mul=ai
			if ai==None:
				e=None
		if e!=None:
			for i in range(abs(exp)):
				e=e*mul
		try:
			assert(a**exp==e and e!=None)
		except ZeroDivisionError:
			assert(exp<=0 and ai==None)
		assert(a==c)
	print("Passed.")

def MatrixFloatTest():
	print("Testing Matrix floating point.")
	Matrix.setunit(1.0)
	trials=10000
	maxdim=10
	mixmul=20
	error,errors=0,0
	seed(1)
	for trial in range(trials):
		n=randrange(maxdim+1)
		m=Matrix(n,n)
		major=list(range(n))
		dup=max(0,randrange(2*n+1)-n-(n==1))
		for i in range(dup):
			j=randrange(n)
			major[j]=major[(j+randrange(1,n))%n]
		for i in range(n):
			m[major[i]][i]=1.0
		for i in range(randrange(mixmul*n+1)):
			j,k=i%n,randrange(n)
			mul=random()*4.0-2.0
			if j!=k:
				j,k=m[j],m[k]
				for l in range(n):
					k[l]+=j[l]*mul
		inv=None
		try:
			inv=m.inv()
			mul=m*inv
			err=0.0
			for r in range(n):
				row=mul[r]
				for c in range(n):
					d=float(r==c)-row[c]
					err+=d*d
			if n:
				error+=sqrt(err/(n*n))
				errors+=1
		except ZeroDivisionError:
			inv=None
		if (inv!=None)!=(n==0 or dup==0):
			print("M=")
			print(m)
			if inv==None:
				print("Unable to find inverse:"+str(n))
			else:
				print("Found impossible inverse:"+str(n)+"\nM*M^-1=")
				print(m*inv)
			exit()
	error/=errors+(errors==0)
	print("errors: {0}".format(errors))
	print("error : {0:.8f}".format(error))
	print("Passed.")

def MatrixPrintTest():
	print("Testing matrix printing.")
	rows,cols=5,4
	maxdim=4
	minval,maxval=-10,11
	mat=Matrix(rows,cols)
	for row in mat.row:
		for c in range(cols):
			subrows=randrange(maxdim+1)
			subcols=randrange(maxdim+1)
			sub=Matrix(subrows,subcols)
			sub.row=[[randrange(minval,maxval) for j in range(subcols)] for i in range(subrows)]
			#print(str(sub))
			row[c]=sub
	print(str(mat))
	print("Passed.")

def MatrixSpeedTest():
	seed(1)
	trials=100000
	a=Matrix(17,17)
	b=Matrix(17,17)
	for r in range(a.rows):
		for c in range(a.cols):
			a[r][c]=random()*100.0-50.0
	for r in range(b.rows):
		for c in range(b.cols):
			b[r][c]=random()*100.0-50.0
	#for i in range(a.elems):
	#	a.elem[i]=random()*100.0-50.0
	#for i in range(b.elems):
	#	b.elem[i]=random()*100.0-50.0
	t0=time()
	for trial in range(trials):
		#a.inv()
		#a*b
		abs(a)
	t0=time()-t0
	print("Matrix speed test")
	print("#{0:.6f}".format(t0))

def SolvePoly():
	#Solving a polynomial:
	def poly(x):
		return [1,x+1,(x+1)**2,(x+1)**3,(x+1)**4,[2,4,7,10,12][x]]
	n=5
	m=Matrix(n,n+1)
	for r in range(n):
		m.row[r]=poly(r)
	m=m.reduced()
	print(str(m))

#--------------------------------------------------------------------------------
#Vector
#--------------------------------------------------------------------------------

"""
@staticmethod
def cross(vecarr):
	#Returns an n-dimensional vector orthogonal to n-1 vectors.
	dim,one=len(vecarr)+1,Matrix.getone
	last=[Vector(dim) for i in range(dim)]
	for i in range(dim): last[i][i]=one()
	return abs(Matrix(list(vecarr)+[last]))

@property
def x(self): return self.elem[0]
@x.setter
def x(self,v): self.elem[0]=v

@property
def y(self): return self.elem[1]
@y.setter
def y(self,v): self.elem[1]=v

@property
def z(self): return self.elem[2]
@z.setter
def z(self,v): self.elem[2]=v

@staticmethod
def fromangle(xang=None,yang=None,zang=None):
	if xang!=None and yang!=None:
		raise NotImplementedError
	elif xang!=None and zang!=None:
		raise NotImplementedError
	elif yang!=None and zang!=None:
		raise NotImplementedError
	elif xang!=None:
		return Vector(cos(xang),sin(xang))
	else:
		raise NotImplementedError

def angle(self):
	#Returns the 2D angle of u in [0,2pi).
	uelem=self.elem
	return pi-atan2(uelem[1],-uelem[0])

def left(self):
	#Rotate a 2D vector left 90 degrees.
	uelem=self.elem
	return Vector(-uelem[1],uelem[0])

def right(self):
	#Rotate a 2D vector right 90 degrees.
	uelem=self.elem
	return Vector(uelem[1],-uelem[0])

def __lshift__(self,v):
	#Rotate a 2D vector counter-clockwise by v, u<<v. v must be a vector or
	#a scalar denoting radians.
	uelem=self.elem
	if isinstance(v,Vector):
		#x=u.x*v.x-u.y*v.y
		#y=u.y*v.x+u.x*v.y
		velem=v.elem
		return Vector(uelem[0]*velem[0]-uelem[1]*velem[1],
		              uelem[1]*velem[0]+uelem[0]*velem[1])
	#Rotate counter clockwise by some angle v.
	cs,sn=cos(v),sin(v)
	return Vector(uelem[0]*cs-uelem[1]*sn,
	              uelem[1]*cs+uelem[0]*sn)

def __ilshift__(self,v):
	#Rotate a 2D vector counter-clockwise by v, u<<=v. v must be a vector or
	#a scalar denoting radians.
	self.elem=self.__lshift__(v).elem
	return self

def __rshift__(self,v):
	#Rotate a 2D vector clockwise by v, u>>v. v must be a vector or a scalar
	#denoting radians.
	uelem=self.elem
	if isinstance(v,Vector):
		#x=u.x*v.x+u.y*v.y
		#y=u.y*v.x-u.x*v.y
		velem=v.elem
		return Vector(uelem[0]*velem[0]+uelem[1]*velem[1],
		              uelem[1]*velem[0]-uelem[0]*velem[1])
	#Rotate clockwise by some angle v.
	cs,sn=cos(v),sin(v)
	return Vector(uelem[0]*cs+uelem[1]*sn,
	              uelem[1]*cs-uelem[0]*sn)

def __irshift__(self,v):
	#Rotate a 2D vector clockwise by v, u>>=v. v must be a vector or a scalar
	#denoting radians.
	self.elem=self.__rshift__(v).elem
	return self
"""

def TmpCross(u,v):
	return Vector([
		u[1]*v[2]-u[2]*v[1],
		u[2]*v[0]-u[0]*v[2],
		u[0]*v[1]-u[1]*v[0]],False)

def VectorTest():
	print("Testing vector operations.")
	trials=10000
	mod=107
	Matrix.setunit(IntMod(1,mod))
	maxsize=30
	zero,one=IntMod(0,mod),IntMod(1,mod)
	def randmod():
		return IntMod(randrange(mod),mod)
	def testvec(l,v):
		if (not isinstance(l,tuple)) or (not isinstance(v,Vector)):
			print("Error: incorrect types: {0}, {1}".format(type(l),type(v)))
			exit()
		n=len(l)
		if len(v)!=n:
			print("Error: incorrect length: {0}!={1}".format(n,len(v)))
			exit()
		for i in range(n):
			if l[i]!=v[i]:
				print("Error: numerical drift: {0}!={1}".format(l[i],v[i]))
				exit()
	for trial in range(trials):
		#Create the test vectors.
		n=randrange(maxsize)
		ulist=tuple([randmod() for i in range(n)])
		vlist=tuple([randmod() for i in range(n)])
		#Create with lists, manually, or with vectors.
		u=Vector(ulist)
		v=Vector(vlist)
		if randrange(2):
			u=Vector(u)
			v=Vector(v)
		#Check the vector creation.
		testvec(ulist,u)
		testvec(vlist,v)
		#Addition.
		wuv=u+v
		wvu=v+u
		wlist=tuple([ulist[i]+vlist[i] for i in range(n)])
		testvec(wlist,wuv)
		testvec(wlist,wvu)
		w=Vector(u)
		w+=v
		testvec(ulist,u)
		testvec(vlist,v)
		testvec(wlist,w)
		#Subtraction and negation.
		wuv=u-v
		wvu=v-u
		wlist=tuple([ulist[i]-vlist[i] for i in range(n)])
		testvec(wlist, wuv)
		testvec(wlist,-wvu)
		wuv=u+(-v)
		wvu=(-u)+v
		testvec(wlist, wuv)
		testvec(wlist,-wvu)
		w=Vector(u)
		w-=v
		testvec(ulist,u)
		testvec(vlist,v)
		testvec(wlist,w)
		#Multiplication and dot product.
		dotuv=u*v
		dotvu=v*u
		dotuu=u*u
		dot=IntMod(0,mod)
		for i in range(n): dot+=ulist[i]*vlist[i]
		if dotuv!=dot or dotvu!=dot:
			print("Error: dot product u*v: {0}, {1}, {2}".format(dot,dotuv,dotvu))
			exit()
		dot=IntMod(0,mod)
		for i in range(n): dot+=ulist[i]*ulist[i]
		if dotuu!=dot:
			print("Error: dot product u*u: {0}, {1}".format(dot,dotuu))
			exit()
		mul=randmod()
		wl=u*mul
		wr=mul*u
		wlist=tuple([ulist[i]*mul for i in range(n)])
		testvec(wlist,wl)
		testvec(wlist,wr)
		w=Vector(u)
		w*=mul
		testvec(wlist,w)
		#Cross product.
		if n==3:
			cross0=TmpCross(u,v)
			cross1=Vector.cross([u,v])
			if cross0!=cross1:
				print("Error: cross product uxv: {0}, {1}".format(cross0,cross1))
				exit()
		#Division.
		div=zero
		while div==zero: div=randmod()
		wmul=u*(1/div)
		wdiv=u/div
		wlist=tuple([ulist[i]/div for i in range(n)])
		testvec(wlist,wmul)
		testvec(wlist,wdiv)
		w=Vector(u)
		w/=div
		testvec(wlist,w)
		#Misc properties.
		if u*u!=u.sqr() or (-u).sqr()!=u.sqr() or (u-u).sqr()!=zero:
			print("Error: sqr")
			exit()
		mag=zero
		try: mag=dotuu**0.5
		except ZeroDivisionError: pass
		if mag!=zero:
			assert(abs(u)==mag)
			w=u.norm()
			assert(w*w==one)
			assert(w*u==mag)
	print("passed")

def VectorSpeedTest():
	"""Internal use. Performance testing of operations."""
	#The majority of vector operations will be in 2 or 3 dimensions, so optimize
	#speed for those dimensions.
	tests=1000000
	#2D
	u=Vector(2).randomize()*4.0
	v=Vector(2).randomize()*4.0
	s=1.0
	t2=time()
	for i in range(tests):
		u+v
		u*v
	t2=time()-t2
	#3D
	u=Vector(3).randomize()*4.0
	v=Vector(3).randomize()*4.0
	t3=time()
	for i in range(tests):
		u+v
		u*v
	t3=time()-t3
	#nD
	u=Vector(100).randomize()*4.0
	v=Vector(100).randomize()*4.0
	tn=time()
	for i in range(tests):
		u+v
		u*v
	tn=time()-tn
	print("  2D: "+"{0:0.12f}".format(t2))
	print("  3D: "+"{0:0.12f}".format(t3))
	print("100D: "+"{0:0.12f}".format(tn))

#--------------------------------------------------------------------------------
#Main
#--------------------------------------------------------------------------------

if __name__=="__main__":
	MatrixTest()
	#MatrixFloatTest()
	VectorTest()
	#MatrixPrintTest()
	#MatrixSpeedTest()
	#VectorSpeedTest()
	#SolvePoly()


