"""
primegen.py - v1.04

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

def primegen(maxn=float("inf"),count=float("inf")):
	# Sequentially output primes. Outputs all p<maxn or the first 'count' primes.
	for n in (2,3,5,7,11,13,17,19,23,29,31,37,41,43,47):
		if n>=maxn or count<=0: return
		yield n
		count-=1
	# Recursive generator for upcoming factors.
	r,sq,n=7,49,49
	it=iter(primegen())
	while next(it)<r: pass
	comp=dict()
	jump=(1,6,5,4,3,2,1,4,3,2,1,2,1,4,3,
	      2,1,2,1,4,3,2,1,6,5,4,3,2,1,2)
	while n<maxn and count>0:
		# See if we have a factor of n.
		f=comp.pop(n,0)
		if n==sq:
			# n=r*r is the next prime square we're waiting for.
			f,r=r,next(it)
			sq=r*r
		elif f==0:
			# n!=sq and isn't in comp, so it's prime.
			yield n
			count-=1
		if f:
			# We've found a factor of n. Add it to comp.
			q=n//f
			q+=jump[q%30]
			while q*f in comp: q+=jump[q%30]
			comp[q*f]=f
		n+=jump[n%30]

if __name__=="__main__":
	print("First 20 primes : "+str(list(primegen(count=20))))
	print("Primes under 100: "+str(list(primegen(100))))
	print("Loop iterator test:")
	for p in primegen():
		if p>50: break
		print(p)
	n=1000000
	print("Testing against sieve for p<"+str(n))
	sieve=list(range(n))
	for i in range(2,n):
		if sieve[i]:
			for j in range(i*i,n,i): sieve[j]=0
	sieve=[p for p in sieve if p>1]
	assert(sieve==list(primegen(n)))

