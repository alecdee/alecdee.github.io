"""
Fraction.py - v1.01

Copyright 2020 Alec Dee - MIT license - SPDX: MIT
alecdee.github.io - akdee144@gmail.com

--------------------------------------------------------------------------------
Continued fractions:

sqrt(2)=[1;2,2,2,2,2,...] = 1+(i>0)
e  =[2;1,2,1,1,4,1,1,6,1,1,8,1,1,10] = 1+(i==0)+(((i%3)&2)*i)//3
phi=[1;1,1,1,1,1,...] = 1
pi =[3;7,15,1,292,1,1,1,2,1,3,1,14,2,1,1,2,2,2,2]

If a CF is periodic, it is a quadratic root.
A CF will be finite iff it represents a rational.
The CFs of irrationals are unique.
"""

def gcd(a,b):
	while b:
		a,b=b,a%b
	return abs(a)

class Fraction(object):
	def __init__(self,n,d=None):
		assert(d!=0)
		if d==None: d=1
		if d<0: n,d=-n,-d
		g=gcd(n,d)
		self.n=n//g
		self.d=d//g

	def __repr__(self):
		return "Fraction("+repr(self.n)+","+repr(self.d)+")"

	def __str__(self):
		return str(self.n)+"/"+str(self.d)

	def __int__(a):
		n=a.n
		if n>=0: n//a.d
		return -((-n)//a.d)

	def __float__(a):
		return float(a.n)/float(a.d)

	def __abs__(a):
		return Fraction(abs(a.n),a.d)

	#---------------------------------------------------------------------------------
	# Comparisons
	#---------------------------------------------------------------------------------

	def __eq__(a,b):
		if isinstance(b,Fraction):
			return a.n*b.d==b.n*a.d
		elif b==None:
			return False
		return a.n==b*a.d

	def __lt__(a,b):
		if isinstance(b,Fraction):
			return a.n*b.d<b.n*a.d
		return a.n<b*a.d

	#---------------------------------------------------------------------------------
	# Algebra
	#---------------------------------------------------------------------------------

	def __add__(a,b):
		if not isinstance(b,Fraction): b=Fraction(b)
		return Fraction(a.n*b.d+b.n*a.d,a.d*b.d)

	def __neg__(a):
		return Fraction(-a.n,a.d)

	def __sub__(a,b):
		if not isinstance(b,Fraction): b=Fraction(b)
		return Fraction(a.n*b.d-b.n*a.d,a.d*b.d)

	def __mul__(a,b):
		if not isinstance(b,Fraction): b=Fraction(b)
		return Fraction(a.n*b.n,a.d*b.d)

	def __rmul__(a,b):
		if not isinstance(b,Fraction): b=Fraction(b)
		return Fraction(b.n*a.n,b.d*a.d)

	def __truediv__(a,b):
		if not isinstance(b,Fraction): b=Fraction(b)
		return Fraction(a.n*b.d,a.d*b.n)

	def __rtruediv__(a,b):
		if not isinstance(b,Fraction): b=Fraction(b)
		return Fraction(b.n*a.d,b.d*a.n)

	__div__=__truediv__
	__rdiv__=__rtruediv__

	def __floordiv__(a,b):
		return int(a/b)

	def __rfloodiv__(a,b):
		return int(b/a)

	def __mod__(a,b):
		d=a//b
		return a-d*b

	def __rmod__(a,b):
		d=b//a
		return b-d*a

	#---------------------------------------------------------------------------------
	# Exponentiation
	#---------------------------------------------------------------------------------

	def __pow__(self,exp):
		n,d=self.n,self.d
		if exp<0:
			if n==0: raise ZeroDivisionError("Can't take 0/1^-1.")
			n,d=d,n
			if d<0: n,d=-n,-d
			exp=-exp
		return Fraction(n**exp,d**exp)

	#---------------------------------------------------------------------------------
	# Misc
	#---------------------------------------------------------------------------------

	@staticmethod
	def approx(val,dmax,dmin=None):
		"""Find the best approximate val~=num/den for dmin<=den<=dmax."""
		if dmin!=None:
			dmin,dmax=dmax,dmin
		else:
			dmin=1
		assert(dmax>=1 and dmin<=dmax)
		orig=abs(val)
		if dmin<=1:
			# Create an initial Farey interval with lower bound floor(val) and upper bound
			# +inf. Note that n and d will always be coprime.
			print("orig: ",orig)
			nl,dl=int(orig),1
			nu,du=1,0
			fmin=Fraction(nl,dl)
			emin=abs(fmin-orig)
			while True:
				# Find a fraction between the lower and upper bounds.
				n,d=nl+nu,dl+du
				if d>dmax:
					break
				f=Fraction(n,d)
				err=abs(f-orig)
				# If this is the best approximation.
				if emin>err:
					emin=err
					fmin=f
				# Refine the interval.
				if f<orig:
					nl,dl=n,d
				else:
					nu,du=n,d
		else:
			# Based on an algorithm by Fyodor Menshikov and Zilin Jiang.
			# First, we find the Farey intervals that will fit in [0,max-min].
			gap=dmax-dmin
			nl,dl=int(orig),1
			nu,du=1,0
			farey=[(nl,dl)]
			while True:
				n,d=nl+nu,dl+du
				if d>dmax:
					break
				farey.append((n,d))
				f=Fraction(n,d)
				if f<orig:
					nl,dl=n,d
				else:
					nu,du=n,d
			# Start our initial approximation at x/dmin for the x closest to orig. Then, loop
			# through the Farey intervals and add the smallest one that makes the
			# approximation more accurate. If no interval increases accuracy, we are done.
			nmin=int(2*orig*dmin+1)//2
			fmin=Fraction(nmin,dmin)
			emin=abs(fmin-orig)
			i,l=0,len(farey)
			while i<l:
				nd=farey[i]
				n,d=nmin+nd[0],dmin+nd[1]
				if d>dmax:
					break
				f=Fraction(n,d)
				err=abs(f-orig)
				if emin>err:
					emin=err
					fmin=f
					nmin,dmin=n,d
					i=-1
				i+=1
			# If there are two numerators that are the same distance to the desired value,
			# take the smaller one. Ex: if orig=5/2, then 2/1 and 3/1 are the same distance,
			# so we take 2/1.
			f=Fraction(fmin.n-1,fmin.d)
			if emin>=abs(f-orig):
				fmin=f
		if val<0:
			fmin.n=-fmin.n
		return fmin

	def changeden(self,den):
		# Given n0/d0 and d1, find n1 such that n0/d0~=n1/d1.
		n,d=self.n,self.d
		if n<0:
			n=-((-2*n*den+d)//(2*d))
		else:
			n=(2*n*den+d)//(2*d)
		return Fraction(n,den)

