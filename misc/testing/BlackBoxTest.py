"""
BlackBoxTest.py - v1.02

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
TODO:
Find optimal particle counts in PSO.
"""

import math,random,multiprocessing
from timeit import default_timer as timer

#--------------------------------------------------------------------------------
#Test Functions
#--------------------------------------------------------------------------------
#See https://www.sfu.ca/~ssurjano/optimization.html

def SphereInit(n):
	#Typical initialization values for the sphere function.
	return [random.uniform(-5.12,5.12) for i in range(n)]

def SphereFunc(x):
	#Hypershpere. F(x)=0 at x={0,0,0,...}.
	s=0.0
	for y in x: s+=y*y
	return s

def RastriginInit(n):
	#Typical initialization values for the Rastrigin function.
	return [random.uniform(-5.12,5.12) for i in range(n)]

def RastriginFunc(x):
	#Rastrigin function. F(x)=0 at x={0,0,0,...}.
	s,pi,cos=0.0,math.pi*2.0,math.cos
	for y in x:
		s+=10.0+y*y-10.0*cos(pi*y)
	return s

def RosenbrockInit(n):
	#Typical initialization values for the Rosenbrock function.
	return [random.uniform(-5,10) for i in range(n)]

def RosenbrockFunc(x):
	#Rosenbrock function. F(x)=0 at x={1,1,1,...}.
	n,s=len(x),0.0
	for i in range(1,n):
		a,b=x[i-1],x[i]
		b,a=b-a*a,a-1
		s+=100.0*b*b+a*a
	return s

def NNAct(x):
	#Neural network activation function.
	if x>1.0: return 1.0
	return x if x>0.0 else 0.0

def NNInit(n):
	#Intialization values for neural network functions.
	return [random.uniform(-1,1) for i in range(n)]

def NNXorBasicFunc(w):
	#Neural network approximation of the xor function. Requires len(x) to be a
	#multiple of 8.
	n=len(w)
	assert(n%8==0)
	bits=n//8+1
	err=0.0
	bitmasks=1<<bits;
	for bitmask in range(bitmasks):
		expect,tmpmask=bitmask,bitmask
		n4,wpos=float(tmpmask&1),0
		for i in range(1,bits):
			tmpmask>>=1
			expect^=tmpmask
			n0=NNAct(n4) if i>1 else n4
			n1=float(tmpmask&1)
			n2=NNAct(n0*w[wpos+0]+n1*w[wpos+1]+w[wpos+2])
			n3=NNAct(n0*w[wpos+3]+n1*w[wpos+4]+w[wpos+5])
			n4=n2*w[wpos+6]+n3*w[wpos+7]
			wpos+=8
		n4-=expect&1
		err+=n4*n4
	return err

def NNXorRobustFunc(w):
	#Neural network approximation of the xor function for noisy inputs. Robust
	#networks can handle noise of +-0.25. Requires len(x) to be a multiple of 8.
	n=len(w)
	assert(n%8==0)
	eps=random.random()*0.10+0.05
	noise=(-eps,1.0-eps,eps,1.0+eps)
	bits=n//8+1
	err=0.0
	bitmasks=1<<(2*bits)
	for bitmask in range(bitmasks):
		expect,tmpmask=bitmask,bitmask
		n4,wpos=noise[tmpmask&3],0
		for i in range(1,bits):
			tmpmask>>=2
			expect^=tmpmask
			n0=NNAct(n4) if i>1 else n4
			n1=noise[tmpmask&3]
			n2=NNAct(n0*w[wpos+0]+n1*w[wpos+1]+w[wpos+2])
			n3=NNAct(n0*w[wpos+3]+n1*w[wpos+4]+w[wpos+5])
			n4=n2*w[wpos+6]+n3*w[wpos+7]
			wpos+=8
		n4-=expect&1
		err+=n4*n4
	return err

def NNLife(w):
	#Neural network approximation of Conway's Game of Life. Requires len(w)=22.
	#Processing is sped up by using a lookup table.
	assert(len(w)==22)
	n0,n0buf,n1,n1buf=w[0],[0]*512,w[10],[0]*512
	s,sbuf,hbit=0,[0]*512,0
	err=0.0
	for bitmask in range(512):
		if bitmask:
			hbit+=(bitmask>>hbit)-1
			j=bitmask&((1<<hbit)-1)
			n0=n0buf[j]+w[ 1+hbit]
			n1=n1buf[j]+w[11+hbit]
			s=sbuf[j]+1
		n0buf[bitmask]=n0
		n1buf[bitmask]=n1
		sbuf[bitmask]=s
		a=bitmask&1
		n2=NNAct(n0)*w[20]+NNAct(n1)*w[21]
		n2-=((s-a)|a)==3
		err+=n2*n2
	return err

