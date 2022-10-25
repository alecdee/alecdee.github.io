"""
NTrace.py - v1.24

Copyright 2020 Alec Dee - MIT license - SPDX: MIT
alecdee.github.io - akdee144@gmail.com

--------------------------------------------------------------------------------
A N-Dimensional Ray Tracer

Notes:
* The scene can have any number of spatial dimensions.
* Most processing time is spent in BVH.raypick() and BVHNode.intersect().
* Epsilon for double precision: 1e-8, single: 1e-4.
* Mesh instancing is supported.
* Wavefront OBJ mesh files are supported. Textures are not.
* Special effects can be done by manipulating how light behaves. Ex: materials
  with negative luminance will emit shadows.
* Coordinate system for the 3D camera:

         +y
          ^
          |        -z
          |      .'
          |    .'
          |  .'
          |.'
          +----------> +x

--------------------------------------------------------------------------------
TODO

Render 2D scenes by using the nearest point we're inside.
Reorganize how scatter length is used to limit ray traversal.
Add recalcnorm() and applytransform() to mesh.
Add vert/face unique id tracking. Add delete/get.
Add text primitives.
"""

import math,random,sys


#---------------------------------------------------------------------------------
# Algebra
#---------------------------------------------------------------------------------
# Helper classes for matrix/vector linear algebra.


