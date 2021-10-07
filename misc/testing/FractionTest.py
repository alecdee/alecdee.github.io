"""
FractionTest.py - v1.01

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
from random import randrange
from fractions import Fraction as fr
from time import time
sys.path.insert(0,"../")
from Fraction import Fraction
from Math import *

def FractionApproxTest():
	print("Testing bounded fraction approximation.")
	from time import time
	#Use powers of 2 to bound the random values to help special conditions occur.
	trials=100000
	maxpot=14
	t0=time()
	for trial in range(trials):
		#Generate the initial fraction.
		pot=1<<(randrange(maxpot+1))
		n0=randrange(-pot,pot+1)
		pot=1<<(randrange(maxpot+1))
		d0=randrange(pot)+1
		while gcd(n0,d0)!=1:
			n0+=1
		f0=Fraction(n0,d0)
		#Generate the denominator bounds.
		pot=1<<(randrange(maxpot+1))
		dmin=randrange(pot)+1
		pot=1<<(randrange(maxpot+1))
		dmax=dmin+randrange(pot)
		#Calculate the approximate values.
		f1=Fraction.approx(f0,dmin,dmax)
		err2,f2=None,None
		for i in range(dmin,dmax+1):
			if n0<0:
				n=-((-2*n0*i+d0)//(2*d0))
			else:
				n=(2*n0*i+d0)//(2*d0)
			f=Fraction(n,i)
			err=abs(f-f0)
			if err2==None or err2>err:
				err2=err
				f2=f
		f=Fraction(f2.n-1,f2.d)
		if abs(f.n)<abs(f2.n) and abs(f-f0)==err2:
			f2=f
		f=Fraction(f2.n+1,f2.d)
		if abs(f.n)<abs(f2.n) and abs(f-f0)==err2:
			f2=f
		if f1!=f2:
			print("bnd: "+str(dmin)+","+str(dmax))
			print(float(f0),f0)
			print(float(f1),f1)
			print(float(f2),f2)
			print("Not best approximation.")
			exit()
	print("Time:",time()-t0)
	print("Passed.")

def FractionChangeTest():
	print("Testing fraction change of denominator.")
	trials=10000
	for trial in range(trials):
		n0=randrange(10000)
		d0=randrange(10000)+1
		d1=randrange(10000)+1
		f0=Fraction(n0,d0)
		f1=f0.changeden(d1)
		minerr=abs(f1-f0)
		n2=(n0*d1)//d0
		for i in range(-2,3):
			f2=Fraction(n2+i,d1)
			err=abs(f2-f0)
			if minerr>err:
				print("Not minimum error.")
				print("f0: "+str(f0))
				print("f1: "+str(f1))
				print("f2: "+str(f2))
				exit()
	print("Passed.")

if __name__=="__main__":
	FractionApproxTest()
	FractionChangeTest()

