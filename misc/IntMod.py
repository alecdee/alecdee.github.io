"""
IntMod.py - v1.01

Copyright 2020 Alec Dee - MIT license - SPDX: MIT
alecdee.github.io - akdee144@gmail.com

--------------------------------------------------------------------------------
Integers modulo n, for n>=1.
If gcd(a,n)=1, then a^k=a^(k%phi(n)) mod n.
"""

class IntMod(object):
	n=0

	def __init__(self,x=None,n=None):
		if isinstance(x,IntMod):
			self.x=x.x
			self.n=x.n
			return
		if n!=None:
			self.n=n
		else:
			n=self.n
		if x!=None:
			x=x%n
			try:
				if x<0:
					x+=n
			except:
				pass
			self.x=x
		else:
			self.x=0

	def __int__(self):
		return self.x

	def __str__(self):
		return str(self.x)

	def __eq__(self,b):
		if isinstance(b,IntMod):
			return self.x==b.x and self.n==b.n
		return False

	def __ne__(self,b):
		return not self==b

	def inv(self):
		# Works for n=1 => 0^-1=0.
		n=self.n
		b0,b1=0,1
		r0,r1=n,self.x%n
		while r1:
			q=r0//r1
			r0,r1=r1,r0-q*r1
			b0,b1=b1,(b0-q*b1)%n
		if r0!=1:
			raise ZeroDivisionError("Cannot invert "+str(self.x)+" mod "+str(self.n))
		return b0

	def __add__(a,b):
		return IntMod(a.x+b.x,a.n)

	def __iadd__(a,b):
		a.x=(a.x+b.x)%a.n
		return a

	def __sub__(a,b):
		return IntMod(a.x-b.x,a.n)

	def __isub__(a,b):
		n=a.n
		a.x=(n+a.x-b.x)%n
		return a

	def __neg__(a):
		return IntMod(-a.x,a.n)

	def __mul__(a,b):
		try:
			b=int(b)
		except:
			return NotImplemented
		return IntMod(a.x*b,a.n)

	def __imul__(a,b):
		a.x=(a.x*b.x)%a.n
		return a

	def __truediv__(a,b):
		return IntMod(a.x*b.inv(),a.n)

	def __itruediv__(a,b):
		a.x=(a.x*b.inv())%a.n
		return a

	def __rtruediv__(a,b):
		return b*a.inv()

	__div__=__truediv__
	__idiv__=__itruediv__
	__rdiv__=__rtruediv__
	__floordiv__=__truediv__
	__ifloordiv__=__itruediv__
	__rfloordiv__=__rtruediv__

	def __pow__(self,exp):
		mul,x,n=1,self.x,self.n
		if exp<0:
			exp=-exp
			x=self.inv()
		if abs(exp-0.5)<1e-10:
			for i in range(n):
				if i*i%n==x:
					return IntMod(i,n)
			raise ZeroDivisionError("Cannot find root {0} mod {1}".format(x,n))
		while exp:
			if exp&1:
				mul=(mul*x)%n
			exp>>=1
			x=(x*x)%n
		return IntMod(mul,n)

if __name__=="__main__":
	x=IntMod(13,107)
	print(x)
	print(x.inv())
	print(x*2)
	print(x//x)
	z=IntMod(3,1)
	print(z.inv())
	z=IntMod(3,107)
	print(z**-0.5)

