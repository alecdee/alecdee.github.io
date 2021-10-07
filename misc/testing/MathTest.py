"""
MathTest.py - v1.01

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

import math,sys
from random import randrange,seed
from time import time
sys.path.insert(0,"../")
from Math import *

#-------------------------------------------------------------------------------
#GCD
#-------------------------------------------------------------------------------

def gcdtest():
	print("Testing GCD and LCM.")
	#Test 2-parameter solutions.
	trials=10000
	maxval=100
	for trial in range(trials):
		a=randrange(-maxval,maxval+1)
		b=randrange(-maxval,maxval+1)
		#Test GCD.
		d=0
		for i in range(max(abs(a),abs(b)),0,-1):
			if a%i==0 and b%i==0:
				d=i
				break
		if d!=gcd(a,b):
			print("gcd("+str(a)+","+str(b)+")="+str(gcd(a,b))+"!="+str(d))
			exit()
		#Test LCM.
		m=0
		for i in range(1,abs(a*b)+1):
			if i%a==0 and i%b==0:
				m=i
				break
		if m!=lcm(a,b):
			print("lcm("+str(a)+","+str(b)+")="+str(lcm(a,b))+"!="+str(m))
			exit()
	#Test n-parameter solutions.
	maxn=10
	for trial in range(trials):
		n=randrange(maxn)+1
		#Test GCD.
		mul=randrange(-32,33)
		arr=[randrange(maxval)*mul for i in range(n)]
		d=gcd(arr)
		if d<0:
			print("negative gcd(arr)")
			exit()
		allz=min(arr)==0 and max(arr)==0
		if (d==0)!=allz:
			print("gcd("+str(arr)+")="+str(d)+"!="+str(allz))
			exit()
		if mul!=0 and d%mul!=0:
			print("gcd%mul!=0")
			exit()
		if d!=0:
			for a in arr:
				if a%d!=0:
					print("arr%gcd!=0")
					exit()
		if n==2 and d!=gcd(arr[0],arr[1]):
			print("gcd(arr)!=gcd(a0,a1)")
			exit()
		#Test LCM.
		arr=[randrange(-maxval,maxval+1) for i in range(n)]
		m=lcm(arr)
		if m<0:
			print("negative lcm(arr)")
			exit()
		hasz=0 in arr
		if (m==0)!=hasz:
			print("lcm("+str(arr)+")="+str(m)+"!=0")
			exit()
		for a in arr:
			if a and m%a!=0:
				print("lcm%arr!=0")
				exit()
		if n==2 and m!=lcm(arr[0],arr[1]):
			print("lcm(arr)!=lcm(a0,a1)")
			exit()
	print("Passed.")

#-------------------------------------------------------------------------------
#Modulo Arithmetic
#-------------------------------------------------------------------------------

def modtest():
	print("Testing modulo operations.")
	trials=100000
	for trial in range(trials):
		if trial<100*100:
			x=trial%100-50
			mod=trial//100-50
		else:
			x=randrange(-10000,10001)
			mod=randrange(-10000,10001)
		if mod==0:
			continue
		#Modular inverse.
		y=modinv(x,mod)
		hasinv=mod and gcd(x,mod)==1
		if hasinv:
			if y==None:
				print("x should have inverse:",x,mod)
				exit()
			if y<0:
				print("invalid inverse:",y,x,mod)
				exit()
			if (x*y)%mod!=1%mod:
				print("not inverse:",y,x,mod)
				exit()
		elif y!=None:
			print("x should not have inverse:",x,mod)
			exit()
		#Exponential testing.
		exp=randrange(-1000,1001)
		ans=1
		for i in range(abs(exp)):
			ans=(ans*x)%abs(mod)
		if exp<0:
			ans=modinv(ans,mod)
		calc=powmod(x,exp,mod)
		if calc!=ans:
			print("invalid exponential:",x,exp,mod,ans,calc)
			exit()
		#Primitive root testing.
		if mod>=0 and mod<1000:
			mod=abs(mod)
			root=primitiveroot(mod)
			if root!=None:
				phi=coprime(mod)
				used=[0]*mod
				x=int(mod>1)
				for i in range(phi):
					if used[x]:
						print("not root:",root,mod)
						exit()
					used[x]=1
					x=(x*root)%mod
	print("Passed.")

def logmod0test():
	#If a^x=0 mod n has a solution, then x<=floor(log2(n)). Hence, m=ceil(sqrt(n))>x
	#is sufficient except for n=4,8,16.
	print("Testing a^x=0 bounds.")
	for n in range(1,257):
		maxp=0
		for a in range(n):
			b=1%n
			for p in range(n):
				if b==0:
					maxp=max(maxp,p)
					break
				b=(b*a)%n
		log2=int(math.log(n)/math.log(2))
		if maxp>log2:
			print("log2:",n,maxp,log2)
			exit()
		m=intsqrt(n)
		m+=(m*m<n)+(n==4)+(n==8)+(n==16)
		if maxp>=m:
			print("sqrt:",n,maxp,m)
			exit()
	print("Passed.")

def logcycletest():
	#a^x=0 mod n has a solution
	#If a^x=0 mod n has a solution, then x<=floor(log2(n)). Hence, m=ceil(sqrt(n))>x
	#is sufficient except for n=4,8,16.
	print("Testing a^x=0 bounds.")
	for n in range(2,16):
		#phi=coprime(n)
		arr=[]
		for a in range(n):
			if gcd(a,n)==1:
				continue
			#inv,d=modinv2(a,n)
			#print(str(a),inv,d,powmod(a,phi,n),(a*inv)%n)
			table=[0]*n
			b=1
			loop=0
			while True:
				if table[b]:
					break
				table[b]=1
				b=(b*a)%n
				loop+=1
			arr.append(loop)
		print(n,arr)
	print("Passed.")

def logmodtest():
	print("Testing modular logarithm.")
	for n in range(1,257):
		for a in range(n):
			if gcd(a,n)!=1:
				continue
			table=[None]*n
			mul=1%n
			for lg in range(n):
				if table[mul]==None:
					table[mul]=lg
				mul=(mul*a)%n
			for b in range(n):
				if logmod(b,a,n)!=table[b]:
					print("not log: "+str(a)+"^x="+str(b)+" mod "+str(n))
					print(logmod(b,a,n))
					print(table[b])
					exit()
	print("Passed.")

#-------------------------------------------------------------------------------
#Primality Testing
#-------------------------------------------------------------------------------

def isprime0(n):
	if n<2:
		return False
	root=intsqrt(n)
	for p in range(2,root+1):
		if n%p==0:
			return False
	return True

def isprime1(n):
	#Miller-Rabin. Requires odd n>3.
	if n<=3:
		return n>=2
	if n%2==0:
		return False
	#Assuming the GRH, test all witnesses in [2,2*ln(n)^2].
	ln=math.log(n)
	witnesses=range(2,int(2*ln*ln)+1)
	#Write n-1 as d*2^s for odd d. Take s=-1 to simplify a later calculation.
	d=n-1
	s=-1
	while (d&1)==0:
		d>>=1
		s+=1
	for a in witnesses:
		#Let x=a^d mod n. If x=+-1 mod n, skip.
		x,exp,pot=1,d,a%n
		if pot<2 or pot==n-1:
			continue
		while exp:
			if exp&1:
				x=(x*pot)%n
			exp>>=1
			pot=(pot*pot)%n
		if x==1 or x==n-1:
			continue
		#Calculate a^(d*2*r) for r in [0,s-1).
		#Note we already have x=a^d and s-=1.
		for r in range(s):
			x=(x*x)%n
			if x==1:
				return False
			if x==n-1:
				break
		else:
			return False
	#We have found a prime.
	return True

def isprimelog(bits):
	#Calculate 1.rem for rem={1,2,...,2^bits}.
	def approx2(n,bits,table):
		log2=n.bit_length()
		frac=(n>>(log2-1-bits))&((1<<bits)-1)
		log2+=float(table[frac])
		return log2
	pot=1<<bits
	table=[0]*pot
	for i in range(pot):
		x=float(pot+i+1)/pot
		x=math.log(x)/math.log(2)-1
		table[i]="{0:0.6f}".format(x)
	dif=0
	for i in range(pot,10000):
		approx=approx2(i,bits,table)
		real=math.log(i)/math.log(2)
		assert(approx>=real)
		dif+=approx-real
	dif/=10000-pot
	print(dif)
	con=math.log(2)/math.log(math.e)
	con*=con*2.0
	con="{0:0.6f}".format(con)
	for i in range(pot,10000):
		approx=approx2(i,bits,table)
		approx*=approx*float(con)
		real=math.log(i)
		real*=real*2.0
		assert(approx>=real)
		if real>0:
			dif+=approx/real
	dif/=10000-pot
	print(dif)
	print("table=("+",".join(table)+")")
	print("log2=n.bit_length()")
	print("frac=(n>>(log2-"+str(1+bits)+"))&"+str((1<<bits)-1))
	print("log2+=table[frac]")
	print("log2*=log2*"+con)
	print("witnesses=range(2,int(log2)+1)")

def isprimelogtest():
	print("Testing logarithm approximation.")
	def approx(n):
		table=(
			-0.912537,-0.830075,-0.752072,-0.678072,-0.607683,-0.540568,
			-0.476438,-0.415037,-0.356144,-0.299560,-0.245112,-0.192645,
			-0.142019,-0.093109,-0.045804, 0.000000
		)
		log2=n.bit_length()
		frac=(n>>(log2-5))&15
		log2+=table[frac]
		log2*=log2*0.960906
		return int(log2)+1
	def real(n):
		ln=math.log(n)
		return int(2*ln*ln)+1
	trials=1000000
	for trial in range(16,trials):
		a=approx(trial)
		r=real(trial)
		assert(a>=r)
	print("Passed.")

def isprime2(n):
	#Miller-Rabin. Requires odd n>3.
	if n<=3:
		return n>=2
	if n%2==0:
		return False
	#Deterministic witnesses discovered by Steve Worley, Wojciech Izykowski, Marcin
	#Panasiuk, and Jim Sinclair.
	if n<341531:
		witnesses=(9345883071009581737,)
	elif n<1050535501:
		witnesses=(336781006125,9639812373923155)
	elif n<350269456337:
		witnesses=(4230279247111683200,14694767155120705706,16641139526367750375)
	elif n<55245642489451:
		witnesses=(2,141889084524735,1199124725622454117,11096072698276303650)
	elif n<7999252175582851:
		witnesses=(2,4130806001517,149795463772692060,186635894390467037,3967304179347715805)
	elif n<585226005592931977:
		witnesses=(2,123635709730000,9233062284813009,43835965440333360,761179012939631437,1263739024124850375)
	elif n<18446744073709551616:
		witnesses=(2,325,9375,28178,450775,9780504,1795265022)
	else:
		#Assuming the GRH, test all witnesses in [2,2*ln(n)^2]. We take a rounded up
		#approximation of log2(n) which yields 2*ln(n)^2=2*(log2(n)*log2(2)/log2(e))^2=
		#0.960906*log2(n)^2.
		table=(
			-0.912537,-0.830075,-0.752072,-0.678072,-0.607683,-0.540568,
			-0.476438,-0.415037,-0.356144,-0.299560,-0.245112,-0.192645,
			-0.142019,-0.093109,-0.045804, 0.000000
		)
		log2=n.bit_length()
		frac=(n>>(log2-5))&15
		log2+=table[frac]
		log2*=log2*0.960906
		witnesses=range(2,int(log2)+1)
	#Write n-1 as d*2^s for odd d. Take s=-1 to simplify a later calculation.
	d,s=n-1,-1
	while (d&1)==0:
		d>>=1
		s+=1
	for a in witnesses:
		#Let x=a^d mod n. If x=+-1 mod n, skip.
		x=a%n
		if x<2 or x==n-1:
			continue
		pot,exp=x,d
		while exp>1:
			exp>>=1
			pot=(pot*pot)%n
			if exp&1:
				x=(x*pot)%n
		if x==1 or x==n-1:
			continue
		#Calculate a^(d*2*r) for r in [0,s-1).
		#Note we already have x=a^d and s-=1.
		for r in range(s):
			x=(x*x)%n
			if x==1:
				return False
			if x==n-1:
				break
		else:
			return False
	#We have found a prime.
	return True

def isprimefilter(cnt):
	def isp(n):
		if n<2:
			return False
		i=2
		while i*i<=n:
			if n%i==0:
				return False
			i+=1
		return True
	def canfilter(n,plist):
		for p in plist:
			if p>=n:
				return True
			if n%p==0:
				return True
		return isp(n)
	plist=[]
	i=2
	while len(plist)<cnt:
		if isp(i):
			plist.append(i)
		i+=1
	lim=plist[-1]*plist[-1]
	while canfilter(lim,plist):
		lim+=1
	print("plist=("+",".join(map(str,plist))+")")
	print("if n<"+str(lim)+":")

def isprime3(n):
	#Miller-Rabin primality test. Requires odd n>3.
	if n<2:
		return False
	#Perform trial division.
	plist=(2,3,5,7,11,13,17,19,23,29,31,37,41,43,47,53)
	for p in plist:
		if p>=n:
			return True
		if n%p==0:
			return False
	if n<3481:
		return True
	elif n<18446744073709551616:
		#Deterministic witnesses discovered by Jim Sinclair.
		witnesses=(2,325,9375,28178,450775,9780504,1795265022)
	else:
		#Assuming the GRH, test all witnesses in [2,2*ln(n)^2]. We use a rounded up
		#approximation of log2(n) and take 2*ln(n)^2=2*(log2(n)*log2(2)/log2(e))^2=
		#0.960906*log2(n)^2.
		table=(
			-0.912537,-0.830075,-0.752072,-0.678072,-0.607683,-0.540568,
			-0.476438,-0.415037,-0.356144,-0.299560,-0.245112,-0.192645,
			-0.142019,-0.093109,-0.045804, 0.000000
		)
		log2=n.bit_length()
		frac=(n>>(log2-5))&15
		log2+=table[frac]
		log2*=log2*0.960906
		witnesses=range(2,int(log2)+1)
	#Write n-1 as d*2^s for odd d. Take s=-1 to simplify a later calculation.
	d,s=n-1,-1
	while (d&1)==0:
		d>>=1
		s+=1
	for a in witnesses:
		#Let x=a^d mod n. If x=+-1 mod n, skip.
		x=a%n
		if x<2 or x==n-1:
			continue
		pot,exp=x,d
		while exp>1:
			exp>>=1
			pot=(pot*pot)%n
			if exp&1:
				x=(x*pot)%n
		if x==1 or x==n-1:
			continue
		#Calculate a^(d*2*r) for r in [0,s-1).
		#Note we already have x=a^d and s-=1.
		for r in range(s):
			x=(x*x)%n
			if x==1:
				return False
			if x==n-1:
				break
		else:
			return False
	#We have found a prime.
	return True

def primetest():
	print("Testing primality test.")
	func=isprime
	table=primetable(10000000)
	for i in range(len(table)):
		if table[i]!=func(i):
			print("isprime failed:",i)
			exit()
	special=(
		341531,1050535501,350269456337,55245642489451,7999252175582851,
		585226005592931977,18446744073709551616
	)
	trials=100000
	refresh=128
	for i in range(trials):
		if (i%refresh)==0:
			k=i//refresh
			if k<len(special):
				n=special[k]-refresh//2
			else:
				n=randrange(66)
				n=randrange(1<<n)
		if func(n)!=isprime1(n):
			print("false prime 0",n)
			exit()
		n+=1
	print("Passed.")

def primespeed():
	#prime2: 15.725976
	#prime3:
	#   1: 15.389337
	#  16: 14.801436
	#  31: 14.783841
	#  62: 14.862957
	# 125: 14.864299
	# 250: 14.904531
	# 500: 15.243685
	#1000: 15.824741
	print("Testing prime testing speed.")
	trials=1000000
	refresh=127
	seed(0)
	t0=time()
	for trial in range(trials):
		if (trial&refresh)==0:
			n=randrange(66)
			n=randrange(1<<n)
		isprime(n)
		n+=1
	print("time:",time()-t0)
	print("Passed.")

#-------------------------------------------------------------------------------
#Prime Sieves
#-------------------------------------------------------------------------------

def primetable1(n):
	#Sieve of Atkin.
	table=bytearray(n)
	x,x2=1,1
	while x2<n:
		y,y2=1,1
		while y2<n:
			z=4*x2+y2
			m=z%12
			if z<n and (m==1 or m==5):
				table[z]^=1
			z-=x2
			if z<n and z%12==7:
				table[z]^=1
			z-=2*y2
			if z<n and x>y and z%12==11:
				table[z]^=1
			y2+=2*y+1
			y+=1
		x2+=2*x+1
		x+=1
	i,i2=5,25
	while i2<n:
		for j in range(i2,n,i2):
			table[j]=0
		i2+=2*i+1
		i+=1
	return table

#-------------------------------------------------------------------------------
#Euler Totient
#-------------------------------------------------------------------------------

def primeskip():
	primes=(2,3,5,7)
	pnext=[0]*(primes[-1]+1)
	for i in range(len(pnext)):
		if not isprime(i):
			continue
		j=i+1
		while not isprime(j):
			j+=1
		pnext[i]=j
	mul=1
	for p in primes:
		mul*=p
	#Start with the smallest prime not in primes[], then loop around mod mul.
	start=pnext[-1]
	pskip=[]
	i=start
	while True:
		next=(i+1)%mul
		while gcd(next,mul)!=1:
			next=(next+1)%mul
		pskip.append((next-i+mul)%mul)
		i=next
		if i==start:
			break
	#print("pnext=("+",".join(map(str,pnext))+")")
	#print("pskip=("+",".join(map(str,pskip))+")")
	#print("mod=",len(pskip))
	#Create a linked list.
	next=1
	last=2
	s=""
	for p in pnext:
		if p:
			if s!="":
				s+=","
			s+="("+str(p-last)+","+str(next)+")"
			last=p
			next+=1
	nonprime=next-1
	for i,skip in enumerate(pskip):
		if i==len(pskip)-1:
			next=nonprime
		s+=",("+str(skip)+","+str(next)+")"
		next+=1
	print("pskip=("+s+")")
	#Create a linked list v2.
	next=1
	last=2
	s=""
	for p in pnext:
		if p:
			if s!="":
				s+=","
			s+=str(p-last)+","+str(next*2)
			last=p
			next+=1
	nonprime=next-1
	for i,skip in enumerate(pskip):
		if i==len(pskip)-1:
			next=nonprime
		s+=","+str(skip)+","+str(next*2)
		next+=1
	print("pskip=("+s+")")

def coprime0(n):
	count=0
	for i in range(1,n):
		if gcd(i,n)==1:
			count+=1
	return count

def coprime1(n):
	if n<2:
		return 0
	count=1
	fact=2
	while fact<=n:
		if n%fact==0:
			k=0
			while n%fact==0:
				n//=fact
				k+=1
			count*=(fact-1)*(fact**(k-1))
		fact+=1
	return count

def coprime2(n):
	pnext=(0,0,3,5,0,7)
	pskip=(4,2,4,2,4,6,2,6)
	p,skip=2,0
	count=n-(n==1)
	while p<=n:
		if n%p==0:
			n=n//p
			while n%p==0:
				n//=p
			count-=count//p
		if p>=7:
			p+=pskip[skip&7]
			skip+=1
		else:
			p=pnext[p]
	return count

def coprime3(n):
	#pypy   :  3.114576
	#python3: 60.622786
	pnext=(0,0,3,5,0,7)
	pskip=(4,2,4,2,4,6,2,6)
	p,skip=2,0
	count=n-(n==1)
	while p*p<=n:
		if n%p==0:
			n=n//p
			while n%p==0:
				n//=p
			count-=count//p
		if p>=7:
			p+=pskip[skip]
			skip=(skip+1)&7
		else:
			p=pnext[p]
	if n>1:
		count-=count//n
	return count

def coprime4(n):
	#pypy   :  3.047732
	#python3: 56.476591
	pnext=(0,0,3,5,0,7,0,11,0,0,0,13,0,17,0,0,0,19)
	pskip=(
		4,6,2,6,4,2,4,2,4,6,2,6,4,2,4,2,4,6,2,6,4,2,4,2,4,8,6,4,2,4,2,4,
		6,2,6,4,2,4,2,4,6,2,10,2,4,2,4,6,2,6,6,4,2,4,6,2,6,4,2,4,2,4,6,2,
		6,4,2,4,6,6,2,6,4,2,4,2,10,2,6,4,2,4,2,4,6,2,6,4,2,4,2,4,6,8,4,2,
		4,2,4,6,2,6,4,2,4,2,4,6,2,6,4,2,4,2,4,6,2,6,4,6,2,4,6,2,6,4,2,6
	)
	p,skip=2,0
	count=n-(n==1)
	while p*p<=n:
		if n%p==0:
			n=n//p
			while n%p==0:
				n//=p
			count-=count//p
		if p>=19:
			p+=pskip[skip]
			skip=(skip+1)&127
		else:
			p=pnext[p]
	if n>1:
		count-=count//n
	return count

def coprime5(n):
	#pypy   :  2.746725
	#python3: 43.530111
	pskip=(
		(1,1),(2,2),(2,3),(4,4),(2,5),(4,6),(2,7),(4,8),(6,9),(2,10),(6,11),(4,12),(2,13),(4,14),
		(6,15),(6,16),(2,17),(6,18),(4,19),(2,20),(6,21),(4,22),(6,23),(8,24),(4,25),(2,26),(4,27),
		(2,28),(4,29),(8,30),(6,31),(4,32),(6,33),(2,34),(4,35),(6,36),(2,37),(6,38),(6,39),(4,40),
		(2,41),(4,42),(6,43),(2,44),(6,45),(4,46),(2,47),(4,48),(2,49),(10,50),(2,51),(10,4)
	)
	p,skip=2,pskip[0]
	count=n-(n==1)
	while p*p<=n:
		if n%p==0:
			n=n//p
			while n%p==0:
				n//=p
			count-=count//p
		p+=skip[0]
		skip=pskip[skip[1]]
	if n>1:
		count-=count//n
	return count

def coprime6(n):
	#pypy   :  3.207849
	#python3: 43.906026
	pskip=(
		1,2,2,4,2,6,4,8,2,10,4,12,2,14,4,16,6,18,2,20,6,22,4,24,2,26,4,
		28,6,30,6,32,2,34,6,36,4,38,2,40,6,42,4,44,6,46,8,48,4,50,2,52,4,
		54,2,56,4,58,8,60,6,62,4,64,6,66,2,68,4,70,6,72,2,74,6,76,6,78,4,
		80,2,82,4,84,6,86,2,88,6,90,4,92,2,94,4,96,2,98,10,100,2,102,10,8
	)
	p,skip=2,0
	count=n-(n==1)
	while p*p<=n:
		if n%p==0:
			n=n//p
			while n%p==0:
				n//=p
			count-=count//p
		p+=pskip[skip]
		skip=pskip[skip+1]
	if n>1:
		count-=count//n
	return count

def coprimetest():
	print("Testing coprime counting.")
	trials=10000
	for trial in range(trials):
		cnt0=coprime0(trial)
		cnt1=coprime(trial)
		if cnt1!=cnt0:
			print("bad count:",trial,cnt0,cnt1)
			exit()
	print("Passed.")

def coprimespeed():
	trials=10000
	seed(0)
	t0=time()
	for trial in range(trials):
		coprime(randrange(2**40))
	print("coprime time:",time()-t0)

def primefactortest():
	print("Testing prime factoring.")
	trials=10000
	table=primetable(100000)
	primes=[0]*sum(table)
	cnt=0
	for p,t in enumerate(table):
		if t:
			primes[cnt]=p
			cnt+=1
	for trial in range(trials):
		ans=[primes[randrange(cnt)] for i in range(3)]
		num=1
		for p in ans:
			num*=p
		calc=primefactors(num)
		ans=sorted(list(set(ans)))
		if ans!=calc:
			print("error factoring:",num)
			print("ans :",ans)
			print("calc:",calc)
			exit()
	print("Passed.")

#-------------------------------------------------------------------------------
#Factorization
#-------------------------------------------------------------------------------

def findfactor0(n):
	#Trial division for p<=sqrt(n).
	if n<2:
		return 1
	p=2
	while p*p<=n:
		if n%p==0:
			return p
		p+=1
	return n

def findfactor1(n):
	#Trial division for p<=sqrt(n).
	if n<2:
		return 1
	pskip=(
		1,2,2,4,2,6,4,8,2,10,4,12,2,14,4,16,6,18,2,20,6,22,4,24,2,26,4,
		28,6,30,6,32,2,34,6,36,4,38,2,40,6,42,4,44,6,46,8,48,4,50,2,52,4,
		54,2,56,4,58,8,60,6,62,4,64,6,66,2,68,4,70,6,72,2,74,6,76,6,78,4,
		80,2,82,4,84,6,86,2,88,6,90,4,92,2,94,4,96,2,98,10,100,2,102,10,8
	)
	p,skip=2,0
	while p*p<=n:
		if n%p==0:
			return p
		p+=pskip[skip]
		skip=pskip[skip+1]
	return n

def findfactor2(n):
	#Trial division for p<=sqrt(n).
	if n<2:
		return 1
	pskip=(
		1,2,2,4,2,6,4,8,2,10,4,12,2,14,4,16,6,18,2,20,6,22,4,24,2,26,4,
		28,6,30,6,32,2,34,6,36,4,38,2,40,6,42,4,44,6,46,8,48,4,50,2,52,4,
		54,2,56,4,58,8,60,6,62,4,64,6,66,2,68,4,70,6,72,2,74,6,76,6,78,4,
		80,2,82,4,84,6,86,2,88,6,90,4,92,2,94,4,96,2,98,10,100,2,102,10,8
	)
	r=intsqrt(n)
	p,skip=2,0
	while p<=r:
		if n%p==0:
			return p
		p+=pskip[skip]
		skip=pskip[skip+1]
	return n

def findfactor3(n):
	#Pollard's Rho.
	if n<2:
		return 1
	if isprime(n):
		return n
	k=2
	while True:
		x,d=k,1
		cycle=2
		while d==1:
			x0,c=x,0
			while c<cycle and d==1:
				x=(x*x+1)%n
				d=gcd(x-x0,n)
				c+=1
			cycle+=cycle
		if d!=n:
			return d
		k+=1

def findfactor4(n):
	#Shanks square forms.
	def issquare(n):
		root=intsqrt(n)
		return root*root==n
	if n<2:
		return 1
	if isprime(n):
		return n
	if issquare(n):
		return intsqrt(n)
	print(n)
	P=[0]*100000
	Q=[0]*100000
	k=1
	while True:
		P[0]=intsqrt(k*n)
		Q[0]=1
		Q[1]=k*n-P[0]*P[0]
		i=1
		while True:
			b=(P[0]+P[i-1])//Q[i]
			P[i]=b*Q[i]-P[i-1]
			Q[i+1]=Q[i-1]+b*(P[i-1]-P[i])
			assert(P[i]>=0)
			assert(Q[i+1]>=0)
			if issquare(Q[i]):
				break
			i+=1
		Q[0]=intsqrt(Q[i])
		b=(P[0]-P[i-1])//Q[0]
		P[0]=b*Q[0]+P[i-1]
		Q[1]=(k*n-P[0]*P[0])//Q[0]
		i=1
		while True:
			b=(P[0]+P[i-1])//Q[i]
			P[i]=b*Q[i]-P[i-1]
			Q[i+1]=Q[i-1]+b*(P[i-1]-P[i])
			if P[i]==P[i-1]:
				break
			i+=1
		d=gcd(P[i],n)
		if d>1 and d<n:
			return d
		k+=1

def findfactortest():
	print("Testing integer factorization.")
	trials=100000
	for trial in range(trials):
		n=randrange(10000000)
		if trial<100:
			n=trial-50
		fact=findfactor4(n)
		isp=isprime(n)
		if fact==1 and n>1:
			print("trivial factor:",fact,n)
			exit()
		if fact<1 or (fact>n and n>0):
			print("factor out of bounds:",fact,n)
			exit()
		if n%fact!=0:
			print("not a factor:",n,"%",fact,"=",n%fact)
			exit()
		if n==fact and isp==False and n!=1:
			print("no factor found:",n)
			exit()
		if n!=fact and isp==True:
			print("prime factored:",fact,n)
			exit()
	print("Passed.")

def findfactorspeed():
	print("Testing integer factorization speed.")
	seed(0)
	trials=1000000
	base=[1]
	for pot in range(21):
		p=1<<pot
		while len(base)<(pot+1)*10:
			if isprime(p) and not (p in base):
				base.append(p)
			p+=1
	bases=len(base)
	t0=time()
	for trial in range(trials):
		n=base[randrange(bases)]
		n*=base[randrange(bases)]
		n*=base[randrange(bases)]
		findfactor4(n)
	print("Time:",time()-t0)
	print("Passed.")

#-------------------------------------------------------------------------------
#Linear Diophantine Equations
#-------------------------------------------------------------------------------

def diotest():
	print("Testing Linear Diophantine solver.")
	def error(a,n,ret):
		print("a  :",a)
		print("n  :",n)
		print("ret:",ret)
		exit()
	trials=10000000
	for trial in range(trials):
		l=randrange(20)
		#Check special cases when a=0's or n=0.
		sol=[0]*(l+1)
		a=[0]*l
		ret=diophantine(a)
		if ret!=sol:
			print("dio(a)!=sol")
			error(a,None,ret)
		if diophantine(a,0)!=sol:
			print("dio(a,0)!=sol")
			error(a,None,ret)
		if diophantine(a,1)!=None:
			print("dio(a,1)!=None")
			error(a,None,ret)
		a=tuple([randrange(-25,26) for i in range(l)])
		for b in a:
			sol[l]=gcd(sol[l],b)
		ret=diophantine(a,0)
		if ret!=sol:
			print("ret!=sol")
			error(a,0,ret)
		#Check general cases for any a and n.
		a=tuple([randrange(-2500,2501) for i in range(l)])
		d=0
		for b in a:
			d=gcd(d,b)
		n=randrange(-20000,20001)
		if randrange(2):
			n=[0,None][randrange(2)]
		ret=diophantine(a,n)
		if n and (d==0 or n%d!=0):
			if ret!=None:
				print("ret!=None")
				error(a,n,ret)
		else:
			if ret[l]!=d:
				print("dio!=gcd",ret[l],d)
				error(a,n,ret)
			if n==None:
				n=d
			sum=0
			for i in range(l):
				sum+=ret[i]*a[i]
			if sum!=n:
				print("sum!=n")
				error(a,n,ret)
	print("Passed.")

def diopostest():
	print("Testing Positive Linear Diophantine Solver.")
	def error(a,n,ret):
		print("a:",a)
		print("n:",n)
		print("x:",x)
		exit()
	trials=1000000
	for trial in range(trials):
		l=randrange(1,3)
		a=[randrange(-50,51) for i in range(l)]
		n=0
		for i in range(l):
			n+=a[i]*randrange(100)
		x=diopositive(a,n)
		if x==None:
			print("pos search")
			error(a,n,x)
		if min(x)<0:
			print("negative x")
			error(a,n,x)
		sum=0
		for i in range(l):
			sum+=a[i]*x[i]
		if sum!=n:
			print("sum!=n",sum,n)
			error(a,n,x)
	#Test (a-1)*(b-1) bound.
	trials=10000
	maxtest=1000
	for trial in range(trials):
		a=randrange(100)+1
		b=randrange(100)+1
		d=gcd(a,b)
		sol=[0]*maxtest
		sol[0]=1
		for i in range(maxtest-a):
			if sol[i]:
				sol[i+a]=1
		for i in range(maxtest-b):
			if sol[i]:
				sol[i+b]=1
		bnd=(a-1)*(b-1)
		for i in range(0,maxtest,d):
			if sol[i]==0 and i>=bnd:
				print("impossible solution")
				exit()
	print("Passed.")

#-------------------------------------------------------------------------------
#Sqrt
#-------------------------------------------------------------------------------

def intsqrt0(n):
	if n==0:
		return 0
	bit=2<<int(math.floor(math.log(n,2)*0.5))
	root=0
	while bit:
		next=root+bit
		if next*next<=n:
			root=next
		bit>>=1
	return root

def intsqrt1(n):
	bit,sqr=1,4
	while sqr<=n:
		sqr<<=2
		bit<<=1
	root=0
	while bit:
		next=root+bit
		if next*next<=n:
			root=next
		bit>>=1
	return root

def intsqrt2(n):
	#(root+bit)*(root+bit)<=n
	#root*root+2*root*bit+bit*bit<=n
	#sqr+root<<(bit+1)+1<<(2*bit)<=n
	#root<<(bit+1)+1<<(2*bit)<=n-sqr
	#root<<(bit+1)+1<<(2*bit)<=n'
	#(root<<1+1<<bit)<<bit<=n'
	#
	#Find the largest k such that 4^k<=n.
	one,stop=1,n>>2
	while one<=stop:
		one<<=2
	#We only need to track n'=n-sqr=n-root^2. Then determine if the increment of
	#(root+one)^2 will put the square over n.
	root=0
	while one:
		inc=root+one
		root>>=1
		if inc<=n:
			root+=one
			n-=inc
		one>>=2
	return root

def sqrttest():
	print("Testing square root finder.")
	trials=1000000
	for trial in range(trials):
		n=trial
		if trial>trials//2:
			n=randrange(2**256)
		root=intsqrt(n)
		if root<0:
			print("negative root:",root,n)
			exit()
		if root*root>n:
			print("root too large:",root,n)
			exit()
		if (root+1)*(root+1)<=n:
			print("root too small:",root,n)
			exit()
	print("Passed.")

def sqrtspeed():
	seed(0)
	trials=1000000
	t0=time()
	for trial in range(trials):
		n=randrange(2**256)
		root=intsqrt(n)
	print("time:",time()-t0)

#-------------------------------------------------------------------------------
#Divisors
#-------------------------------------------------------------------------------

def sumdiv0(n,k):
	sum=0
	for i in range(1,n+1):
		if n%i==0:
			sum+=i**k
	return sum

def sumdiv1(n,k):
	#4.198583
	sum=0
	for i in range(1,n+1):
		d=n//i
		if d<i:
			break
		if n%i==0:
			sum+=i**k
			if d<=i:
				break
			sum+=d**k
	return sum

def sumdiv2(n,k):
	#pypy   :  13.368482
	#python3: 195.855770
	pskip=(
		1,2,2,4,2,6,4,8,2,10,4,12,2,14,4,16,6,18,2,20,6,22,4,24,2,26,4,
		28,6,30,6,32,2,34,6,36,4,38,2,40,6,42,4,44,6,46,8,48,4,50,2,52,4,
		54,2,56,4,58,8,60,6,62,4,64,6,66,2,68,4,70,6,72,2,74,6,76,6,78,4,
		80,2,82,4,84,6,86,2,88,6,90,4,92,2,94,4,96,2,98,10,100,2,102,10,8
	)
	p,skip=2,0
	n=abs(n)
	sum=int(n>0)
	while n>1:
		#If n>1 and p^2>n, then n is the last prime.
		if p*p>n:
			p=n
		if n%p==0:
			n=n//p
			#Take q=p^k.
			exp,pot,q=k,p,1
			while exp:
				if exp&1:
					q*=pot
				exp>>=1
				pot*=pot
			#Calculate the polynomial 1+q+q^2+...+q^a.
			x,poly=q,1+q
			while n%p==0:
				n//=p
				x*=q
				poly+=x
			sum*=poly
		p+=pskip[skip]
		skip=pskip[skip+1]
	return sum

def sumdivtest():
	print("Testing sum of divisors.")
	trials=100000
	for trial in range(trials):
		n,k=trial//8,trial%8
		calc0=sumdiv0(n,k)
		calc1=sumdiv(n,k)
		if calc1!=calc0:
			print("bad sum divisors:",n,k,calc0,calc1)
			exit()
	print("Passed.")

def sumdivspeed():
	trials=1000000
	seed(0)
	t0=time()
	for trial in range(trials):
		sumdiv(randrange(1000000000),randrange(8))
	print("time:",time()-t0)

#-------------------------------------------------------------------------------
#Misc
#-------------------------------------------------------------------------------

def fibtest():
	print("Testing Fibonacci calculator.")
	fib0,fib1=0,1
	for trial in range(100):
		fib=fibonacci(trial)
		if fib!=fib0:
			print("fib!=fib0:",fib,fib0)
			exit()
		fib0,fib1=fib1,fib0+fib1
	print("Passed.")

def quadresidues():
	#Let qn(n) be the count of quadratic residues mod n. That is,
	#qn(n)=|{i^2%n | i=0,1,...,n-1}|
	#For n=a*b, gcd(a,b)=1, qn(n)=qn(a)*qn(b)
	#For prime p, qn(2)=2, otherwise qn(p)=(p+1)/2.
	#There is a recursive formula for computing sq(n).
	minrat=1.0
	minn=1
	minused=[0]
	for n in range(1,129):
		used=[0]*n
		for i in range(n):
			used[(i*i)%n]=1
		cnt=sum(used)
		rat=cnt/n
		print(str(n).rjust(3),":",str(cnt).rjust(3),rat)
		if minrat>rat:
			minrat=rat
			minn=n
			minused=used
	print("min:")
	print(str(minn).rjust(3),":",minrat)
	print("("+",".join(map(str,minused))+")")

if __name__=="__main__":
	#gcdtest()
	#modtest()
	#logmod0test()
	#logcycletest()
	#logmodtest()
	#isprimefilter(32)
	#isprimelog(4)
	#isprimelogtest()
	#primetest()
	#primespeed()
	#primeskip()
	#coprimetest()
	#coprimespeed()
	#primefactortest()
	#findfactortest()
	#findfactorspeed()
	diotest()
	diopostest()
	#sqrttest()
	#sqrtspeed()
	#sumdivtest()
	#sumdivspeed()
	#fibtest()
	#quadresidues()