def TestFunctionSolutions():
	#Make sure the test functions have solutions.
	for f in range(6):
		print("Test: {0}".format(f))
		if f==0: func,sol,n0,n1=SphereFunc,[0.0],0,50
		if f==1: func,sol,n0,n1=RastriginFunc,[0.0],0,50
		if f==2: func,sol,n0,n1=RosenbrockFunc,[1.0],0,50
		if f==3: func,sol,n0,n1=NNXorBasicFunc,[25,25,-12,25,25,-37,1,-1],0,4
		if f==4: func,sol,n0,n1=NNXorRobustFunc,[25,25,-12,25,25,-37,1,-1],1,4
		for i in range(n0,n1+1):
			assert(func(sol*i)==0)

#--------------------------------------------------------------------------------
#Parameter Testing
#--------------------------------------------------------------------------------

def TestParamsUnpack(args):
	#Unpack the argument array supplied to the multithreaded testing pool.
	f,name,dim,optfunc,iters,params=args
	if   name=="Sphere"     : func,init,weight=SphereFunc,SphereInit,1.0/dim
	elif name=="Rastrigin"  : func,init,weight=RastriginFunc,RastriginInit,0.1/dim
	elif name=="Rosenbrock" : func,init,weight=RosenbrockFunc,RosenbrockInit,0.1/dim
	elif name=="NNXorBasic" : func,init,weight=NNXorBasicFunc,NNInit,4.0/(1<<(dim//8+1))
	elif name=="NNXorRobust": func,init,weight=NNXorRobustFunc,NNInit,4.0/(1<<2*(dim//8+1))
	else: raise NotImplementedError("Unrecognized function: "+name)
	if params is None: err=optfunc(func,init(dim),iters)
	else: err=optfunc(func,init(dim),iters,params)
	return (f,err,err*weight)

def TestParams(optfunc,iters,trials,params=None,funcs=None,threaded=False):
	#Test an optimization function against various optimization functions. Each
	#function will take a real vector as input and return a real number that needs to
	#be minimized.
	#
	#(function,dimension)
	if funcs is None:
		funcs=(("Sphere",30),("Rastrigin",30),("Rosenbrock",30),
		       ("NNXorBasic",8),("NNXorBasic",16),("NNXorRobust",8))
	funcn=len(funcs)
	start=timer()
	args=[]
	for f in range(funcn):
		name,dim=funcs[f]
		args+=[(f,name,dim,optfunc,iters,params)]*trials
	if threaded:
		pool=multiprocessing.Pool()
		results=pool.imap_unordered(TestParamsUnpack,args)
		pool.close()
		pool.join()
	else:
		results=[TestParamsUnpack(arg) for arg in args]
	#Find the average error for each function.
	normerr,weighterr=[0.0]*funcn,[0.0]*funcn
	for f,nerr,werr in results:
		normerr[f]+=nerr
		weighterr[f]+=werr
	for f in range(funcn):
		normerr[f]/=trials
		weighterr[f]/=trials
	#Display the results.
	padname,paddim=0,0
	for name,dim in funcs:
		padname=max(padname,len(name))
		paddim=max(paddim,len(str(dim)))
	pad=padname+paddim+1
	print("{0:<{1}}: {2}".format("Iters",pad,iters))
	print("{0:<{1}}: {2:.6f}".format("Time",pad,timer()-start))
	print("{0:<{1}}: {2:.5e}".format("Weighted Total",pad,sum(weighterr)))
	for f in range(funcn):
		args=(funcs[f][0],padname,funcs[f][1],paddim,normerr[f])
		print("{0:<{1}} {2:>{3}}: {4:.5e}".format(*args))
	return normerr

#--------------------------------------------------------------------------------
#Dummy Optimizer
#--------------------------------------------------------------------------------

def DummyOpt(F,x,iters):
	#Simple gaussian perturbation solver.
	#
	#Iters         : 10000
	#Time          : 18.865184
	#Total Error   : 4.22635e+00
	#Sphere      30: 5.87754e-05
	#Rastrigin   30: 8.90368e-01
	#Rosenbrock  30: 3.12973e-01
	#NNXorBasic   8: 9.83096e-01
	#NNXorBasic  16: 1.28210e+00
	#NNXorRobust  8: 7.57751e-01
	n,xerr=len(x),F(x)
	gauss=random.gauss
	y=[0.0]*n
	for iter in range(iters):
		for i in range(n): y[i]=gauss(x[i],0.01)
		yerr=F(y)
		if xerr>yerr:
			xerr=yerr
			for i in range(n): x[i]=y[i]
	return xerr

#--------------------------------------------------------------------------------
#Particle Swarm Optimization
#--------------------------------------------------------------------------------

#Detecting particle convergence by their euclidean distances won't work. For the
#Rastrigin function, there's a lot of local minima with the same values but at
#different coordinates.

def PSO(F,x,iters,params=(40,2000,4,5,0.644392,1.587432,1.5005519,1.0,1.0)):
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
			p.locerror,p.locpos[:],p.locmag=error,pos,mag
			p.life+=lifeinc
		p.life-=lifedec
		if glberror>error or (glberror>=error and glbmag>mag):
			glberror,glbpos[:],glbmag=error,pos,mag
	return glberror

def PSORing(F,x,iters,params=None):
	#params=particles,lifespan,lifeinc,lifedec,w,c1,c2,posscale,velscale
	rand=random.random
	def cauchy(): return math.tan((rand()-0.5)*3.141592652)
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
			self.locpos=[0.0]*dim
			self.life=0
	dim=len(x)
	particles=int(math.log(dim if dim>1 else 1)*38+39)
	nbh=int(math.sqrt(particles)*0.5) if particles>5 else 1
	partarr=[Particle() for i in range(particles)]
	glberr,glbpos=F(x),list(x)
	for iter in range(iters):
		p=partarr[iter%particles]
		pos,vel,locpos=p.pos,p.vel,p.locpos
		nbhpos=p.locpos,p.locpos
		if iter>=particles:
			nbherr=p.locerr
			for i in range(-nbh,nbh+1):
				q=partarr[(iter+i)%particles]
				if nbherr>q.locerr:
					nbherr,nbhpos=q.locerr,q.locpos
		if p.life<=0:
			randvec(pos,cauchy())
			randvec(vel,cauchy())
			for i in range(dim): pos[i]+=nbhpos[i]
			p.lifespan=random.randrange(200,401)
			p.life=p.lifespan
		else:
			u=float(p.life)/p.lifespan
			w =0.798704-u*0.188289
			c1=1.967469-u*0.578807
			c2=1.156719-u*0.339261
			for i in range(dim):
				r1,r2=c1*rand(),c2*rand()
				vel[i]=w*vel[i]+r1*(locpos[i]-pos[i])+r2*(nbhpos[i]-pos[i])
				pos[i]+=vel[i]
		err=F(pos)
		if p.life==lifespan or p.locerr>err:
			p.locerr,p.locpos[:]=err,pos
		p.life-=1
		if glberr>err:
			glberr,glbpos[:]=err,pos
	return glberr

def BBPSO(F,x,iters,params=(40,2000,4,5)):
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
			self.life=0
	dim=len(x)
	particles,lifespan,lifeinc,lifedec=params
	partarr=[Particle() for i in range(particles)]
	glberror,glbpos,glbmag=F(x),list(x),sum(y*y for y in x)
	for iter in range(iters):
		p=partarr[iter%particles]
		pos=p.pos
		if p.life<=0:
			randvec(pos,dim*cauchy())
			for i in range(dim): pos[i]+=glbpos[i]
			p.life=lifespan
		else:
			locpos=p.locpos
			for i in range(dim):
				l,g=locpos[i],glbpos[i]
				pos[i]=random.gauss((l+g)*0.5,l-g)
		error,mag=F(pos),sum(y*y for y in pos)
		if p.life==lifespan or p.locerror>error or (p.locerror>=error and p.locmag>mag):
			p.locerror,p.locpos[:],p.locmag=error,pos,mag
			p.life+=lifeinc
		p.life-=lifedec
		if glberror>error or (glberror>=error and glbmag>mag):
			glberror,glbpos[:],glbmag=error,pos,mag
	return glberror

def APSO(F,x,iters,params=(40,2000,4,5,0.644392,1.587432,1.5005519,1.0,1.0)):
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
			self.locpos=[0.0]*dim
			self.life=0
	dim=len(x)
	particles=params[0]
	lifespan,lifeinc,lifedec=params[1:4]
	w,c1,c2,pscale,vscale=params[4:9]
	partarr=[Particle() for i in range(particles)]
	glberror,glbpos=F(x),list(x)
	for iter in range(iters):
		rank=iter%particles
		p=partarr[iter%particles]
		pos=p.pos
		vel=p.vel
		new=0
		if p.life<=0:
			randvec(pos,dim*pscale*cauchy())
			randvec(vel,dim*vscale*cauchy())
			for i in range(dim): pos[i]+=glbpos[i]
			p.life=300+random.randrange(301)
			new=1
		else:
			locpos=p.locpos
			for i in range(dim):
				vel[i]=0.7*vel[i]+(random.random()/(rank+1))*(locpos[i]-pos[i])
				px=0.0
				for j in range(particles):
					q=partarr[j]
					if p.error>q.locerror:
						px+=(random.random()/(j+1))*(q.locpos[i]-pos[i])
				vel[i]+=px
				pos[i]+=vel[i]
		p.error=F(pos)
		if new or p.locerror>p.error:
			p.locerror,p.locpos[:]=p.error,pos
		p.life-=1
		if glberror>p.error:
			glberror,glbpos[:]=p.error,pos
		i=iter%particles
		while i and p.error<partarr[i-1].error:
			partarr[i]=partarr[i-1]
			i-=1
		partarr[i]=p
	return glberror

def PSOFormatCoefs(coefs):
	#(1-u)*(a-b)+b
	#a-b+b-u*(a-b)
	#a-u*(a-b)
	print("w={0:.6f}-u*{1:.6f}".format(coefs[0],coefs[0]-coefs[1]))
	print("c1={0:.6f}-u*{1:.6f}".format(coefs[2],coefs[2]-coefs[3]))
	print("c2={0:.6f}-u*{1:.6f}".format(coefs[4],coefs[4]-coefs[5]))

#PSOFormatCoefs((0.798704,0.610415,1.967469,1.388662,1.156719,0.817458))

#--------------------------------------------------------------------------------
#Evolution Strategies
#--------------------------------------------------------------------------------

def SNES(F,x,iters,params=(1.0,)):
	#Train the network to fit a given data set using Seperable NES. Adapted from
	#Natural Evolution Strategies by Wierstra, Schaul, Glasmachers, Sun, Peters, and
	#Schmidhuber.
	learn=params[0]
	gauss=random.gauss
	dim=len(x)
	samples=4+int(3*math.log(dim))
	learn*=0.5*(3.0+math.log(dim))/(5*math.sqrt(dim))
	#Instead of using the direct values from our fitness function, the samples are
	#sorted by fitness and given a utility value from their sorted position.
	off=math.log(samples*0.5+1)
	utility=[max(off-math.log(i+1),0) for i in range(samples)]
	norm,off=sum(utility),1.0/samples
	for i in range(samples): utility[i]=utility[i]/norm-off
	samplearr=[[0.0]*dim for i in range(samples)]
	mean,dev=list(x),[1.0]*dim
	point,fitness=[0.0]*dim,[0.0]*samples
	minpoint,minfitness=list(mean),F(mean)
	for iter in range(0,iters,samples):
		#Generate a random sampling of points in normal(mean,dev).
		for i in range(samples):
			sample=samplearr[i]
			for j in range(dim):
				sample[j]=gauss(0,1)
				point[j]=mean[j]+dev[j]*sample[j]
			#Find the fitness of the new point and sort it.
			j,fit=i,F(point)
			while j and fit<fitness[j-1]:
				fitness[j]=fitness[j-1]
				samplearr[j]=samplearr[j-1]
				j-=1
			fitness[j]=fit
			samplearr[j]=sample
		#Check if we have a new optimal point.
		if minfitness>fitness[0]:
			minfitness=fitness[0]
			sample=samplearr[0]
			for i in range(dim):
				minpoint[i]=mean[i]+dev[i]*sample[i]
		#Compute gradients.
		for i in range(dim):
			mgrad,dgrad=0.0,0.0
			for j in range(samples):
				u,s=utility[j],samplearr[j][i]
				mgrad+=u*s
				dgrad+=u*(s*s-1.0)
			#Update the mean and deviation for our next sampling.
			mean[i]+=mgrad*dev[i]
			dev[i]*=math.exp(learn*dgrad)
	return minfitness

#--------------------------------------------------------------------------------
#Main
#--------------------------------------------------------------------------------

if __name__=="__main__":
	#TestFunctionSolutions()
	#TestParams(DummyOpt,10000,100)
	TestParams(APSO,10000,10)
	"""
	results: 2.229267e-02, 9.761426e-01, 9.087044e-01, 2.085259e-01, 2.147334e-01, 3.741740e-01
	time   : 64.165335
	"""
	#params=(40,2000,4,5,0.644392,1.587432,1.5005519,1.0,1.0)
	#params=(40,2000,4,5)
	#params=(1.0,)
	#params=(45,1787,8,7,0.667046,1.903300,1.511318,1.0,1.0)
	#TestParams(PSORing,10000,100)

