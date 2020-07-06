"""
Math.py - v1.01

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

#-------------------------------------------------------------------------------
#GCD
#-------------------------------------------------------------------------------

def gcd(a,b=None):
	if b==None:
		d=abs(a[0])
		for i in range(1,len(a)):
			d=gcd(d,a[i])
		return d
	while b:
		a,b=b,a%b
	return abs(a)

def lcm(a,b=None):
	if b==None:
		m=abs(a[0])
		for i in range(1,len(a)):
			m=lcm(m,a[i])
		return m
	if a==0 or b==0:
		return 0
	return abs(a*(b//gcd(a,b)))

#-------------------------------------------------------------------------------
#Modulo Arithmetic
#-------------------------------------------------------------------------------

def modinv(x,mod):
	"""x^-1%mod. Note that 0^-1=0 mod 1."""
	#Equivalent to s where s*x+t*mod=1.
	if mod<0: mod=-mod
	b0,b1=0,1
	r0,r1=mod,x%mod
	while r1:
		q=r0//r1
		r0,r1=r1,r0-q*r1
		b0,b1=b1,(b0-q*b1)%mod
	if r0==1: return b0
	return None

def powmod(x,exp,mod):
	"""For some int exp, returns (x^exp)%mod"""
	#x^-exp=(x^-1)^exp if x^-1 exists.
	if exp<0:
		exp=-exp
		x=modinv(x,mod)
		if x==None:
			return None
	#Positive mod so the answer is always positive.
	if mod<0:
		mod=-mod
	val=1
	while exp:
		if exp&1:
			val=(val*x)%mod
		exp>>=1
		x=(x*x)%mod
	return val

def logmod(b,a,n):
	"""Returns the smallest x such that a^x=b mod n. Returns None if no
	solution exists. Assumes (a,n)=1."""
	#We use the baby-step giant-step algorithm:
	#Let m=ceil(sqrt(n)). Then we want to compute x=i*m+j for i,j in {0,1,...,m-1}.
	#We first create a table such that table[a^j%n]=j for j in 0,...,m-1. We then
	#find i by taking a^(i*m+j)=b => a^j*a^(i*m)=b => a^j=b*a^(-i*m). If any
	#b*a^(-i*m) is in the table, then we have found x=i*m+j.
	#
	#If a^x=0 mod n has a solution, then x<=floor(log2(n)). Hence, m=ceil(sqrt(n))>x
	#is sufficient except for n=4,8, or 16.
	if n<=0:
		raise ArithmeticError("modulus<=0.")
	a,b=a%n,b%n
	m=intsqrt(n)
	m+=m*m<n
	table=dict()
	mul=n>1
	for j in range(m):
		if not mul in table:
			table[mul]=j
		mul=(mul*a)%n
	#We have mul=a^m, so take mul=a^(-m).
	mul=modinv(mul,n)
	for i in range(m):
		if b in table:
			return i*m+table[b]
		b=(b*mul)%n
	return None

def primitiveroot(mod):
	"""Returns the smallest primitive root given mod."""
	if mod==1:
		return 0
	if mod==2:
		return 1
	phi=coprime(mod)
	for i in range(2,mod):
		if gcd(i,mod)==1:
			x=1
			for j in range(phi-1):
				x=(x*i)%mod
				if x==1:
					break
			if (x*i)%mod==1:
				return i
	return None

#-------------------------------------------------------------------------------
#Primes
#-------------------------------------------------------------------------------
#A number is prime iff (p-1)!=-1 mod p.

def isprime(n):
	#Miller-Rabin primality test.
	if n<2: return False
	#Perform trial division.
	plist=(2,3,5,7,11,13,17,19,23,29,31,37,41,43,47,53)
	for p in plist:
		if p>=n  : return True
		if n%p==0: return False
	if n<3481:
		return True
	elif n<18446744073709551616:
		#Deterministic witnesses discovered by Jim Sinclair.
		witnesses=(2,325,9375,28178,450775,9780504,1795265022)
	else:
		#Assuming the GRH, test all witnesses in [2,2*ln(n)^2]. We use a rounded up
		#approximation of log2(n) and take 2*ln(n)^2=2*(log2(n)*log2(2)/log2(e))^2=
		#0.960906*log2(n)^2.
		table=(-0.912537,-0.830075,-0.752072,-0.678072,-0.607683,-0.540568,
		       -0.476438,-0.415037,-0.356144,-0.299560,-0.245112,-0.192645,
		       -0.142019,-0.093109,-0.045804, 0.000000)
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
		if x<2 or x==n-1: continue
		pot,exp=x,d
		while exp>1:
			exp>>=1
			pot=(pot*pot)%n
			if exp&1: x=(x*pot)%n
		if x==1 or x==n-1: continue
		#Calculate a^(d*2*r) for r in [0,s-1).
		#Note we already have x=a^d and s-=1.
		for r in range(s):
			x=(x*x)%n
			if x==1  : return False
			if x==n-1: break
		else:
			return False
	#We have found a prime.
	return True

def primegen(maxp=float("inf"),count=float("inf")):
	#Sequentially output primes. Outputs the first 'count' primes or all p<maxp.
	#
	#Based on http://code.activestate.com/recipes/117119-sieve-of-eratosthenes.
	#We first manually output a small set of primes, then begin iterating over a
	#possible prime, p. To speed up iterating over all values p=1,2,3,4,..., we use
	#the fact that for p>=30=2*3*5, only 1*2*4=8 values in every block of 30 will be
	#relatively prime to 30. Hence, given p=30*q+r, we may use r to jump to the next
	#highest value relatively prime to 30. This allows us to only have to test 26% of
	#integers as possible primes.
	#
	#When testing if p is prime:
	#
	#If p is in the dictionary 'comp', then p is prime, and dict[p] is a prime factor
	#of p.
	#
	#If p is less than s, than it is less than the square of the largest prime we
	#need to test for, s=r*r, and it must be prime.
	#
	#Else, p=s=r*r, and r is a factor of p. We add r to 'comp' and find the next
	#prime r'>r and s'=r'*r'.
	#
	#If we find a factor f of p, then we calculate the next composite that will have
	#f as a factor based on the jump values we're using. If the composite isn't in
	#'comp', we add it. Otherwise, we find the next such composite.
	#
	#In this way, 'comp' is a rolling dictionary of the next set of composites to
	#look for.
	#We must manually output all primes below 2*3*5 and up to 7^2.
	for n in (2,3,5,7,11,13,17,19,23,29,31,37,41,43,47):
		if n>=maxn or count<=0: return
		yield n
		count-=1
		#The largest prime we need to test for divisibility is 7, hence s=7*7. We also
	#set p to the first value in our jump schedule that we haven't already output.
	r,sq,n=7,49,49
	it=iter(primegen())
	while next(it)<r: pass
	comp=dict()
	#Based on p%30, find the next value relatively prime to 30.
	jump=(1,6,5,4,3,2,1,4,3,2,1,2,1,4,3,
	      2,1,2,1,4,3,2,1,6,5,4,3,2,1,2)
	while n<maxn and count>0:
		#See if we have a factor of n.
		f=comp.pop(n,0)
		if n==sq:
			#n=r*r is the next prime square we're waiting for.
			f,r=r,next(it)
			sq=r*r
		elif f==0:
			#n!=sq and isn't in comp, so it's prime.
			yield n
			count-=1
		if f:
			#We've found a factor of f. Add it to comp.
			q=n//f
			q+=jump[q%30]
			while q*f in comp: q+=jump[q%30]
			comp[q*f]=f
		n+=jump[n%30]

def coprime(n):
	"""
	Euler totient function. Counts the integers in [1,n) that are relatively
	prime to n.
	"""
	#For a*b=n and d=gcd(a,b), phi(n)=phi(a)*phi(b)*d/phi(d).
	#For prime p, phi(n)=n*prod(p|n,(1-1/p)).
	#phi(1)=1
	#phi(p)=p-1
	#phi(p^k)=p^(k-1)*(p-1)
	#phi(n^m)=n^(m-1)*phi(n)
	#a|b => phi(a)|phi(b)
	#
	#Calculate the totient function by finding prime factors, p, of n and taking
	#cnt-=cnt/p. We speed the function up by skipping integers that cannot be prime
	#because they share a factor with m=2*3*5*7. We begin with p=2 and skip until we
	#hit p=11, then skip based on coprimality with m. (skip amount,next skip). Note
	#that the final "next skip" skips past the initial prime increments.
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
			#We have found a prime factor. Take n//p in case n is a reference.
			n=n//p
			while n%p==0:
				n//=p
			count-=count//p
		#Go to the next factor. It may or may not be a prime.
		p+=pskip[skip]
		skip=pskip[skip+1]
	#If we terminated before finding the last factor, then n is a prime factor.
	if n>1:
		count-=count//n
	return count

def primefactors(n):
	"""Returns a list of the prime factors of n."""
	if n<2:
		return []
	pskip=(
		1,2,2,4,2,6,4,8,2,10,4,12,2,14,4,16,6,18,2,20,6,22,4,24,2,26,4,
		28,6,30,6,32,2,34,6,36,4,38,2,40,6,42,4,44,6,46,8,48,4,50,2,52,4,
		54,2,56,4,58,8,60,6,62,4,64,6,66,2,68,4,70,6,72,2,74,6,76,6,78,4,
		80,2,82,4,84,6,86,2,88,6,90,4,92,2,94,4,96,2,98,10,100,2,102,10,8
	)
	S=[0]*n.bit_length()
	cnt=0
	p,skip=2,0
	while p*p<=n:
		if n%p==0:
			#We have found a prime factor. Avoid n//=p in case n is a reference.
			n=n//p
			while n%p==0:
				n//=p
			S[cnt]=p
			cnt+=1
		#Go to the next factor. It may or may not be a prime.
		p+=pskip[skip]
		skip=pskip[skip+1]
	#If we terminated before finding the last factor, then n is a prime factor.
	if n>1:
		S[cnt]=n
		cnt+=1
	return S[:cnt]

def findfactor(n):
	"""Returns a non-trivial factor of n. Returns n if n is prime."""
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

#-------------------------------------------------------------------------------
#Diophantine Equations
#-------------------------------------------------------------------------------

def diophantine(a,n=None):
	"""
	For a_i,n in Z, returns [x0,x1,...,gcd] such that a0*x0+a1*x1+...=n, or None
	if there is no solution. If n=None, behaves as if n=gcd.
	"""
	#Use the extended Euclidean algorithm to solve gcd[i-1]*x+a[i]*y=gcd[i], where
	#gcd[-1]=0. Once all x,y pairs have been found, reverse over the coefficients so
	#that every solution x'[i]=y[i]*x[i+1]*x[i+2]*... Also multiply all coefficients
	#by n/gcd if n is supplied.
	#
	#Optional speed increases for longer inputs:
	#    Sort abs(a[i]) from smallest to largest.
	#    Add "if r0==1 or r0==-1: r1=0" to loop.
	#    Check if n%r0==0 in loop and terminate early.
	l=len(a)
	x,y=[0]*l,[0]*(l+1)
	r0=0
	for i in range(l):
		#Use the extended Euclidean algorithm to compute x,y and the gcd. Let
		#r0=gcd[i-1] and r1=a[i]. When done, the gcd will be stored in r0.
		x0,x1=1,0
		y0,y1=0,1
		r1=a[i]
		if r0==0:
			y0,r0,r1=1,r1,0
		while r1:
			q=r0//r1
			x0,x1=x1,x0-q*x1
			y0,y1=y1,y0-q*y1
			r0,r1=r1,r0-q*r1
		x[i],y[i]=x0,y0
	#Determine if we have a valid solution. For some a_i, r0 may be negative.
	#Use n=n//r0 in case n is a reference.
	y[l]=abs(r0)
	if n==None: n=y[l]
	if n:
		if r0==0 or n%r0!=0:
			return None
		n=n//r0
	#Propagate all coefficients and multiply by n/gcd.
	for i in range(l-1,-1,-1):
		y[i]*=n
		n=n*x[i]
	return y

def diopositive(a,n):
	"""
	For x_i>=0, return [x0,x1,...,gcd] such that a0*x0+a1*x1+...=n, or None
	if there is no solution.
	"""
	#If n%gcd(a0,a1,...,ak)!=0, then there is no solution. Otherwise:
	#If ai<0 and aj>0, then there is a solution.
	#If k=2, then there is a solution if n>=(a0-1)*(a1-1).
	#If k>=3, then the problem is NP-complete by way of the subset sum problem over
	#the natural numbers.
	assert(len(a)<=2)
	x=diophantine(a,n)
	if x==None:
		return None
	l=len(a)
	for i in range(l):
		if a[i]==0:
			x[i]=0
		if x[i]>=0:
			continue
		j=(i+1)%l
		s,t=a[i],a[j]
		d=gcd(s,t)
		s,t=s//d,t//d
		ta=abs(t)
		k=(-x[i]+ta-1)//ta
		if t<0:
			k=-k
		x[i]+=t*k
		x[j]-=s*k
	if min(x)<0:
		return None
	return x

#-------------------------------------------------------------------------------
#Misc
#-------------------------------------------------------------------------------

def intsqrt(n):
	"""Returns x such that x^2<=n<(x+1)^2."""
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

def sumdiv(n,k=1):
	"""Sum of the positive divisors of n to the k-th power: sum(d^k for d|n)."""
	#We take o(n,k)=sum(d^k for d>0 and d|n)
	#o(p,0)=2
	#o(p^n,0)=n+1
	#o(p,1)=p+1
	#For pi^ai|n and k>0, o(n,k)=prod((pi^((ai+1)*k)-1)/(pi^k-1)).
	#If k=0, o(n,0)=prod(ai+1).
	#Equivalently, for all k, o(n,k)=prod(1+p^k+p^2k+...+p^ai*k).
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

def fibonacci(n):
	"""Calculates the n-th Fibonacci number in log2(n) time."""
	#Let F0=0, F1=1, F2=1, F3=2, ..., FN=F(N-2)+F(N-1). We use the relation
	#
	# (Fn+1) = (0 1) * (Fn+0)
	# (Fn+2)   (1 1)   (Fn+1)
	#
	# (Fn+k+0) = (0 1)^k * (Fn+0)
	# (Fn+k+1)   (1 1)     (Fn+1)
	#
	#Let A and B be matrices such that
	#
	# A = a0 a1   B = b0 b1
	#     a2 a3       b2 b3
	#
	#Then A*B yields
	#
	# A*B = a0*b0+a1*b2  a0*b1+a1*b3
	#       a2*b0+a3*b2  a2*b1+a3*b3
	def mul(A,B):
		return [A[0]*B[0]+A[1]*B[2],A[0]*B[1]+A[1]*B[3],
		        A[2]*B[0]+A[3]*B[2],A[2]*B[1]+A[3]*B[3]]
	mat=[0,1,1,2]
	pot=[0,1,1,1]
	while n:
		if n&1:
			mat=mul(mat,pot)
		n>>=1
		pot=mul(pot,pot)
	return mat[0]

def choose(n,k):
	#For 32 bits, allows for n<=34.
	#
	#We have the standard definition of n choose k. Note that C(n,k)=C(n,n-k).
	#
	#            n!
	#C(n,k) = --------
	#         (n-k)!k!
	#
	#Expanding the factorials and factoring (n-k)! out of the numerator and
	#denominator.
	#
	#          n*(n-1)*(n-2)*...*1          n*(n-1)*(n-2)*...*(n-k+1)
	# = --------------------------------- = -------------------------
	#   (n-k)*(n-k-1)*...*1*k*(k-1)*...*1      k*(k-1)*(k-2)*...*1
	#
	#The numerator has n-(n-k+1)+1=k terms, and the denominator has k-1+1=k terms.
	#Thus we may write the expression as
	#
	#       |k n-k+i
	# = prod|i -----
	#       |1   i
	#
	#Let x(i) denote the i'th term of the product and let x(0)=1. Then
	#
	#                 n-k+i            ( n-k     )                 n-k
	# x(i) = x(i-1) * ----- = x(i-1) * ( --- + 1 ) = x(i-1)+x(i-1)*---
	#                   i              (  i      )                  i
	#
	# x(k) = C(n,k)
	#
	#By calculating x(i) in order, i=1,2,...,k, x(i) will always be an integer.
	#Since the number of iterations is based on k, and C(n,k)=C(n,n-k), we take
	#k'=min(k,n-k) and n'=n-k'. Thus, x(i)=x(i-1)+x(i-1)*n'/i for i=0,...,k'. We may
	#also simplify the calculation of n' and k'. Let
	#
	#    n'=n-k'
	#    if k<=n-k: k'=k  , n'=n-k
	#    if k> n-k: k'=n-k, n'=k
	#
	#Thus, set k'=k and n'=n-k and swap if k'>n'. We may also rewrite the
	#calculation of x(i) to minimize the size of the terms used. Let x' be the next
	#value of x(i) we want to calculate, and x be the previous value x(i-1). We have
	#
	#    x'=x+x*n'/i
	#      =x+n'*((x/i)*i+x%i)/i
	#      =x+n'*(x/i)+(n'*(x%i))/i
	if k<0 or k>n:
		return 0
	n-=k
	if k>n: n,k=k,n
	c=1
	for i in range(1,k+1):
		c+=n*(c//i)+(n*(c%i))//i
	return c

def catalan(n):
	#First 10: 1,1,2,5,14,42,132,429,1430,4862
	#Direct: cat(n)=choose(2*n,n)/(n+1)
	#Recursive: cat(0)=1, cat(n+1)=cat(n)*(4*n+2)/(n+2)
	#
	#Counts the number of:
	#* Dyck words of length 2*n. A Dyck word is made up of X's and Y's and written
	#such that no initial segment has more X's than Y's. For n=6: XXXYYY, XYXXYY,
	#XYXYXY, XXYYXY, XXYXYY.
	#* Ways n pairs of parenthesis can be matched.
	#* Ways n+1 factors may be grouped by parenthesis.
	#* Full binary trees of n+1 leaves (or n nodes).
	#* Non-isomorphic ordered trees of n nodes.
	#* Monotonic (ex: only up and right) lattice paths along the edges of a grid with
	#nxn cells that doesn't cross the diagonal.
	#* Ways a convex polygon with n+2 sides (or n+1 vertices) can be divided into
	#triangles with non-intersecting lines.
	#* Stack sortable permutations of length n.
	#* Permutations of length {1,...,n} with no three-term increasing subsequence.
	#* Non-crossing partitions of {1,...,n}.
	#* Ways to tile a stairstep shape of height n with n rectangles.
	#* Rooted binary trees with n+1 leaves (or n nodes).
	#* Mountain ranges formed by upstrokes and downstrokes.
	#
	#c=1
	#for i in range(1,n+1):
	#	c+=n*(c//i)+(n*(c%i))//i
	#return c//(n+1)
	c=1
	for i in range(n):
		c=(c*(4*i+2))//(i+2)
	return c

def bernoulli(n):
	#Returns (a,b) such that B(n)=a/b. B(1)=+1/2.
	#Akiyama-Tanagawa algorithm.
	if n>1 and n&1:
		return (0,1)
	a=[0]*(n+1)
	for i in range(n+1):
		#a[i]=1/(i+1)
		a[i]=(1,i+1)
		for j in range(i,0,-1):
			#a[j-1]=j*(a[j-1]-a[j])
			#j*(n0*d1-n1*d0)/d0*d1
			n0,d0=a[j-1]
			n1,d1=a[j]
			n=j*(n0*d1-n1*d0)
			d=d0*d1
			g=gcd(n,d)
			a[j-1]=(n//g,d//g)
	return a[0]

def bernoulliarr(n):
	#Returns (a,b) such that B(n)=a/b. B(1)=+1/2.
	#Akiyama-Tanagawa algorithm.
	a=[0]*n
	b=[0]*n
	for i in range(n):
		#a[i]=1/(i+1)
		a[i]=(1,i+1)
		for j in range(i,0,-1):
			#a[j-1]=j*(a[j-1]-a[j])
			#j*(n0*d1-n1*d0)/d0*d1
			n0,d0=a[j-1]
			n1,d1=a[j]
			n=j*(n0*d1-n1*d0)
			d=d0*d1
			g=gcd(n,d)
			a[j-1]=(n//g,d//g)
		b[i]=a[0]
	return b

def sumexp(n,exp):
	#Sum 1^k+2^k+...+n^k.
	if exp==0:
		return n
	elif exp==1:
		return (n*(n+1))//2
	elif exp==2:
		return (n*(n+1)*(2*n+1))//6
	else:
		#Faulhaber's formula.
		exp+=1
		bn=bernoulliarr(exp)
		d=bn[0][1]
		for i in range(1,exp):
			d=lcm(d,bn[i][1])
		s=0
		for i in range(exp):
			s+=choose(exp,i)*bn[i][0]*(d//bn[i][1])*(n**(exp-i))
		s//=exp*d
		return s

def sternseq(n):
	#Stern's diatomic series. Given f(n), the sequence f(n)/f(n+1) produces every
	#non-negative ratio a/b exactly once. Let
	#
	#    f(0)=0
	#    f(1)=1
	#    f(n)={n even: f(n/2)
	#         {n odd : f(n/2)+f(n/2+1)
	#
	if n<2:
		return n
	k=n//2
	if n&1:
		return sternseq(k)+sternseq(k+1)
	return sternseq(k)

def caterer(n):
	#The maximum number of pieces a cake can be divided into with n cuts.
	#f(n)=1,2,4,7,11,16,22,29,37,46,56
	return (n*(n+1))//2+1

def bentlines(n):
	#The maximum number of pieces a cake can be divided into when cut with n bent
	#lines (V shaped wedges).
	#f(n)=1,2,7,16,29,46,67,92,121,154
	#OEIS: A130883
	return 1-n+2*n*n

def rotpoint3(p,xr,yr,zr):
	x,y,z=p
	#x
	xt,yt,zt=x,y,z
	cs,sn=math.cos(xr),math.sin(xr)
	y=yt*cs-zt*sn
	z=yt*sn+zt*cs
	#y
	xt,yt,zt=x,y,z
	cs,sn=math.cos(yr),math.sin(yr)
	x=xt*cs+zt*sn
	z=-xt*sn+zt*cs
	#z
	xt,yt,zt=x,y,z
	cs,sn=math.cos(zr),math.sin(zr)
	x=xt*cs-yt*sn
	y=xt*sn+yt*cs
	return (x,y,z)


