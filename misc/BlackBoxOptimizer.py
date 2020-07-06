"""
BlackBoxOptimizer.py - v1.02

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

import random,math

def BBO(F,x,iters,params=(40,2000,4,5,0.644392,1.587432,1.5005519,1.0,1.0)):
	#params=particles,lifespan,lifeinc,lifedec,w,c1,c2,posscale,velscale
	def cauchy(): return math.tan((random.random()-0.5)*3.141592652)
	def randvec(arr,dev):
		norm=1e-20
		for i in range(dim):
			v=random.gauss(0.0,1.0)
			arr[i]=v
			norm+=v*v
		norm=dev/math.sqrt(norm)
		for i in range(dim): arr[i]*=norm
	class Particle(object):
		def __init__(self):
			self.pos=[0.0]*dim
			self.vel=[0.0]*dim
			self.life=0
	dim=len(x)
	particles=params[0]
	lifespan,lifeinc,lifedec=params[1:4]
	w,c1,c2,pscale,vscale=params[4:9]
	partarr=[Particle() for i in range(particles)]
	glberror,glbpos,glbmag=F(x),list(x),sum(y*y for y in x)
	for iter in range(iters):
		p=partarr[iter%particles]
		pos,vel=p.pos,p.vel
		if p.life<=0:
			randvec(pos,dim*pscale*cauchy())
			randvec(vel,dim*vscale*cauchy())
			for i in range(dim): pos[i]+=glbpos[i]
			p.life=lifespan
		else:
			locpos=p.locpos
			for i in range(dim):
				r1,r2=random.random(),random.random()
				vel[i]=w*vel[i]+r1*c1*(locpos[i]-pos[i])+r2*c2*(glbpos[i]-pos[i])
				pos[i]+=vel[i]
		error,mag=F(pos),sum(y*y for y in pos)
		if p.life==lifespan or p.locerror>error or (p.locerror>=error and p.locmag>mag):
			p.locerror,p.locpos,p.locmag=error,list(pos),mag
			p.life+=lifeinc
		p.life-=lifedec
		if glberror>error or (glberror>=error and glbmag>mag):
			glberror,glbpos,glbmag=error,p.locpos,mag
	return glbpos

if __name__=="__main__":
	from timeit import default_timer as timer
	def Rastrigin(x):
		n,s=len(x),0.0
		cos,pi=math.cos,math.pi*2
		for i in range(n):
			y=x[i]-1
			s+=10.0+y*y-10.0*cos(pi*y)
		return s/n
	t0=timer()
	x=BBO(Rastrigin,[0]*10,100000)
	print(timer()-t0)
	print("x={0}".format(x))
	print("error={0}".format(Rastrigin(x)))