class Matrix(object):
	def __init__(self,rows=None,cols=None,copy=True):
		if isinstance(rows,Matrix):
			cols=(rows.rows,rows.cols)
			rows=rows.elem
		if hasattr(rows,"__getitem__"):
			elem=rows
			if cols: rows,cols=cols
			elems=rows*cols
			if copy: elem=list(elem)
			assert(len(elem)==elems)
		elif rows is not None:
			if cols is None: cols=0
			elem=[0.0]*(rows*cols)
		else:
			rows,cols,elem=0,0,[]
		self.elem,self.elems=elem,rows*cols
		self.rows,self.cols=rows,cols


	@staticmethod
	def getinverse(x):
		y=abs(x)
		if y<1e-10 or y>1e10:
			return None
		return 1.0/x


	def replace(a,b):
		assert(isinstance(b,Matrix))
		a.elem,a.elems=b.elem,b.elems
		a.rows,a.cols=b.rows,b.cols
		return a


	def one(a):
		"""Make A the identity matrix."""
		a.zero()
		elem=a.elem
		n,cols=min(a.rows,a.cols),a.cols
		for i in range(n):
			elem[i*cols+i]=1.0
		return a


	def zero(a):
		"""Zeroize matrix A."""
		elem=a.elem
		for i in range(a.elems):
			elem[i]=0.0
		return a


	def __neg__(a):
		return Matrix([-e for e in a.elem],(a.rows,a.cols),False)


	def __mul__(a,b):
		if isinstance(b,Vector):
			# Vector A*v.
			arows,acols,i=a.rows,a.cols,0
			ae,be,ve=a.elem,b.elem,[0.0]*arows
			for r in range(arows):
				sum=ae[i]*be[0]
				for c in range(1,acols):
					sum+=ae[i+c]*be[c]
				i+=acols
				ve[r]=sum
			return Vector(ve,False)
		elif not isinstance(b,Matrix):
			# If b is not a matrix, perform a scalar multiplication.
			return Matrix([e*b for e in a.elem],(a.rows,a.cols),False)
		assert(a.cols==b.rows)
		m=Matrix(a.rows,b.cols)
		aelem,belem,melem=a.elem,b.elem,m.elem
		brows,bcols,belems=b.rows,b.cols,b.elems-1
		aval,bval=0,0
		for i in range(m.elems):
			# Multiply row r of A with column c of B.
			sum=melem[i]
			while bval<=belems:
				sum+=aelem[aval]*belem[bval]
				aval+=1
				bval+=bcols
			melem[i]=sum
			bval-=belems
			if bval==bcols: bval=0
			else: aval-=brows
		return m


	def __imul__(a,b):
		return a.replace(a*b)


	def inv(a):
		"""Returns the multiplicative inverse of A."""
		rows,cols=a.rows,a.cols
		assert(rows==cols)
		ret=Matrix(a)
		getinverse=Matrix.getinverse
		elem,elems=ret.elem,ret.elems
		perm=list(range(cols))
		for i in range(rows):
			# Find a row with an invertible element in column i.
			dval=i*cols
			sval,j,j0=dval,i,i+1
			for k in range(dval+cols,elems,cols):
				if abs(elem[k+i])>abs(elem[sval+i]):
					sval,j=k,j0
				j0+=1
			inv=getinverse(elem[sval+i])
			if inv is None:
				raise ZeroDivisionError("Unable to find an invertible element.")
			# Swap the desired row with row i. Then put row i in reduced echelon form.
			if sval!=dval:
				for c in range(cols):
					elem[sval+c],elem[dval+c]=elem[dval+c],elem[sval+c]
			perm[i],perm[j]=perm[j],perm[i]
			# Put the row into reduced echelon form. Since entry (i,i)=1 and (i,i')=1*inv,
			# set (i,i)=inv.
			for c in range(cols):
				if c==i: continue
				elem[dval+c]*=inv
			elem[dval+i]=inv
			# Perform row operations with row i to clear column i for all other rows in A.
			# Entry (j,i') will be 0 in the augmented matrix, and (i,i') will be inv, hence
			# (j,i')=(j,i')-(j,i)*(i,i')=-(j,i)*inv.
			for r in range(rows):
				if r==i: continue
				sval=r*cols
				mul=elem[sval+i]
				for c in range(cols):
					if c==i: continue
					elem[sval+c]-=elem[dval+c]*mul
				elem[sval+i]=-elem[dval+i]*mul
		# Re-order columns due to swapped rows.
		tmp=[0]*cols
		for r in range(rows):
			dval=r*cols
			for i in range(cols):
				tmp[i]=elem[dval+i]
			for i in range(cols):
				elem[dval+perm[i]]=tmp[i]
		return ret


	def __abs__(a):
		"""Returns the determinant of A."""
		cols=a.cols
		assert(a.rows==cols)
		if cols==0:
			# The empty matrix has a determinant of 1.
			return 1.0
		# Copy the matrix. Use the upper triangular form to compute the determinant.
		m=Matrix(a)
		elem,elems=m.elem,m.elems
		getinverse=Matrix.getinverse
		sign,dval=0,0
		for i in range(cols-1):
			dval=i*cols
			sval=dval
			for j in range(dval+cols,elems,cols):
				if abs(elem[j+i])>abs(elem[sval+i]):
					sval=j
			inv=getinverse(elem[sval+i])
			if inv is None: continue
			if sval!=dval:
				sign^=1
				for c in range(i,cols):
					elem[sval+c],elem[dval+c]=elem[dval+c],elem[sval+c]
			for c in range(i+1,cols):
				elem[dval+c]*=inv
			for r in range(i+1,cols):
				sval=r*cols
				mul=elem[sval+i]
				for c in range(i+1,cols):
					elem[sval+c]-=elem[dval+c]*mul
		# We have the matrix in upper triangular form. Multiply the diagonals to get the
		# determinant.
		det=elem[0]
		for i in range(1,cols):
			det=det*elem[i*cols+i]
		return -det if sign else det


	def rotate(a,angs):
		"""Perform a counter-clockwise, right-hand rotation given n*(n-1)/2 angles. In
		3D, angles are expected in ZYX order."""
		if not hasattr(angs,"__len__"):
			angs=(angs,)
		dim=a.rows
		ret=Matrix(a)
		assert(dim==a.cols and dim*(dim-1)//2==len(angs))
		elem,ang=ret.elem,0
		for j in range(1,dim):
			for i in range(j):
				# We have
				# (i,i)=cos   (i,j)=-sin
				# (j,i)=sin   (j,j)=cos
				cs=math.cos(angs[ang])
				sn=math.sin(angs[ang])
				ang+=1
				# For each row r:
				# (r,i)=(r,i)*cos+(r,j)*sin
				# (r,j)=(r,j)*cos-(r,i)*sin
				# (r,c)=(r,c) otherwise
				ival,jval=i,j
				for r in range(dim):
					t0,t1=elem[ival],elem[jval]
					elem[ival]=t0*cs+t1*sn
					elem[jval]=t1*cs-t0*sn
					ival+=dim
					jval+=dim
		return ret


class Vector(object):
	def __init__(self,x,copy=True):
		if isinstance(x,int):
			elem=[0.0]*x
		else:
			elem=list(x) if copy else x
		self.elem=elem
		self.elems=len(elem)


	def __len__(self):
		return self.elems


	def __getitem__(self,i):
		return self.elem[i]


	def __setitem__(self,i,v):
		self.elem[i]=v


	def __iter__(self): return iter(self.elem)


	def randomize(u):
		# Turn u into a random unit vector.
		n=u.elems
		if n==0: return u
		ue,mag=u.elem,0.0
		gauss=random.gauss
		while mag<=1e-10:
			mag=0.0
			for i in range(n):
				x=gauss(0.0,1.0)
				ue[i]=x
				mag+=x*x
		mag=1.0/math.sqrt(mag)
		for i in range(n): ue[i]*=mag
		return u


	def zero(u):
		ue=u.elem
		for i in range(u.elems): ue[i]=0.0
		return u


	def __add__(u,v):
		ue,ve=u.elem,v.elem
		return Vector([ue[i]+ve[i] for i in range(u.elems)],False)


	def __iadd__(u,v):
		ue,ve=u.elem,v.elem
		for i in range(u.elems): ue[i]+=ve[i]
		return u


	def __sub__(u,v):
		ue,ve=u.elem,v.elem
		return Vector([ue[i]-ve[i] for i in range(u.elems)],False)


	def __isub__(u,v):
		ue,ve=u.elem,v.elem
		for i in range(u.elems): ue[i]-=ve[i]
		return u


	def __neg__(u):
		return Vector([-x for x in u.elem],False)


	def __mul__(u,v):
		# Return the dot product if v is a vector, or the scalar product otherwise.
		ue=u.elem
		if isinstance(v,Vector):
			# Vector dot product u*v=u.x*v.x+u.y*v.y+...
			s,ve=0.0,v.elem
			for i in range(u.elems):
				s+=ue[i]*ve[i]
			return s
		# Elementwise scalar product u*s.
		return Vector([x*v for x in ue],False)


	def __rmul__(u,v):
		# Make sure to use the scalar on the left side (s*u instead of u*s).
		return Vector([v*x for x in u.elem],False)


	def __imul__(u,s):
		ue=u.elem
		for i in range(u.elems): ue[i]*=s
		return u


	@staticmethod
	def cross(vecarr):
		n=len(vecarr)+1
		ret=Vector(n)
		m=Matrix(n-1,n-1)
		for i in range(n):
			me,k=m.elem,0
			for v in vecarr:
				for c in range(n):
					if c==i: continue
					me[k]=v[c]
					k+=1
			ret[i]=abs(m)*(1,-1)[i&1]
		return ret


	def sqr(u):
		s=0.0
		for x in u.elem: s+=x*x
		return s


	def __abs__(u):
		return math.sqrt(u.sqr())


	def norm(u): return Vector(u).normalize()


	def normalize(u):
		mag=abs(u)
		if mag<=1e-10: u.randomize()
		else: u*=1.0/mag
		return u


class Transform(object):
	# A class to easily hold spatial transformation information.


	def __init__(self,off,angs=None,scale=1.0):
		if isinstance(off,Transform):
			self.off=Vector(off.off)
			self.mat=Matrix(off.mat)
		else:
			self.off=Vector(off)
			dim=len(self.off)
			if angs is None: angs=[0]*(dim*(dim-1)//2)
			self.mat=Matrix(dim,dim).one().rotate(angs)*scale


	def apply(self,v):
		# Transform a vector or another transform.
		if isinstance(v,Vector):
			return self.mat*v+self.off
		t=Transform(v)
		t.mat=self.mat*t.mat
		t.off=self.mat*t.off+self.off
		return t


	def rotate(self,v):
		return self.mat*v


	def inv(self):
		# Return the inverse transform.
		#
		#      A*x+b=y
		#      A^-1*(y-b)=x
		#      (A^-1)*y+(-A^-1*b)=x
		#
		inv=Transform(len(self.off))
		inv.mat=self.mat.inv()
		inv.off=-(inv.mat*self.off)
		return inv


#---------------------------------------------------------------------------------
# Meshes
#---------------------------------------------------------------------------------


class Ray(object):
	def __init__(self,pos,dir):
		# The min distance value can cause artifacts if it's too low.
		self.pos=pos
		self.dir=dir
		self.inv=Vector(dir)
		self.swap=0
		self.min=1e-4
		self.max=float("inf")
		self.dot=float("inf")
		self.face=None
		self.facenorm=None
		self.facemat=None


	def precalc(self):
		# Setup the ray for raytracing.
		self.face=None
		self.facenorm=None
		self.facemat=None
		# If the ray direction is negative along a BVH node's dividing axis,
		# then the node will want to swap its children.
		inv,dir,swap=self.inv,self.dir,0
		for i in range(len(dir)):
			d=dir[i]
			swap|=(d>0.0)<<i
			if abs(d)>1e-10: inv[i]=1.0/d
			else: inv[i]=float("inf")
		self.swap=swap
		self.dot=float("inf")


class MeshMaterial(object):
	# All that a material needs to tell us is what direction to go next and what color
	# to apply.


	def __init__(self,color,luminosity=0.0,reflectprob=1.0,diffusion=1.0,refractprob=0.0,refractindex=1.0,scatterlen=float("inf")):
		self.color=list(color)
		self.luminosity=luminosity
		self.reflectprob=reflectprob
		self.diffusion=diffusion
		self.refractprob=refractprob
		self.refractindex=refractindex
		self.scatterlen=scatterlen
		self.absorbprob=0.01


class MeshVertex(object):
	def __init__(self,pos,id):
		self.pos=pos
		self.id=id


class MeshFace(object):
	def __init__(self,vertarr,mat):
		# Set up the face and its normal.
		self.mat=mat
		self.vertarr=vertarr
		self.calcnorm()

	def calcnorm(self):
		# Calculate the face's normal and barycentric vectors.
		vertarr=self.vertarr
		verts=len(vertarr)
		arr=[vertarr[i].pos-vertarr[0].pos for i in range(1,verts)]
		if verts==0: self.norm=Vector(verts)
		else: self.norm=Vector.cross(arr).normalize()
		# Precompute vectors for the barycentric coordinates of the face.
		#
		#      p=p-v0, v1=v1-v0, v2=v2-v0
		#      u1*v1+u2*v2=p
		#      u1*(v1*v1)+u2*(v1*v2)=(v1*p)
		#      u1*(v1*v2)+u2*(v2*v2)=(v2*p)
		#
		dim=verts-(verts>0)
		a=Matrix(dim,dim)
		for r in range(dim):
			for c in range(r+1):
				d=arr[r]*arr[c]
				a.elem[r*dim+c]=d
				a.elem[c*dim+r]=d
		try:
			self.bary=(a.inv()*Vector(arr,False)).elem
		except ZeroDivisionError:
			self.bary=[Vector(dim+1) for i in range(dim)]

	def intersect(self,ray):
		# Return the distance from the ray origin to the face. Return false if the ray
		# misses.
		# First, project the ray onto the face's plane. We have (pos+u*dir)*norm=v0*norm,
		# thus u=-(pos-v0)*norm/(dir*norm).
		dot=ray.dir*self.norm
		if abs(dot)<=1e-10: return False
		p=ray.pos-self.vertarr[0].pos
		dist=-(p*self.norm)/dot
		# If the new distance is within +-eps, and the new face is more pointed away from
		# the ray, skip this new face.
		min,dif=ray.min,dist-ray.max
		if dist<min or dif>=min: return False
		if dif>-min and dot>ray.dot: return False
		p+=ray.dir*dist
		# Make sure the barycentric coordinates of the point are within the face.
		s=0.0
		for bary in self.bary:
			u=bary*p
			s+=u
			if u<0.0 or s>1.0: return False
		ray.max=dist
		ray.dot=dot
		ray.face=self
		ray.facenorm=self.norm
		ray.facemat=self.mat
		return True


class Mesh(object):
	def __init__(self,dim,mat=None,transform=None):
		self.dim=dim
		self.vertarr=[None]
		self.verts=0
		self.facearr=[None]
		self.faces=0
		self.instarr=[None]
		self.insts=0
		self.updated=1
		self.bvh=BVH(self)
		if isinstance(dim,str):
			self.load(dim,mat,transform)


	def load(self,path,mat=None,transform=None):
		# Load from a Wavefront OBJ file.
		self.clear()
		self.dim=3
		verts=self.verts-1
		data=""
		with open(path,"r") as f: data=f.read()
		for line in data.split("\n"):
			line=line.lower()
			c=line[0] if line else ""
			if c=="v":
				coord=[float(x) for x in line.split()[1:]]
				self.addvertex(coord,transform)
			elif c=="f":
				faces=[verts+int(x) for x in line.split()[1:]]
				self.addface(faces,mat)


	def save(self,path):
		# Save to a Wavefront OBJ file.
		with open(path,"w") as f:
			idmap=dict()
			for i in range(self.verts):
				vert=self.vertarr[i]
				idmap[vert.id]=str(i+1)
				arr=["{0:.9f}".format(x) for x in vert.pos]
				f.write("v "+" ".join(arr)+"\r\n")
			for i in range(self.faces):
				arr=[idmap[v.id] for v in self.facearr[i].vertarr]
				f.write("f "+" ".join(arr)+"\r\n")


	def clear(self):
		self.verts=0
		self.faces=0
		self.insts=0
		self.updated=1
		self.bvh=BVH(self)


	def addmesh(self,mesh,mat=None,transform=None,instanced=True):
		# Copy the faces from another mesh into this one. If instanced=True, only create a
		# pointer to that mesh instead.
		if instanced:
			arr,insts=self.instarr,self.insts
			if insts>=len(arr): arr+=[None]*insts
			arr[insts]=MeshInstance(mesh,transform,mat)
			self.insts+=1
		else:
			# Copy vertices, faces, and materials.
			vmap=dict()
			for i in range(mesh.verts):
				v=mesh.vertarr[i]
				vmap[v.id]=self.addvertex(v.pos,transform).id
			for i in range(mesh.faces):
				face=mesh.facearr[i]
				arr=[vmap[v.id] for v in face.vertarr]
				self.addface(arr,mat)


	def addvertex(self,coord,transform=None):
		# Add a vertex and return it.
		coord=Vector(coord)
		if transform: coord=transform.apply(coord)
		arr,verts=self.vertarr,self.verts
		if verts>=len(arr): arr+=[None]*verts
		arr[verts]=MeshVertex(coord,verts)
		self.verts+=1
		return arr[verts]


	def addface(self,vertarr,mat):
		# Add a face and return it.
		assert(len(vertarr)<=self.dim)
		arr,faces=self.facearr,self.faces
		if faces>=len(arr): arr+=[None]*faces
		varr=[(v if isinstance(v,MeshVertex) else self.vertarr[v]) for v in vertarr]
		arr[faces]=MeshFace(varr,mat)
		self.faces+=1
		return arr[faces]


	def addcube(self,sidearr,mat,transform=None):
		# Create an N-dimensional cube.
		dim,vbase=self.dim,self.verts
		sides=len(sidearr)
		assert(sides<=dim)
		# Create the vertices of the cube centered around the origin.
		for i in range((dim>0)<<sides):
			v=Vector(dim)
			for j in range(sides): v[j]=sidearr[j]*(((i>>j)&1)-0.5)
			self.addvertex(v,transform)
		# If the cube can be contained in a single simplex, use a simplex instead.
		if self.verts-vbase<=dim:
			self.addface(range(vbase,self.verts),mat)
			return
		# If we're in a high dimension with a low dimension cube, limit the dimensionality
		# of the simplexes we use.
		sim=min(dim-1,sides)
		combos,perm=1,[0]*sim
		for i in range(sim): combos*=i+1
		for f in range(2*dim):
			# Given a fixed axis and side of the cube, generate the dim-1 dimensioned surface.
			# Each surface will be made up of sim! simplexes.
			axis=f>>1
			base=vbase+((f&1)<<axis)
			for combo in range(combos):
				for i in range(sim):
					j=combo%(i+1)
					combo//=i+1
					perm[i],perm[j]=perm[j],1<<(i+(i>=axis))
				# Find the vertices of the simplex. If the number of permutation inversions is
				# odd, then the sign of the normal will be negative.
				vertarr=[base]*(sim+1)
				for i in range(sim): vertarr[i+1]=vertarr[i]+perm[i]
				if vertarr[sim]>=self.verts: continue
				inv=(sum(sum(perm[j]>perm[i] for j in range(i)) for i in range(sim))^axis^f)&1
				if dim>1 and inv==0: vertarr[0],vertarr[1]=vertarr[1],vertarr[0]
				face=self.addface(vertarr,mat)
				if dim==1 and inv==0: face.norm=-face.norm


	def addsphere(self,pos,rad,maxfaces,mat,transform=None):
		# Generates a sphere with at most maxfaces number of faces. Begin with a line and
		# rotate it in "segs" segments to create a circle. Rotate the circle in segments
		# to create a sphere, etc. This will create square faces that we tessellate like
		# the face of a cube.
		dim=self.dim
		trans=Transform(pos,scale=rad)
		if transform: trans=transform.apply(trans)
		# Dimensions 0 and 1 are special cases.
		if dim<2 and maxfaces>dim:
			self.addcube([2.0]*dim,mat,trans)
			return
		# Find out how many segments we can support given maxfaces. We need at least 4
		# segments to create an enclosed volume.
		segs,hsegs,faces=0,0,0
		while faces<=maxfaces:
			segs,hsegs,faces=segs+2,hsegs+1,segs+4
			for i in range(dim-2):
				faces*=segs+(hsegs-1)*i
		if segs<4: return
		dim1=dim-1
		dim2=1<<dim1
		# There are several different rotations that can reach the same point on a sphere.
		# Reduce a given angle (with an offset) to a standard form. Also, generate the
		# vertex if it's new.
		vertmap=dict()
		def getangs(angs,offset):
			# Reduce angle to standard form. ang0=pi*2-ang0, ang1+=pi/2.
			std,carry=0,0
			for i in range(dim1):
				a=(angs//den[i]+carry+((offset>>i)&1))%segs
				if carry<0: a=0
				elif a==0 or a==hsegs: carry=-1
				else: carry=0
				if a>hsegs and i<dim-2:
					a=segs-a
					carry=hsegs
				std+=a*den[i]
			# Generate the vertex if it's new.
			if not std in vertmap:
				v=Vector([1.0]*dim)
				for d in range(dim1):
					u=((std//den[d])%segs)*(math.pi*2.0/segs)
					v[d+1]=v[d]*math.sin(u)
					v[d]*=math.cos(u)
				vertmap[std]=self.addvertex(v.normalize(),trans).id
			return std
		# Determine if a face is valid and unique.
		faceset=set()
		def facevalid(varr):
			varr=tuple(sorted(varr))
			for i in range(1,dim):
				if varr[i]==varr[i-1]: return False
			if varr in faceset: return False
			faceset.add(varr)
			return True
		# Loop through all possible square faces and tessellate them.
		den=[1]*dim1
		cube=Mesh(dim)
		cube.addcube(den,None)
		for i in range(dim-3,-1,-1): den[i]=den[i+1]*segs
		basethres=segs if dim==2 else den[0]*hsegs
		for base in range(basethres):
			vertarr=[getangs(base,offset) for offset in range(dim2)]
			vertarr.sort()
			vertarr=[vertmap[p] for p in vertarr]
			# Certain faces need to be flipped to point outward.
			inv=((base+1)%segs==0)==((dim&2)>0)
			for f in range(cube.faces):
				idarr=cube.facearr[f].vertarr
				varr=[vertarr[v.id] for v in idarr]
				varr[0],varr[inv]=varr[inv],varr[0]
				if facevalid(varr): self.addface(varr,mat)


	def buildbvh(self):
		if self.updated:
			self.updated=0
			self.bvh.build()


	def raypick(self,ray):
		# Finds the nearest surface that the ray intersects. Surface information is
		# returned in the ray object.
		if self.updated: self.buildbvh()
		return self.bvh.raypick(ray)


class MeshInstance(object):
	# A mesh instance serves as a pointer to a mesh instead of a direct copy. This
	# saves on time and memory.


	def __init__(self,mesh,transform=None,mat=None):
		self.mesh=mesh
		self.mat=mat
		if transform is None:
			transform=Transform(mesh.dim)
		self.transform=Transform(transform)
		self.inv=transform.inv()


	def intersect(self,ray):
		# Apply the inverse instance transform to put the ray in the mesh's local space.
		# Don't normalize the direction here or distance metrics will be thrown off.
		nray=Ray(self.inv.apply(ray.pos),self.inv.rotate(ray.dir))
		nray.min=ray.min
		nray.max=ray.max
		self.mesh.raypick(nray)
		if nray.face:
			ray.face,ray.facemat,ray.max=nray.face,nray.facemat,nray.max
			ray.facenorm=self.transform.rotate(nray.facenorm).normalize()
			if self.mat: ray.facemat=self.mat


#---------------------------------------------------------------------------------
# Bounding Volume Hierarchy
#---------------------------------------------------------------------------------


class BVHNode(object):
	DIVIDE,FACE,INSTANCE=0,1,2


	def __init__(self,dim):
		self.parent=None
		self.left=None
		self.right=None
		self.bbmin=Vector(dim)
		self.bbmax=Vector(dim)
		self.type=BVHNode.DIVIDE
		self.cost=0.0
		self.axis=0


	def intersect(self,ray):
		# Project the box onto the ray. The intersection of all projections will give us
		# the range of u where the ray intersects the box. If the intersection of all the
		# ranges is null, then the ray misses the box.
		#
		#             b3
		#              '. b2
		#              . '.              ray=pos+u*dir
		#              .  .'.            ranges: [b0,b1] [b2,b3]
		#              .  .  '.
		#      +----------+. . '.b1
		#      |          |      '.
		#      |          |        '.
		#      |          |          '.
		#      |          |            '.
		#      +----------+. . . . . . . '.b0
		#
		# Want pos[i]+u*dir[i]=box[i], thus u=(box[i]-pos[i])/dir[i].
		# We spend almost half of our time in this function, so optimize it.
		raypos,rayinv=ray.pos.elem,ray.inv.elem
		bbmin,bbmax=self.bbmin.elem,self.bbmax.elem
		u0,u1,i=ray.min,ray.max,len(bbmin)
		while i:
			i-=1
			p,d=raypos[i],rayinv[i]
			b0=(bbmin[i]-p)*d
			b1=(bbmax[i]-p)*d
			if b0>b1: b0,b1=b1,b0
			if u0<b0: u0=b0
			if u1>b1: u1=b1
			if u0>u1: return False
		return True


	def aabbinit(self):
		# Initialize the node's bounding box, area, and cost.
		#
		# Worst case complexity for a face intersection test is n^2, and for a box is n.
		# Thus, consider a box collision test to take n/n^2~=1/(n+1) relative operations.
		b0,b1=self.bbmin,self.bbmax
		dim=len(b0)
		for i in range(dim):
			b0[i]=float("inf")
			b1[i]=-float("inf")
		self.cost=1.0/(dim*dim+1.0)
		if self.type==BVHNode.DIVIDE:
			# If the node has children, merge them into the node's bounding box.
			l,r=self.left,self.right
			if l: self.aabbmerge(l)
			if r: self.aabbmerge(r)
			return
		elif self.type==BVHNode.FACE:
			# The node contains a face.
			self.cost+=1.0
			face=self.left
			varr=[v.pos for v in face.vertarr]
		elif self.type==BVHNode.INSTANCE:
			# The node contains a mesh instance. Transform the bounding box of the mesh to
			# find the instance's bounding box.
			inst=self.left
			root=inst.mesh.bvh.root
			# Add 2 to the cost for creating a new ray.
			self.cost+=root.cost+2.0
			m=(root.bbmin,root.bbmax)
			v,varr=Vector(dim),[None]*(1<<dim)
			for i in range(len(varr)):
				for j in range(dim):
					v[j]=m[(i>>j)&1][j]
				varr[i]=inst.transform.apply(v)
		# Calculate the node's bounding box.
		for v in varr:
			for i in range(dim):
				x=v[i]
				if b0[i]>x: b0[i]=x
				if b1[i]<x: b1[i]=x


	def aabbmerge(self,other):
		b0,b1=self.bbmin.elem,self.bbmax.elem
		o0,o1=other.bbmin.elem,other.bbmax.elem
		for i in range(len(b0)):
			if b0[i]>o0[i]: b0[i]=o0[i]
			if b1[i]<o1[i]: b1[i]=o1[i]
		self.cost+=other.cost


	def aabbarea(self):
		# The probability of a ray intersecting a volume inside another volume is
		# surface_area_inside/surface_area_outside. Surface area is an n-1 dimensional
		# volume in n dimensional space. That is, fix one axis as constant, and compute
		# the volume of the non-fixed axis.
		#
		# For 2D, we'll mostly be doing point tests, so return the volume.
		b0,b1=self.bbmin.elem,self.bbmax.elem
		dim,area=len(b0),1.0
		if dim==2:
			return (b1[1]-b0[1])*(b1[0]-b0[0])
		elif dim>=3:
			vol=b1[0]-b0[0];
			for i in range(1,dim):
				dif=b1[i]-b0[i]
				area=area*dif+vol
				vol*=dif
		return area


class BVH(object):
	def __init__(self,mesh):
		self.mesh=mesh
		self.root=None
		self.nodes=0
		self.nodearr=[]
		self.sortarr=[]
		self.tmparr=[]


	def build(self):
		# Create a bounding volume hierarchy for a given mesh. The BVH works by dividing
		# up the mesh faces into different axis-aligned boxes. The BVH is built so that if
		# a ray misses a node's box, we know that the ray will miss all of the node's
		# children and they don't need to be tested.
		#
		#      +--------------------+
		#      |            +--+    |
		#      | +----+     |  |    |
		#      | |    |     +--+    |
		#      | |    |             |
		#      | +----+             |
		#      +--------------------+
		#
		mesh=self.mesh
		dim=mesh.dim
		facearr,faces=mesh.facearr,mesh.faces
		instarr,insts=mesh.instarr,mesh.insts
		objects=faces+insts
		self.root=None
		self.nodes=0
		if objects==0: return
		# Create an array of all active faces and instances.
		if objects>len(self.tmparr):
			self.nodearr=[BVHNode(dim) for i in range(objects*2-1)]
			self.sortarr=[[None]*objects for j in range(dim)]
			self.tmparr=[None]*objects
		nodearr=self.nodearr
		nodes=0
		for i in range(objects):
			node=nodearr[nodes]
			if i<faces:
				node.left=facearr[i]
				node.type=BVHNode.FACE
			else:
				inst=instarr[i-faces]
				inst.mesh.buildbvh()
				if inst.mesh.bvh.root is None: continue
				node.left=inst
				node.type=BVHNode.INSTANCE
			node.aabbinit()
			nodes+=1
		if nodes==0: return
		self.nodes=nodes*2-1
		# Sort the nodes along each axis by their AABB centers.
		for i in range(dim):
			arr=self.sortarr[i]
			for j in range(nodes):
				node=nodearr[j]
				node.axis=node.bbmin[i]+node.bbmax[i]
				arr[j]=node
			arr.sort(key=lambda x: x.axis)
		# Move the child nodes to the end of the array.
		for i in range(nodes):
			j=nodes*2-2-i
			nodearr[i],nodearr[j]=nodearr[j],nodearr[i]
		# Make the first node the root. If it's not the only node, set up its partition.
		node=nodearr[0]
		self.root=node
		node.parent=None
		if nodes>1:
			node.left=0
			node.right=nodes
		# Begin dividing nodes.
		newpos=1
		for npos in range(nodes-1):
			node=nodearr[npos]
			left,right=node.left,node.right
			# Try and find an axis to divide the nodes along.
			node.type=BVHNode.DIVIDE
			node.left=None
			node.right=None
			# Find the axis that best divides the nodes.
			minaxis,minhalf,mincost=0,left+1,float("inf")
			for axis in range(dim):
				sortarr=self.sortarr[axis]
				node.aabbinit()
				for i in range(left+1,right):
					node.aabbmerge(sortarr[i-1])
					prob=node.aabbarea()*node.cost
					if prob>=mincost: break
					sortarr[i].axis=prob
				node.aabbinit()
				for j in range(right-1,left,-1):
					node.aabbmerge(sortarr[j])
					prob=node.aabbarea()*node.cost
					if prob>=mincost: break
					cost=sortarr[j].axis+prob
					if mincost>cost and j<i:
						mincost=cost
						minhalf=j
						minaxis=axis
			# For each axis, parition the nodes based on whether they're in the left half or
			# right half or the splitting axis.
			node.axis=1<<minaxis
			tmp=self.tmparr
			sortarr=self.sortarr[minaxis]
			for i in range(left,right):
				sortarr[i].axis=i<minhalf
			for axis in range(dim):
				if axis==minaxis: continue
				sortarr=self.sortarr[axis]
				lpos,rpos=left,minhalf
				for i in range(left,right):
					m=sortarr[i]
					if m.axis:
						tmp[lpos]=m
						lpos+=1
					else:
						tmp[rpos]=m
						rpos+=1
				for i in range(left,right):
					sortarr[i]=tmp[i]
			# If the left side has multiple nodes, queue it for further dividing.
			if minhalf-left==1:
				work=sortarr[left]
			else:
				work=nodearr[newpos]
				newpos+=1
				work.left=left
				work.right=minhalf
			work.parent=node
			node.left=work
			# If the right side has multiple nodes, queue it for further dividing.
			if right-minhalf==1:
				work=sortarr[minhalf]
			else:
				work=nodearr[newpos]
				newpos+=1
				work.left=minhalf
				work.right=right
			work.parent=node
			node.right=work
		# Rebuild the AABBs from the bottom up.
		for i in range(nodes-2,-1,-1):
			nodearr[i].aabbinit()


	def raypick(self,ray):
		# Finds the nearest surface that the ray intersects. If (swap&axis)!=0, then the
		# sign of the ray is negative along that axis, so switch the children.
		ray.precalc()
		swap=ray.swap
		node=self.root
		prev=None
		while node:
			next=node.parent
			if not (prev is next) or node.intersect(ray):
				if node.type==BVHNode.DIVIDE:
					# This is a dividing node. Determine which child to visit first using the dividing
					# axis and sign of the ray.
					if swap&node.axis:
						l=node.left
						r=node.right
					else:
						l=node.right
						r=node.left
					if prev is next:
						next=l
					elif prev is l:
						next=r
				else:
					# We are intersecting a mesh instance or a face.
					node.left.intersect(ray)
			prev=node
			node=next


#---------------------------------------------------------------------------------
# Scenes
#---------------------------------------------------------------------------------


class Scene(object):
	def __init__(self,dim,width,height):
		self.dim=dim
		# Epsilons are needed to prevent a ray from re-intersecting a face.
		self.eps=1e-4 if sys.float_info.epsilon>1e-10 else 1e-8
		self.raysperpixel=128
		self.maxbounces=16
		self.imgwidth=width
		self.imgheight=height
		self.imgrgb=[0.0]*(3*width*height)
		self.mesh=Mesh(dim)
		angs=dim*(dim-1)//2
		self.setcamera([0.0]*dim,[0.0]*angs)


	def __getattr__(self,name):
		# Pass any unknown commands to the mesh.
		return getattr(self.mesh,name)


	def raytrace(self,ray,rgb):
		# Shoot a ray into the scene, and follow it as it bounces around. Track what
		# material we're inside of for ambient properties of the medium.
		# Situations to consider:
		#
		#      Coplanar faces will be fairly common.
		#      Rays may start inside a mesh.
		#      Inside-out geometry will define an infinitely large space.
		#
		rand=Vector(self.dim)
		uniform=random.random
		ambient=None
		col=[1.0,1.0,1.0]
		ret=[0.0,0.0,0.0]
		inf=float("inf")
		for bounce in range(self.maxbounces,0,-1):
			# Perform scattering before interacting with the face. Use the Beer-Lambert
			# scattering law to limit scattering length.
			scatterlen=ambient.scatterlen if ambient else inf
			if scatterlen<inf: scatterlen*=-math.log(uniform())
			ray.min=self.eps
			ray.max=scatterlen
			# Find the closest face the ray collides with. If we can't find one, or the ray
			# gets absorbed, abort.
			self.mesh.raypick(ray)
			dir,dist=ray.dir,ray.max
			# If we didn't hit anything or scatter, we escape into the void.
			if dist>=inf: break
			norm,mat=ray.facenorm,ray.facemat
			if mat is None: mat=ambient
			if mat is None: break
			if uniform()<mat.absorbprob: break
			cosi=0.0 if norm is None else dir*norm
			inside=cosi>0.0
			if inside==bounce: break
			ray.pos+=dir*dist
			# If we're performing subsurface scattering, randomly bounce around.
			if dist>=scatterlen:
				dir.randomize()
				continue
			if inside:
				# We're inside and pointing out.
				norm=-norm
				ambient=mat
			else:
				# We're outside and pointing in.
				cosi=-cosi
				matcol=mat.color
				matlum=mat.luminosity
				for i in range(3):
					col[i]*=matcol[i]
					ret[i]+=matlum*col[i]
			refract=0
			if uniform()<mat.refractprob:
				# Perform refraction and determine if we have total internal reflection.
				ior=mat.refractindex
				if not inside: ior=1.0/ior
				disc=1.0-ior*ior*(1.0-cosi*cosi)
				if disc>0.0:
					cost=math.sqrt(disc)
					# Fresnel reflectance equations.
					a=ior*cost;rs=(cosi-a)/(cosi+a)
					a=ior*cosi;rp=(a-cost)/(a+cost)
					prob=1.0-(rs*rs+rp*rp)*0.5
					refract=uniform()<prob
			if refract:
				# Refraction.
				dir*=ior
				dir+=norm*(ior*cosi-cost)
				ambient=None if inside else mat
			elif uniform()<mat.reflectprob:
				# Lambertian scattering.
				rand.randomize()
				if rand*norm<0.0: rand=-rand
				dir+=norm*(2.0*cosi)
				dir+=(rand-dir)*mat.diffusion
			dir.normalize()
		for i in range(3): rgb[i]+=ret[i]


	def setcamera(self,pos,angs,fov=90.0):
		# Set up the camera based on the number of dimensions.
		#
		#   (-x, y,-1)                       (x, y,-1)               2*x
		#             +---------------------+               +-------------------+  }
		#             |                     |                '.               .'   }
		#             |                     |                  '.           .'     }
		#             |                     |                    '.       .'       } -1
		#             |                     |                      '.   .'         }
		#             +---------------------+                        '.'           }
		#   (-x,-y,-1)                       (x,-y,-1)               pos
		#
		# x=tan(fov*pi/360)
		# y=x*height/width
		#
		# Dimension effects
		# 1: Camera shoots rays in direction -1. All pixels will be the same.
		# 2: Pixels will be mirrored along the y axis. Will look like a ray scanned maze.
		# 3: 2D plane projected at z=-1.
		self.campos=Vector(pos)
		dim=self.dim
		x,y,z=Vector(dim),Vector(dim),Vector(dim)
		if dim>0: z[2 if dim>2 else dim-1]=-1.0
		if dim>1: x[0]=math.tan(fov*math.pi/360.0)
		if dim>2: y[1]=-x[0]*float(self.imgheight)/self.imgwidth
		rot=Matrix(dim,dim).one().rotate(angs)
		self.cambl=rot*(-x-y+z)
		self.camu=(rot*x)*(2.0/self.imgwidth)
		self.camv=(rot*y)*(2.0/self.imgheight)


	def render(self,fast=False,progress=False):
		# Render the scene to a series of RGB values.
		# Divide the camera space into a grid of pixels. Then, shoot several rays into
		# each pixel and use the average value as the pixel's color.
		uniform=random.random
		cambl,camu,camv=self.cambl,self.camu,self.camv
		campos,imgwidth=self.campos,self.imgwidth
		imgrgb,pixels=self.imgrgb,imgwidth*self.imgheight
		ray=Ray(campos,cambl)
		rpp=self.raysperpixel
		norm=1.0 if rpp<1 or fast else 1.0/rpp
		if progress: progress=(pixels+9999)//10000
		for i in range(pixels):
			# Print progress every pixel if we've been asked to.
			if progress and i%progress==0:
				sys.stdout.write("\rprogress: {0:.2f}%".format(i*100.0/pixels))
				sys.stdout.flush()
			x,y,rgb=i%imgwidth,i//imgwidth,[0.0]*3
			if fast:
				# Fast render. Use the color of the first face we intersect.
				u,v=x+0.5,y+0.5
				ray.pos=Vector(campos)
				ray.dir=(cambl+camu*u+camv*v).normalize()
				ray.max=float("inf")
				self.mesh.raypick(ray)
				if ray.facemat: rgb=ray.facemat.color
			else:
				# High quality render. Let the light bound around the scene.
				for r in range(rpp):
					u,v=x+uniform(),y+uniform()
					ray.pos=Vector(campos)
					ray.dir=(cambl+camu*u+camv*v).normalize()
					self.raytrace(ray,rgb)
			for j in range(3): imgrgb[i*3+j]=rgb[j]*norm
		if progress: print("\rprogress: 100.00%")


	def savebmp(self,path):
		# Save the scene to a bitmap image file. Perform gamma correction.
		f=open(path,"wb")
		width,height,buf=self.imgwidth,self.imgheight,self.imgrgb
		# Write the bitmap header.
		padding=(-width*3)&3
		bmpsize=(width*3+padding)*height
		info=(bmpsize+54,0,0x36,0x28,width,-height,
			 0x180001,0,bmpsize,0,0,0,0)
		f.write(bytearray([0x42,0x4d]))
		for i in info:
			arr=(i&255,(i>>8)&255,(i>>16)&255,(i>>24)&255)
			f.write(bytearray(arr))
		# Write the RGB values.
		pad=bytearray(padding)
		rgb=bytearray(3)
		i=0
		def toint(x): return int(min(256*max(x,0.0)**0.45,255.0))
		for y in range(height):
			for x in range(width):
				rgb[2]=toint(buf[i]);i+=1
				rgb[1]=toint(buf[i]);i+=1
				rgb[0]=toint(buf[i]);i+=1
				f.write(rgb)
			f.write(pad)
		f.close()


#---------------------------------------------------------------------------------
# Example Scene
#---------------------------------------------------------------------------------


if __name__=="__main__":
	# Render a quick, low quality scene demonstrating glass, mirrors, and subsurface
	# scattering. Low-end CPU times:
	# PyPy  : 20 minutes
	# python: 2 hours
	import time
	start=time.time()
	highquality=sys.argv[-1]=="-HQ"
	pixels,rays,sphere=((300,1<<7,1<<13),(600,1<<16,1<<19))[highquality]
	path="render3d.bmp"
	hpi=math.pi*0.5
	sc=Scene(3,pixels,pixels)
	sc.raysperpixel=rays
	sc.setcamera((278,273,800),(0,0,0),37.5)
	lightmat=MeshMaterial((1.0,1.0,1.0),25.0)
	wallmat =MeshMaterial((0.9,0.9,0.9))
	rightmat=MeshMaterial((0.2,0.9,0.2))
	leftmat =MeshMaterial((0.9,0.2,0.2))
	mirmat  =MeshMaterial((1.0,1.0,1.0),0.0,1.0,0.0)
	submat  =MeshMaterial((0.4,0.4,0.9),0.0,0.0,0.0,1.0,1.0,5.0)
	glassmat=MeshMaterial((1.0,1.0,1.0),0.0,1.0,0.0,1.0,1.5)
	sc.addcube((130,0.2,105),lightmat,Transform((278,548.7,-279.5)))
	sc.addcube((556,559.2),wallmat,Transform((278,0,-279.6),(0,0,hpi)))
	sc.addcube((556,559.2),wallmat,Transform((278,548.8,-279.6),(0,0,-hpi)))
	sc.addcube((556,-548.8),wallmat,Transform((278,274.4,-559.2)))
	sc.addcube((559.2,548.8),leftmat,Transform((0,274.4,-279.6),(0,hpi,0)))
	sc.addcube((559.2,548.8),rightmat,Transform((556,274.4,-279.6),(0,-hpi,0)))
	sc.addcube((166,166,166),submat,Transform((371,83,-168.5),(0,0.2856,0)))
	sc.addsphere((250,280,-370),100,sphere,mirmat)
	sc.addsphere((135,125,-125),80,sphere,glassmat)
	print("rendering {0} triangles".format(sc.faces))
	sc.render(False,True)
	print("saving image to "+path)
	sc.savebmp(path)
	print("time: {0:.6f}".format(time.time()-start))

