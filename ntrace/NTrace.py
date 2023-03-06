"""

NTrace.py - v1.29

Copyright 2020 Alec Dee - MIT license - SPDX: MIT
alecdee.github.io - akdee144@gmail.com


--------------------------------------------------------------------------------
A N-Dimensional Ray Tracer


Notes:
* The scene can have any number of spatial dimensions.
* Most processing time is spent in BVH.raypick() and BVHNode.intersect().
* Epsilon for double precision is 1e-8. For single precision it's 1e-4.
* Mesh instancing is supported.
* Textures are not supported.
* Wavefront OBJ mesh files are supported.
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


Simplify text generation. Reduce to 5kb.
Use quadtree/octtree.
	Build from bottom up.
	How to test if simplex / cube overlap?
	Might not need to rebuild tree when adding or deleting.
	Can terminate when first collision is found.
Add denoising.
Add recalcnorm() and applytransform() to mesh.
Add vert/face unique id tracking. Add delete/get.


"""

import math,random,sys,struct


#---------------------------------------------------------------------------------
# Algebra
#
# Helper classes for matrix/vector linear algebra.


class Matrix(object):
	def __init__(self,rows=None,cols=None,copy=True):
		if isinstance(rows,Matrix):
			# Matrix( mat )
			cols=(rows.rows,rows.cols)
			rows=rows.elem
		if hasattr(rows,"__getitem__"):
			# Matrix( elem, (rows,cols) )
			elem=rows
			if cols: rows,cols=cols
			elems=rows*cols
			if copy: elem=list(elem)
			assert(len(elem)==elems)
		elif rows is not None:
			# Matrix( rows, cols )
			if cols is None: cols=0
			elem=[0]*(rows*cols)
		else:
			rows,cols,elem=0,0,[]
		self.elem,self.elems=elem,rows*cols
		self.rows,self.cols=rows,cols


	def __str__(self):
		"""String representation. Each row and column are padded individually."""
		rows,cols=self.rows,self.cols
		rpad,cpad=[1]*rows,[0]*cols
		cell=[[0]*cols for r in range(rows)]
		for r in range(rows):
			for c in range(cols):
				# Convert the element value into a string and split it by eol's.
				s=self.elem[r*cols+c]
				if isinstance(s,float):
					s="{0:.6f}".format(s)
				s=str(s).split("\n")
				# Find the dimensions of the string.
				h,w=len(s),max(map(len,s))
				cell[r][c]=(h,w,s)
				rpad[r]=max(rpad[r],h)
				cpad[c]=max(cpad[c],w)
		rsep,csep="",(" ",",")
		if rpad and max(rpad)>1:
			rsep="\n["+" "*(sum(cpad)+cols*3-1)+"]"
			csep=("   "," , ")
		# Generate the output line-by-line.
		r,line,ret=0,0,""
		while r<rows:
			rp=rpad[r]
			sep=csep[line==(rp-1)//2]
			ret+="["
			for c in range(cols):
				h,w,s=cell[r][c]
				i=line-(rp-h)//2
				ret+=sep[(c==0)*2:]
				ret+=("" if i<0 or i>=h else s[i]).rjust(cpad[c])
			ret+=sep[2:]+"]"
			line=(line+1)%rp
			if line==0:
				r+=1
				if r<rows: ret+=rsep
			if r<rows: ret+="\n"
		return ret


	def __repr__(self):
		def rp(r): return "["+",".join([repr(e) for e in r])+"]"
		return "Matrix(["+",".join([rp(r) for r in self])+"])"


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
			elem[i*cols+i]=1
		return a


	def zero(a):
		"""Zeroize matrix A."""
		elem=a.elem
		for i in range(a.elems):
			elem[i]=0
		return a


	def __neg__(a):
		return Matrix([-e for e in a.elem],(a.rows,a.cols),False)


	def __mul__(a,b):
		if isinstance(b,Vector):
			# Vector A*v.
			arows,acols,i=a.rows,a.cols,0
			ae,be,ve=a.elem,b.elem,[0]*arows
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
			return 1
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
			elem=[0]*x
		else:
			elem=list(x) if copy else x
		self.elem=elem
		self.elems=len(elem)


	def __str__(self):
		return str(Matrix(self,(1,len(self)),False))


	def __repr__(self):
		return "Vector(["+",".join([repr(x) for x in self])+"])"


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
		for i in range(u.elems): ue[i]=0
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
			s,ve=0,v.elem
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
		s=0
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


	def __init__(self,off,angs=None,scale=None,mat=None):
		if isinstance(off,Transform):
			mat=off.mat
			off=off.off
		off=Vector(off)
		dim=len(off)
		if mat is None:
			mat=Matrix(dim,dim).one()
		else:
			mat=Matrix(mat)
		if not angs is None:
			mat=mat.rotate(angs)
		if not scale is None:
			if not hasattr(scale,"__getitem__"): scale=[scale]*dim
			for i in range(dim*dim): mat.elem[i]*=scale[i//dim]
		self.mat=mat
		self.off=off


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
		self.vertarr=list(vertarr)
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


	def loadobj(self,path,mat=None,transform=None):
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


	def saveobj(self,path):
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
		if not transform is None:
			coord=transform.apply(coord)
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
		vertarr=[0]*(sim+1)
		for f in range(2*dim):
			# Given a fixed axis and side of the cube, generate the dim-1 dimensioned surface.
			# Each surface will be made up of sim! simplexes.
			axis=f>>1
			for combo in range(combos):
				# If the number of permutation inversions is odd, invert the normal.
				inv=(axis^f)&1
				for i in range(sim):
					j=combo%(i+1)
					combo//=i+1
					inv^=(i-j)&1
					for k in range(i,j,-1): perm[k]=perm[k-1]
					perm[j]=1<<(i+(i>=axis))
				# Find the vertices of the simplex.
				vertarr[0]=vbase+((f&1)<<axis)
				for i in range(sim): vertarr[i+1]=vertarr[i]+perm[i]
				if vertarr[sim]>=self.verts: continue
				if dim>=2 and inv==0: vertarr[0],vertarr[1]=vertarr[1],vertarr[0]
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
					v[d  ]=v[d]*math.cos(u)
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


	def addtext(self,text,thickness,transform=None,mat=None):
		# Adds 3D text faces to the mesh.
		assert(self.dim==3)
		width=0.520093
		# Base 91 encoded vertices and faces.
		font={
			"!":("Wn+KU[VgI3VgFi+KPk]RT8^+W<_DY[bTYke5WxgAU<h^Q]iQLjiNIIhcF?g5D^dyDcc0F0a)I:^JLy]X","5'&4'54('3(43)(2)32*)1*20*10+*0,+/,0.,/.-,$!%$#!"),
			"\"":("j.+Kgs?1XZ?1V;+KHd+KFJ?193?16q+K","(&)('&$!%$#!"),
			"#":("w7WGe5WGb6hpT9hpW8WGB]WG?^hp3chp6bWG%MWG%MQz7gQz:]C8)XC8)X=j;c=j>J/vJ7/vGV=j]9=ja!/vl|/vj.=j{P=j{PC8i*C8f9Qzw7QzXDQz[5C8FQC8CcQz","132143576587/10:8;:98/.1-+*.@1#>&-@.>#<-A@'&A>;?&>A><;+-,4@??54!<#!=<1@4-*')'*-'A)('5?;%#&;85%$#"),
			"$":("Qp(!^T(![K04f&0gmj1Rmj8#d26wYw6DU>HBcFK%k<MWpCP2sBRgt~UbtoZ6r=_)mnc1iMd|cufUXjh&MThlJtri?*riAhhi57h&*|f{+#_%7Xa_CJb=H1MH:sJA4OH,0)E_,zBk+f?8,E;^/H7r3b597~3O?61YFA0VOm/yN/64B97e=_9];&<(;(?P<vA]@tC]J%F+O6bDYEa@^l_:b{]oeVZCeqVUcrT;a!RlZ.Q4S<Oa","K#!K$#J$KJ%$I%JI&%I'&('IH(IG)H)(HFLGL)GS)LS*)FMLFNMENFEONDOEDPODQPCQDCRQBRCBSRB*SA*BA+*@+A?+@?,+>^?^,?^-,>T^]-^].-[.]Z.[Z/.Y/ZY0/X0YW0XW10V1WU1V;=<U21T2U;>=;T>;2T;32;43;54:5;:6596:869876"),
			"%":("}C+K0rhp#Yhpo{+KP68nNd<QJb@8D$By=9Cz6aCw0gC*,fAm)G@%&T=/%/9p%*5m&Y2B(h0&+].'/U,J4]+9;8*oBX+DH>,xL;/*Nq1sP.4}C03$?H0f:-026{0X3n1s1M4N0k7v2-;p5r>.<%>a@^=NC_:gDP6{{~]<zWagwqdVt>fgo)hQhziDbCiAZKhQV0g.RweAP9bYNq^:NgYaP-U{SKR_X!P:]YO$c?NCj>NDp=O4tXPXwqRGzPU/{wXKopX>nVV/lFTei#SfdZScavT7]jUpZdY'Zs^S]Ras_Tc-dMd*hiczkyc(o+_dp7[=","687$!%$#!5865984954:93:4?:3>:?3@?>;:2@32A@=;>=<;2BA1B2I<=1CBI&<0C1H&I0DCH'&/D0G'H/EDG('F(G.E/.FE.(F-(.-)(,)-+),+*)[^]Z^[Y^ZY_^Ya_XaYhgXgaXgbaWhXWihfbgWjiebfecbdceWkjVkWscdsJcVlkUlVrJsrKJTlUTmlqKrTnmqLKTonpLqSoToLpSLoSMLRMSRNMQNRPNQPON"),
			"&":("vqJ3v/OstUTQqAYMna]9~uhpl?hpe5d9aie^V~h(KwiBA=i=:ehU4lg@.Zd~*qbN(w_P&pZs&kUb(!R[*:Oj-xLz2[JS:GGb3AB60P>9/_:N0d6A34376I0x;c.eAe-EH&,fPq,kV7-F['.Kag08ds29f~4Ph;7Hh.;2fd=xd2@M_NBoYhD|NHH]e6V1gER9hdJ45OY/6k[U9r_,>)apDQc'M@c$Rub2X#_b[K^.AZLD:|O?7HQ|5:UXX+8hW'6=TN4MPr39L$2pGd3%D'3qA65->e7]><:l?L=mByA'G<D#P=A*T^>pVu<uW~:|","ACBADCAED@EA@FE?F@?GF>G?fG>>gfeGfeHG>hgdHe=h>=ihcHdcIH=jibIc<j=bJI<kjrJb<lkqJr;l<qKJpKqpLK;mloLp:m;oMLnMo:nmnNM9n:9Nn9ON9PO8]9]P97]8[P]R#!7^]6^7Q#R6_^Q$#5_65a_4a5P$Q[$P[%$3a43Sa3TS[&%['&3UTZ'[2U32VU1V2Y)Z)'Z1WVX)YW)X1)W0)10*)(')/*0/+*.+/-+.-,+"),
			"'":("Xk+KVJ?1HS?1F;+K","$!%$#!"),
			"(":("aNzNVXuuLlo_E(i5>3_s:iV5:8O,;bGj?R@BCg;7I'64RT/Haf(6i|,WbO0dX96>Qg<+KzCXI'KGHZQZI_WNL{_LRTg7Y=m%cerXi|u~","-/.-0/-10,1-,21+2,*2+*32)3*)43(4)(54'5('65&6'&76&87%8&%98$9%$:9#:$#;:#!;"),
			")":("?N(9HD,qR23,Yw9WblA~f6JffhPxf-Uzd?[9_Cc}VUk|M&r|?:zR7!v0=BreEpm.M=fbQ{_iTeYHVJQCT|HTQyB=M2<9Fb6J>K0q7!,i",";#!:#;:$#9$:9%$8%98&%7&86&76'&5'65('5)(4)54*)3*43+*2+32,+1,21-,0-1/-0/.-"),
			"*":("q^CRl0HSSK@eU>O*IhO*KR@e4@HS/8CZH'=;/86m4o1tKc9oIh+KU>+KS<9ol01mqn6|Vx=B","-/.-0/021+-,*-+032*0-*30)'*3*''$3$!3)('&$'&%$#!$"),
			"+":("x4S-VJS-VJf;HSf;HSS-(kS-(kLgHSLgHS;eVJ;eVJLgx4Lg",")+*),+('&!-,,#!&#)%#&)#,%$#&)("),
			",":("56qK:^qDA6pKE>o>HJmiJFkaJ4h?F[eICXc&Bw_sCV]lEO[/H3Y|KlYCP5YCTJZ2W[[TZ+^U[db&]=e/[dhnY3l{Scq8KStPAxvQ5:w<",".0/.10-1.-21,2-,32+3,+43*4+*54)5*)65(6)'6('76&7'%7&%87$8%#8$;#!;8#;98;:9"),
			"-":("i^SD7@SD7@LNi^LN","#%$#!%"),
			".":("O>YWRmYtVVZpZ%]a]'a5]'d2YRfxV5hMS!i;NBi^IIi&F,gzC&f(AOcYAUaKBd^YE#[lH$ZSKIYk","4#!3#43$#2$32%$1%21&%0&1/&0/'&.'/.('-(.-)(,)-,*)+*,"),
			"/":("r.+K8cqs+<qsde+K","$!%$#!"),
			"0":("whO*uaV[rd[Co=_vj*dFdnf^^Dh5TJiNHGiH?bh)7keO0__k+vXS)FPl)7Gc+?@1/T9q4Z5e;#2KB=0HJW/9VU/@__0Sfb2:kL4Tnn6nrv:rv7@|wcG2i_JVi#F':<WA<QZN?']pB*_bFnbGL?c9S/c7Z9ajag]~evXvh}RE7BMq7]P;fI>zbJ:E^78>XP6IRR5NLd5LH46+D$79@I9&=+;U9i@$7YF@","5765874854984:93:4S:3SR:R;:Q;R3TS3UT2U3P;QP<;2VUO<P2WVN<O1W21XWN=<M=N1YXM@=0Y1@>=MA@?>@?!>0LY/L0K!?/ML/AMK#!.A/J#K.BAJ$#I$J-B.-CBI%$-DCH%I-EDH&%G&H,E-,FE,GF,&G,'&+',+('*(+*)("),
			"1":("tUhp05hp05b$KCb$KC7y2(?),v8rNQ/^Z{/^Z{b$tUb$","(*)(&*&+*('&%+&#%$#+%#,+#!,"),
			"2":("uJhp-shp-sb;PRN=WcIv[sFO_=BZ_R>?^L;X[C9<XR7]Tv6JOv5eHz5bB-6[<U8=5};/.;6D1C4m7Z2C>g0NH-/9SF/:^!0VfB3&it5'l76}o!:dop?rnpCslHGJg:L#ZwR7@.aruJar","7986975965:94:54;:/;4.;/.<;3/4-<.30/213103,<-,=<+=,*=+)=*)>=(>)(?>'?('@?&@'&A@%A&%BA$B%$CB$DC$!D#!$"),
			"3":("rlYapE^9l*bYfbe(_-g(RshzF+iZ8fiG/8hq/8b<8zb~EIc:O#bzVqas]Y_2bT[gd3Y>doUqbxR^^@PPXXO$RaN&KdMV<2MS<2GRLEGKReFXWFE5ZlC<^%@]^W=T]B:#Xv7cU&6PML5PBv5_9~6N2(7a2,18:O0(Ba/CKB/-U=/X[]0Rc/1phE4'l%6qn+:Jn)?RkLC<ftFJ[?Iid3JmkyMKq4P}sLU(","JLKILJIMLHMIHNMGFHFNHFENEONEDODPOCPDBPCAPBAQP@QA@RQ?R@?SR>S?>TS=T><T=;T<9;:9T;9UT9VU9WV98W7W86W76XW5X64X54YX3Y43!Y2!31!21#!0#10$#/$0.$/*,+-$.*-,*$-*%$*&%*'&)'*)('"),
			"4":("zcZchbZchbhpX=hpX=Zc%LZc%LT:RM/vhb/vhbT:zcT:X=6|3RT:X=T:","(-)-*)-+*(.-/+-'.('/.!,+/'&!+#/&#%#&#+/%$#"),
			"5":("rYW^p;[pkpaZe0du[=g9Q|hsEpi^7Wi:0Dhq0Db46Lbm@Lc5J)c3QDbMVya<[a^Qa=[)c.XPcdU{c,R{a<Pf]CNzWPMJN5L.27K}27/vm-/vm-6=?N6=?NEeNOEkYeF^d(H7kLJ|p!N<rFQz",":>;><;>=<:?>:@?:A@:BA:CB:9C9DC8D97D87ED6E75E64E54!E3!42!32#!1#21$#0$1/$0*,+.$/*-,.%$*.-*%.*&%*'&)'*)('"),
			"6":("vLX8t3]Tp{a_l<dUeDg/]^h]TaiQICiIAGhE:YfS5-ce0V^l-5Wo+wQ7,1K,-:E|/NA'2M=,7c8Y?M4kHR21Qv0c[Z/}nO/vnO6=[P6CS,7+Kf8MD=;+?=>L<lAO;7Di:PHFD1F4NuE,YCE(b^Epi$G9o(IgrLL3u+O6vaS]gsSofqQ<dyN~a]M,[MKlUXK#N[J|FeKi?!MA:FNb;+U8<gYT?g^9C1a=FhbVL|cNSdcSZ5bea__md{]Ug+Yxg~W(","8:97:86:75:64;5;:54<;4=<4>=3>43?>2?32@?2A@1A2DFECFDCGF1BABGCBHG0B10HB0RHRQHQIH0SRPIQOIP0TSOJI/T0NJO/UTMJNMKJLKM/VU.V/L!Kc!L.WVb!c-W.b#!-XWa#b_#a_$#-YX^$_-ZY,Z-^%$,[Z]%^,][,%]+%,+&%*&+*'&)'*)('"),
			"7":("tt6eFXhp6QhpfO6e+J6e+J/vtt/v","&('(&%%!($!%$#!"),
			"8":("t{]/rAaamndahNfb_ehPSHiSHJiN=@h<4Nem.lbR,!]b+^X3-aT81:Q(9_M(AMJd8(GQ3CE//CAb-h=(/58V434B;m1FC+/yJt/5V!/9_t0+gk1XmE3npq6Nr[96s.=Tq.AOmpDDhIG+^]J-f=L(m(Nuq;QKtETsuKX3da;ccb9WaY7v]I6]V-5KJ25BCW6D@-7R=k9(<Q;!<N=z>H@FA@B/GLDPPoFy[^CVb=@~dH>LeCVbb~TG^4RFVCOwN>MrDhPa?0S=;{Uq:gY7;d]A@,a2F/bdLQc=R?c<Whbs^]accD^~e=]?f:Yo","9;:9<;8<98=<8>=7>8P>7PO>O?>7QPN?O6Q76RQM?NM@?6SRL@M6TSK@LKA@5T65UT]AK4U54VU[A][BA4WVZB[ZCB4XW3X4YCZYDC3YX2Y32DY2ED1E21FE0F10cFcGFbGc0dc/d0bHGaHb/ed.e/aIH_Ia.fe-f.^I_^JI-gfqJ^q!J-hg,h-p!qo!p,iho#!+i,n#o+jim#nm$#+kjl$mk$l+$k*$+*%$)%*)&%(&)('&"),
			"9":("tzG:tDN&rnS/p4WSlW[Fg{_]_Fd0Qag7Akhf0Rhp0RbK@VbEKpaMV$^@^4Z%c-VUeMRGf/NLX{PkO~Q]ERQa>5Pv7lOO1*L^,WHg*IDU*'@b+9<4/U7A444K:A1wB!0-Il/6T@/=]e0Feh2DkC5Aol91sU?JJQ58D/62>W8=;@:n9J=U8lAu:-Ed=#HZAkJVF?KJLXKrU)KF_oIgfGH+eoB?d<=ka=9y[I7FVl5zPy55","ACBADC@DA@ED?E@?FE]F??I]>I?[F]>JIZF[ZGF>KJYGZ=K>=LKXGYXHG=ML<M=<NMWHX;N<W!HV!W;ON:O;:POU!V:QP9Q:T!UT#!9RQ9SRS#T9#S93#8392#32$#8437486476541$21%$0%10&%/&0/'&.'/.('-(.+-,+(-+)(+*)"),
			":":("P{;sT}<VXV=x[7@4]%BnZmE$XwFSUDH'P@HoJRH@F0FZCYDBC+AwD0?bGb==L3<*PgZdT3[1XV]f[7a!]%c[ZmeoXwgBVEhOS+iAO&iZJ0i&F%g@D,egC/czCKaNES^>H7[yLEZp","C32B3CB43A4BA54@5A@65?6@>6?>76=7>=87<8=<98<:9;:<1#!0#10$#/$0/%$.%/.&%-&.-'&,'-,(',)(+),+*)"),
			";":("P{;sT}<VXV=x[7@4]%BnZlE$XwFSUDH'P@HoJRH@F0FZCYDBC+AwD0?bGb==L3<*65qN>Zq*E0odHun+K?knK8hVHxfBDPc#Cu_gDJ]|F-[BHZZ0LxY>R(YNUDZ3XI[J[(^U]_b&^:e/]ahnZ0l{T^q8LOtPBtvQ67w;","=?>=@?=A@<A=;A<;BA:B;:CB9C:9DC8D98ED7E86E76FE5F65GF4G53G42G3JG2JHGJIH1#!0#10$#/$0/%$.%/.&%-&.-'&,'-,(',)(+),+*)"),
			"<":("n1dteCiP-'OyeC8Bn1=$@.Oq","$&%$'&$!'#!$"),
			"=":("t7Kb,gKb,gEPt7EPt7Z>,gZ>,gT.t7T.","')('&)#%$#!%"),
			">":("2s=$;Y8BsvOy;YiP2sdt_wP#","!$#'$!'%$&%'"),
			"?":("J,]LNO^.QY_PSabZSle5RCg&P?h;LCiJH(iVDKi#ATgq?efO>_d3?Fb*Ac_,Ev]jn6@ukhEJf/I!^>K#UjL*P-LFONVgCJVgBEF]NmFYT-F-XlDu[HC7]gAF^9>y]a;uZM8~W'6^Qr4SIm2o@i2':M2#:M+KDq+XRb-9[L/Pd@2=iG5Sl182n?<'","GIHGJIKELJGFFEKDLEDMLCMDCNMBNCBONAOB@OA@2O?2@?32>3?=3><3=;3<9;:97;73;7437547659871#!0#10$#0%$/%0.%/.&%-&.-'&,'-,('+(,+)(*)+FKJ"),
			"@":("b<XjbP]rd(_:fx_lj2_2lb]XouXHr8OOrDF2q-?,nS9KjG4}dX1s^00VVe0#O80WHH2GB65=<Z967j>'20FN.iQM.8Yl/Bc_2bj{81p/>Zs:FFtwQtu)]SsshPqghPw1]Py-Q0z9C!z$6mwc-gs+'wm-$9eF![VM$NKk'?Dh+:>H0g8E783F>s/KH1,JQ}+$^P+1hQ,ipY/sw>5.{L;[}YCh}NP2yQ[3s{bXnqdxhef,_(evY_d:WIb%W%_-QOdBKSf$COf$=qd3;*aw8g['90Rn;iKxA3EGI,ABPF@(WG@-^'A+iN?pXkFeV-EZP$EZK5H?H'LfEjSHEaZ+F^^>H8_KJ__hLm_BO^]tSIY2","PRQPSRPTSOTPO0TO10/T0.T/N1ON21.UT-U.N32M3N,U-M43,VUL4ML54+V,+WVo!plnmL65lonlrorqoq!oK6L*W+krlsrk}!qktsJ6K*XWjtk)X*jutJ76I7Jiujivu(X)(YXI87hvihwv|!}|#!'Y(hxwI98&Y'H9I|$#b$|hyxa$b{b|gyh&ZYa%$%Z&zb{gzygbzaZ%gcbfcg_Za_[Z^[_ecfedc^][H:9G:HG;:F;GF<;?A@F=<>A?E=FE>=EA>EBADBEDCB"),
			"A":("~1hpnNhpg.Zr92Zr1ghp!lhpEr/vYW/vc#T2O06m==T2","'+(+)(+!)',+*!+'%,%*,%$*$!*'&%#!$"),
			"B":("u}Xks%^]nRbrh&eU[hgkP'hj.hhp.h/vVt0+dc1llC4IqG9$r7>{peBCmpE<iMGPaHIcftJRmoLaqnN|t3Q1ukS|cC=jb_;Sa,9dZz7fR>6@=.65=.GFNMGCT:FvYzEf_;CbblA%fWTid5R'_qP7YdNlQbMf=.MZ=.bRSfbD](a%b8^Pe([HfXXe","(=)=*)=+*=,+=<,<-,(>=;-<:-;9-:9.-8.9C.8C/.B/CB0/A0BA10@1A?1@(I>I?>I1?I21I32I43IH4(JIH54G5HF5GF65E6FE76D7ED!7O!DN!ON#!M#NL#ML$#K$L(KJ($K(%$(&%('&"),
			"C":("tEflluh1ari@QuiJE:h*:je54Ga|/E]&+&UH)@M4*<E*-T>c2k958p5O?I2hG~0YR4/Aat/BkG07tB1otE97oS7}fB6FY)5pRT61LZ7'GC8WBL:l=F>k:5CU8TJ;9oRd<qWvAa[vI/a&Rrb[[|bne<bElSaGtD^i","243142154051085875765/90980/:9/;:.;/.<;.=<-=.->=,>-,?>,@?+@,+A@*A+*BA)B*)CB)DC(D)H!IG!H(ED'E(F!G'FE'!F&!'&#!&$#%$&"),
			"D":("y,I#xnN^wNS^s|YJnF_0hRc9bAeCY9g#Pkh1GNhk*lhp*l/vLz/~Z?1:gL4$mx7)s#:rwHACiyHjhFB?dd=.]O9CTQ77Jj6;926592bCHCb=QWaLY~^HbGZ9fvUxiIPG",",:-:.-:/.:0/:90910,;:8198217286276325365!34!5A!4A#!A$#@$A@%$?%@>%?>&%=&>='&<'=,<;,'<,(',)(,*),+*"),
			"E":("p:hp26hp26/vp:/vp:65@Y65@YG7nNG7nNMS@YMS@YbKp:bK","#'$'%$'&%#('#+(+)(+*)#,+#-,#!-"),
			"F":("p+6=A96=A9H,miH,miNDA9NDA9hp2Thp2T/vp+/v",")#*#+*#!+)$#)'$'%$'&%)('"),
			"G":("u;9>nk7fg~6Ya%5|Sz5~L<7&FH8W?U;f:9@A7BEB6EIp6TO58YUC;TY&>c[UCr_+I|akQbbpYjb}b0b[gRasgSNDO{NDO{H4uiH4uif;p@gKg(hmZaiTN9iFDwh9=/fO4Bby-E[e)TV7'NO{'eF}*=@j.p;34Y7)9o4M@O22G?0[Qw/<_e/6ia/qu01g","MONLOMLPOKPLK$P$#P#!P%$KJ%KI&J&%JI'&I('H(IH)(H*)G*HF*GF+*F,+8:987:7;:E,FE-,6;7E.-D.ED/.C/DC0/C10B1CB215;6B324;5B43B;4A;BA<;@<A@=<?=@?>="),
			"H":("v)hpgchpgcMZ9@MZ9@hp*zhp*z/v9@/v9@G/gcG/gc/vv)/v","')('*)+-,+!-'%*%+*%$+$!+'&%#!$"),
			"I":("H465/t65/t/vq(/vq(65Vh65VhbKq(bKq(hp/thp/tbKH4bK","#%$'%!-'!#!%-('+-,+(-+)(+*)&%'"),
			"J":("jq/vjiWvi@](fma<cEcz]-fIUdh5Mwi;DZiF<^hl4AgJ0bfB0c]q5$_;;BajCGbmJ6btPzb$V:^aXq[*Z-WzZ66D2'6D2'/v","8!987!7#!6#75#65$#4$5-/.4%$3%4-0/3&%-102&3-21-&2-'&,'-,('+(,+)(*)+"),
			"K":("xWhpfNhp<|Kv<|hp.Whp.W/v<|/v<|IHea/vvf/vK%J!","&('&)()+*),+&$)$,)$!,&%$#!$"),
			"L":("sVhp4mhp4m/vCI/vCIbKsVbK","#%$#&%#'&#!'"),
			"M":("{#hplzhpi~7_SITyIOTy:[?x5p7d3Qhp%yhp+,/v<0/vNxKBdE/vuw/v","*(+(,+(-,-$.$/.$!/'-(-%$&-'#!$*)(&%-"),
			"N":("uIhpbbhp9$:#9#hp+Xhp+X/v>+/vg~]Vh#/vuI/v","&$'$('$)(*!+)!*#)$&%$#!)"),
			"O":("zWJ+ysQMw*X0qa_6jad^a*gxSYiPJLiRADhc8bfK3Od..G_c*,YR(*U0&lOz&aHT($Bb*}=3/k845A4]:i2CAw0HL%/5TM/6[A/lcC0vhn2SoA5^u>:ry5Ask9FDi&@*eV;^_Z8MZ46wTZ5tKP5lE+6{?<9A:P=47ZAO5]Gr5lOX7!T68pWw<^]'Bqa?JEbvS}b{Ywam_c^}eSZ]i%V5kCO^","8:97:87;:7<;6<75<65=<5F=FE=4F54GFD=EC=D4HGC>=B>C3H43IHB?>A?B3JI2J3@?A2KJ1K2@!?W!@0K10LKW#!0ML/M0V#WV$#/NM.N/U$V.ONU%$-O.T%U-POS%TS&%R&S-QP,Q-,RQ,&R+&,+'&*'+*(')(*"),
			"P":("v.A5u)E0qYIljJN3cUPN[$QyPnS$=.S-=.hp.hhp.h/vQ3/{]a0vhP3)m{5FrU8OuK<hg(?dej<bbY9x[S7tUm6dO361=.6-=.LgN-LdU0L/[2JyaxI)e/FYfsCK","+9,9-,9.-9/.90/980810+:97186175165214253243!2@!3@#!?#@?$#>$?=$><$=<%$;%<+):);:)%;)&%)'&)('+*)"),
			"Q":("GbiH>Xh,7Sf)1dc--*^O(wWX&mPD&aHu(e@{-l:%3=5m8Q36>41=Dd/~L%/5TM/6[A/kcD0thn2Pmz4qs@8cwH=xy=B?zIGUz6OgxJU:ugYqq+_WlucAh4e[agg]YGhtT|iGWYm3[7oVaTpuh$qXoNq/tbp!xXnY~uslwcv;mlwpc$wqYyv|SkuJMCr?H~mZk9FHi&@.eV;e_Z8TZ36~TZ5|J|5wDc70?<9E:P=27ZAG5]G[5lOG7!T*8pWo<^]!Bna9JDboS}bsYwaf_c^yeSZZi%V6kCOc","021/20/32.3/.43-4.-54,5-X5,W5XW65V6W,YX+Y,U6V+ZYT6U+[ZT76*[+S7T*][S87R8S*^]R98)^*R:9k:R)_^(_)(a_k;:j;k'a('baj<;i<j'cb&c'i=<h=i&dcg=h%d&f=g%edf>=%fe%>f%?>$?%$@?#@$#A@!A#!BAQB!QCBQDCHJIPDQPEDGJHPFEFJGPJFOJPOKJNKONLKMLN"),
			"R":("xvhph_hpUZStR,Q*NUOVK0NiFkNF>+ND>+hp/ehp/e/vQR/|Zf0ibQ1rgd3HlJ5|nw8FpT;Mpu?HoyBLmSEYhtHfc~J]^/KwXRL]^@N*bvP-fzSQab=4_B:p[u8|X97VQG6B>+65>+HCLlH@R_GoWYFk[LE6^xCIad@r","+C,C-,C.-C/.C0/C10CB1+DCA1BA21@2A@32?3@>3?>43J4>J54I5JI65H6IG6HG76F7GE7F+)D)ED)7E)87)98):9);:)(;+*)';('<;&<'%<&%=<$=%$!=#!$"),
			"S":("t?ZUqo_RmscRh|edbLgTVYi#KXiX@giL3<h^*zge+$_W8/b>BYbxMob|U;bNZIa^___Dct]CeBYue@VvbTT*[.QoU$P.B#L*9AIf3hGM/6DS,U@w,:=A-2:V/f7E3X4k8J2d@c0VI0/RRS/,[F/Cfd0$mh0kmg7Nbl64T~5WJg5wDu6c?/8M;p;8;7=W;m?Z>iB.D?DBJ*Exa8JMj&M:o3OqrNRWt;UT","DFEDGFCGDCHGCIHBJCJICAKBKJBALK@LA@ML@NM?N@?ON>O?>PO>QP=Q>=RQ<R=<SR<TS;T<;UT:U;9U:9VU8V98WV7W87XW6X76YX5Y65!Y4!53!43#!2#31#2+-,1$#0$1+.-/$0+/.+$/+%$+&%*&+*'&)'*)('"),
			"T":("x#6=Vg6=VghpH4hpH46=(x6=(x/vx#/v","')()'&&#)%#&!)#%$#"),
			"U":("v.V)ttZ'rJ^hmHcnerf~]Sh[T8iQF0iC;}gm62e|2Cd(/=ai,X]H*vWF*k/v91/v97V5:0Y]<#]E>Z_=B%ajH<c%P[cBX|b^_|_gdL]DfgYEgkUygq/vv7/v","/10/21=?>=!?<!=/32<#!.3/;#<.43;$#:$;.54-5.-65:%$9%:-76,7-8%9,87,%8+%,+&%*&+*'&)'*)('"),
			"V":("~]/vXihpEChp!=/v2S/vOnaco</v","$&%$'&'!('#!$#'"),
			"W":("{?/vt5hpaThpNnMB>vhp,thp%Y/v33/v8MaEJDBJT?BJima?nM/v","')('*)-!.-#!*,+*%,%-,$-%*&%'&*$#-"),
			"X":("}$hpjphpO/P^5Chp#IhpFVJi&9/v7>/vOLDWil/vzB/vWzJI","')('*)*,+*-,'-*-$!&$'-'$&%$#!$"),
			"Y":("~u/vViS5VihpH6hpH6S&!!/v3C/vP3KunO/v","&('&)()!*)#!&#)%#&%$#"),
			"Z":("tr5l<{aruwaruwhp*yhp*yc8c16e,F6e,F/vtr/v",")+*)!+)(!(#!'#('$#'%$&%'"),
			"[":("gbz(=qz(=q)}gb)}gb/sK:/sK:t3gbt3","#'$'%$'&%#('#)(#!)"),
			"\\":("uhqsh@qs.v+K<>+K","#%$#!%"),
			"]":("c)z(98z(98t3SPt3SP/s98/s98)}c))}","')('&)&!)%!&#%$#!%"),
			"^":("uvJigqJiNO5d8QJi+hJiI?/vTl/v","$'&$!(&%$#!$'$("),
			"_":("~uz(!!z(!!t#~ut#","#%$#!%"),
			"`":("Wz5[Iu5[0$+KDE+K","#%$#!%"),
			"a":("e#hpdbc7]SewVLgqLRiLAkiN:_h]4Pfw0:dS-eaa,g]U-&X~.zUu2sRu9nP<A~NkKcN*cNN&c4H-^^D]XpB}T&B<LQB*C2B_:UCq3PE13R>R<M=0GJ<*SW;u]x<^e|>+jQ?tmnAzpJDyqTH5q[hpcNS[JBSfB^Tu>^VS<0Xl;^]U=fa.@[bLE!cCJJcNOVb}Vra=^F]{cN[,",">@?=@>=A@<A=;:<:9<9A<9BA98B8CB7C86C76DC5D64D54ED4FE3F42G3GF31G20G1/G0HG/TFG/IH.I/.JI-J.-KJ-LK,L-SFT#FS+L,R#S+ML+NMQ#R+ON*O+!F#P#Q*PO*#P*$#)$*)%$(%)(&%'&("),
			"b":("u|Tys;ZeniaHf}eZZ]hAOFiBE7i3;dhJ.{fK.u+K<{+K<SCJB/@+IY=PR8<(]0;|en=4ku?So~B?ssFqv%MIgDLFeAH!bdEA]~CGY(BNTvB9O}B_J$D2CaG$<}K(=#abEqc!MIcMU)bx[:aPbs]NfVWzgrRj","*,+*-,021/20/32.3/.43.<4-<.;4<-=<:4;->=*@-@?-?>-:5495:859758765*A@H67H!6G!HG#!F#GF$#E$FD$E*BA*CBC$DC%$*%C*&%)&*(&)('&"),
			"c":("owg>ehhqYPiHNti6D@gr:hdx57aS1f])/,VH.lP//tL91uHi6ADE;|A0B4>lL-<bW=<#c8<@jE=&ox>$omDsemB|^bBIW&B9PTBjJ~D%EmF)ASI&>pL@=PP,=dU%@0Z,E)^aKEawS8c$^)c+hab)ow_O","132143154051075765870/8098/.9/.:9.;:.<;-<.-=<->=,>-+>,+?>+@?*@+*A@)A*)BA(B)(CBF!G'C('DCE!F'ED'!E&!'&#!%#&%$#"),
			"d":("*jQ-,,KQ.sGB2%D=7DA&>#>XDZ=0K5<DSO<,Zn<IcL=0cN+KqZ+KqZhpe#hpdP_{]tdOX!fePMhpFYi_=@hn6-fN0~c4-A]r+/W593T%:'XL</]?@=aTEuc/K%c?PKbOX>^EcJWZcMCv]zC!U-B7LlB@G6C/BJDV>%G&;$JH9FNl",",.-,/.)+*(+)(,+(D,D/,ED('E(&F'FE'&GF%G&%HG%IHC/D%JI$J%$KJ#K$#LK!L#!;L:;!:<;:=<9=:B1C1/C9>=8>9A1B0/18?>A21@2A8@?82@728732743647546"),
			"e":("uJP|u+T*:-T*:EVg<-Z;?t^MEUakL$c%S-cO^)cBkYbEq'acq&gff>hyXuiSLwiPCahW;gfr56d.0=_S,NXe+AQC,KL(/KG+34Cc7R@{<n>kBM=2K0;}VR<%^^<yf$>JkX@joHC7s3G<u&KufnNLf^KPe2H@bIEc]NCaX<BOSTAoLxAjHOBBCZCe>RFc;GJL:(NK","=?>=@?=A@<A=;A<;BAMB;MLBLCB;NMKCL:N;:ONJCKICJ9O:IDC9POHDI9QP8Q9GDHGED8RQFEGF!E7R87FR7!F7#!$#77%$6%76&%6'&5'65(',.-5)(4)5+.,4*)*.+4.*3.42.32/.1/210/"),
			"f":("xt25is1(]@1JVC34SO5%Q+8OPpBkvEBkvEHsPpHsPphpBRhpBRHs(IHs(IBkBRBkB]9fC}5GG91MLB.MS=,D].+4jR*|xt+w","7986976!95!6#!54#5$#44%$3%43&%3'&2'32('1(2/101/.+(1.+1+)(-+.+*)-,+"),
			"g":("kGBZmmDYoqGpo~L2nTO@l,Q~ghThaPV~Y;X8ROXwGHXj=eW':OYu:C]Z=6_?A~a8^}asg2bPmDcdr?eLv-g}wxk#wxmyv@q@qvtkipww^QyeT=zIFxzF<ty]51x=.sv7*ks2)Poa*/lu,=j(4Veb1'dM-}b1,m^l-!Zv.aXG11V84xS_0#OK.WKg/&Gb0~DE5v@V>t=CI*<!Q=;wX6<PxC<]xCBY8Roh:7qc>GsBHqtUV6tOa1s5ehqSgto|i)mahLkSfEiz^PhGAEgd<qiS:!kS8jmI=,LU?5OABKQDG&RkKNSFPnSHVvRT]9P9aYLZaiHy_SFW[nD9WhBWS#AZM6ADGQAzBfCK?pE,=-H7","TVUSVTSWVSXWRXSyXRxXyRzywXxQzR!XwQ{zv!wv#!Q|{u#vu$#Q}|P}Qt$uO}Pt%$s%tOk}NkOs&%Nlkr&sNmlr'&MmNq'rMnmMonp'qp('MpoM(pL(ML)(-)LK-L-*)K.-,*-,+*J.KJ/.I/JI0/H0IH10H21H32H43G4HG54F5GF65g6Ff6gEgFEhge6fe76Eihd7eDiEc7dDjic87CjDCYjc98b9ca9bCZYBZC_9aB[Z_:9^:_B][A]B]:^A:]A;:@;A?;@?<;?=<>=?"),
			"h":("r+hpd&hpcnH}aqEa^ZD#YxB_U7B2O]BKJjCcE6F'<{Jp<{hp.uhp.u+K<{+K<]C0@_@qG!>6L?<lRx;z[b<$e-=0l1@!pODHr#I/",".0/.105764753743872832(8(982)('9(1)21*)&9'.,1,+1+*1%9&$9%$:9.-,$!:#!$"),
			"i":("SA+6WA,WY7-{Z?/HZP1=YY3+W,4{Sn6&PK6MKV63Gc4tED33D;0cE7.FGm,IJy+HN(*zJRBc2RBc2R<]Xh<]Xhbgrwbgrwhp/rhp/rbgJRbg","465436376<73:<;:7<:87:981!20!10#!0$#/$0/%$.%/.&%-&.-'&-(',(-+(,+)(+*)"),
			"j":("^0*wc%+7fv,DiF.6jE/wj;1li$3Zem5Nb!6@]C6MX>5vT84-RL1uRB/fT)-LVx+{Ya+8gp<]g^k)dvpn^[u/XDwMS&x{Lpy{E+zO;.z=22yE,TxB,TqD0crC7VsP?qt6G_t0NTs!T$p5VSm3WTi}WZBc/rBc/r<]","H3IHG3G43F4GE4FE54D5EC5D=?>=@?C65B6C=A@A6B=6A=76=87<8=<98;9<;:92#!1#21$#0$10%$/%0/&%.&/.'&.('-(.-)(,)-,*)+*,"),
			"k":("yrhpfThp>]P(>fhp0ahp0a+K>f+Ke2<]wi<]OcP+","&('&$($*)$+*$!+&%$#!$"),
			"l":("JR1L2R1L2R+KXh+KXhbgrwbgrwhp/rhp/rbgJRbg","#%$#!%!&%+&!)+*)&+)'&)('"),
			"m":("jhhpjbFFifC@gbB-d0B&_qCCZzFMUpKfUphpH~hpHnEZGSB}EeB*C1A~A/BC>}CJ<#Ea61Kb61hp)7hp)7<]3}<]4^DU:(?H>H=/BI<-H%;rND<xRI?fT'DiXC@O[j>1b;<Mfy;ul)<(p&<vtM?9wLDbwahp","BDC;=<BED:=;576587AEBAFE9=:9>=@FA@%F%GF&%@9?>90//.9.?9?&@809-?.$G%?'&810,?-821538328?('#G$,(?#HG!H#+),)(,543+*)"),
			"n":(".u<];H<];}CJAL@EG<>*Kn<qRR;{[p<$eG=0k3?EnOAqpkDzr$I/r+hpd%hpcmHyaWEC]tC^XGBGQXB7MpBiIqCtDCFE<|Jk<zhp.uhp","(*)'*(;#!;$#&*'&+*%+&%,+%5,54,$5%$654-,3-4$76;9$98$87$2-31-21.-;:91/.0/1"),
			"o":("w-UGtdZmq<_RmZc6gbf(_xh#Vji>KgiXDFi'=lg|5feE.~a*++Y{)UU#)WNd+XIc.BF+3aA|:l>tA2=5GT<:Pq;oYu<Bc,=Pk3@)p7C*ssFKvUK<wRP)hbMcfiIbcRFO]1ClV9BRP3B'ISBGDmC>?(EV:jI)8cL_7eQ#8EV@:NZ<>*^RD'b.KFc>S/cAY'bM^)a3cC]~fjYWhGV?i1RM","6875865984954:93:43D:D;:3EDC;D3FEB;CB<;3GF2G3A<B2HG1H2@<A@=<1IH0I1?=@?>=0JIV>?/J0V!>/KJU!V.K/U#!T#U.LKS#T.ML-M.S$#R$S-NMR%$Q%RP%Q-ON,O-,PO,%P,&%+&,+'&+('*(+)(*"),
			"p":("v9QhuDVgsNZJo|_LiWdOaog4Y0hNR(i6Gui==!hN<zz(.uz(.u<];H<]<=CbAV@HG|=yMw<]T.;|]e;~en=6kv?QpRBnspFwunLCgnOhg.KmeMH3b,Du[IBxV!B6QMBNN'C%HjD^BZGX<{K,<~aaDMbsJVcER1c:YzaxbP]he{X{gXT[","354365-/.-0/2632761721871@80@10A@?8@0BA0CB>8?-E0ED0DC0>98=9>=:9<:=-FE;:<;!:M!;M#!L#ML$#K$LK%$J%KJ&%-+F+GFI&J+HGH&I+&H+'&+('-,++)(*)+"),
			"q":("*gQc+}K}.ZGc1tDG8O@JBN=IN&</X7<;e/=KqZ;tqZz(cMz(cya?^.dHTKgvL)iFCQiT<>hX7Xg+3Ye0/Aa^,O[:++Vj9-Q79PVG;G[7>P_EAFaxDob{IgcCOPbfVo_*]XZscMWRcMCw^oC-UyB2L[B9EICJ?sEm<9Hn9~Lb","*,+')('*)'E*ED*D,*&F'FE'&GF%G&%HGC,D%IH$I%$JI#J$#KJ#9K!9#!:98:!7:87;:B.C.,CA.B7<;6<7A/.@/A6=<6>=?/@6?>5?65/?50/405304310213-,."),
			"r":("24<]?&<]?KDDENA$K@>XR{<WZ!;ubs<&hs<ymw>PrFA4uCDkvnI>vsLghpLdgrGSf@E?d#Cf_]BXXBB0RDC%MPDYFeGp@HKf@Hhp24hp","')('*);#!;$#'+*&+'&,+%,&5,%4,5$5%4-,$653-4$762-3;9$98$87$1-21.-0.10/.;:9"),
			"s":("q,]<ohaElGd)i%eecqgDZ}hbR]iPG6iT;ii+0ah$0daA>AbqGVcBRlc?Z-bH_<a&b5^CbY[MayY}_NXl[WW[U,V(GnSu>0Qs7:O43sLl1|J&1lFo3+D34zB=8+@?<}>JCc<wKz<$WA;wc+<Akl=*klCZb>BUSiAzJVB=EXC0BnD)A)E7@1F^@CHoC'JwKOM7YDOOdeQFlDT4oVVjptY6","CEDBECBFEBGFAGBHGA@HAIH@?I@?JI?KJ>K?>LK>ML=M>=NM=ON<O=<PO;P<;QP:Q;:RQ:SR9S:9TS8T97T87UT6U76VU5V64V53V43!V2!32#!1#20#1+-,/#0/$#+.-+/.+$/+%$+&%+'&*'+*(')(*"),
			"t":("r9h9kshz^*iMQOhyHLg5BHd5?=_u=rZu=iBk'&Bk'&<]=i<]=i1&Kn/0Kn<]r9<]r9BkKnBkL%ZTN-^RQ2aDUTbX^#c?k!bkr9az",".0/-0.+-,30-+*-*3-203)3*102)43)54(5)(65(769!:'7('878!9'!8&!'%!&%#!%$#"),
			"u":("r+hpeOhpe!b%^Ye#WJgMRsh_LmiOC(iK<>hO6vfc2rd(04_V.|ZE.t<]<z<]=/ZA?s_[EQb|LTc?QPbdWo_TcyXmd%<]r+<]",".0/.107987!9-1.-216$7$!7-325$6,3-#!$5%$4%5,43,%4+%,+&%*&+*'&)'*)('"),
			"v":("'<<]7<<]OLa(iZ<]y&<]W5hpG&hp","(#!($#$&%$'&('$"),
			"w":("|%<]p7hp^3hpO*Q.A7hp0_hp$z<]2b<]:yaaJ4G/T=G/fZaAn.<]","')('*)-!.-#!*,+*%,%-,$-%*&%$#-'&*"),
			"x":("z#hpgAhpOKVg9lhp'ZhpG&Q^)(<];*<]PHLrgA<]xe<]X9Qo","')('*)*,+*-,'-*&-'&$-$!-&%$#!$"),
			"y":("y&<]XoghS/mnN1qrG^u_@Fx7:#yT1Dz?&hz2&nsU0'sr59sK9lrJ>zp:CHm*Gehw'<<]7<<]P(_yiY<]","1321434!54#!1#41$#0$1/$0/%$.%/-%.-&%,&-*,+*&,*'&*('*)("),
			"z":("rWhp/5hp/5cW^$Bk0ABk0A<]ow<]owBB@vb_rWb_","&('&)(&%)%*)$*%$+*$!+#!$"),
			"{":("lJz(b*z$W_y<OqwLJEtUGTqREpmPEUXRDRV/BvTR@=S9<IR76?QZ/&QV/&Kf6(Kc;zK;@fJ:C^H^EKEwEl6wGd2)K^.WP@,MU0+6[:*@lE)rlJ/sbJ0!Y11NUT3QS36bRcE}OIJhJIM0C6N_HXOHN'QPPaSSRqW5SAm8V9p}Z;rpbNt&lJt3",";=<:=;9=:8=9>=87>87?>7@?7A@6A75A65BA4B54CB3C42C31C2/10/C1/DC/ED/FE/GF/.G-G.-HG,H-+H,+IH*I+)I*)JI(J)(KJ'K('LK&L'&ML&NM&!N%!&$!%#!$"),
			"|":("V)z(Hoz(Ho!!V)!!","#%$#!%"),
			"}":("4K)}>m*%G7*iN8,BSL.iWE2JY-70Y>DXZdGe^VI]cTJuj4KaqyKfqyQVjvQYd|R$_ER}[7T[YGWYY2l<XAocV1s0RzuZOEw>Inxq@vy{4Kz(4Kt3>Pt'EhrUIBpRKdmCL5W?NCSeRLPn[bNbV=MvPpKkN6IhL&F)KT6mI63WE^1P>L0!4K/s","N#!N$#N%$N&%NM&M'&L'MK'LJ'KJ('J)(I)JI*)H*IH+*H,+G,HG-,G.-G/.F/GE/FD/E0/DD10C1DC21C32B3CB43B54A5BA65@6A?6@?76>7?<>=<7><87<98<:9<;:"),
			"~":("yfIWy4McwjPYu+SWp;V5kFW]edXA]nX9V$V{OHTNDQO,@&Mx;KMo7mNs5}P94WRa44U}';U}'BSZ(NP#*rLz-mJc1VH}6yGX>8G,E'G^LYImR0LHWzOA]^Q2b3QffvQQjVOxl-MXltIY","9;:8;98<;7<8D#!7=<6=7C#D6.=-=.5.6->=,>-B#C5/.50/B$#,?>A$B+?,510A%$+@?@%A+%@415421324+&%*&+*'&)'*)('")
		}
		base91str="!#$%&'()*+,-./0123456789:;<=>?@ABCDEFGHIJKLMNOPQRSTUVWXYZ[]^_abcdefghijklmnopqrstuvwxyz{|}~"
		base91inv={base91str[i]:i for i in range(len(base91str))}
		if transform is None: transform=Transform([0]*3)
		def addedge(a,b):
			pt=(a,b) if a<b else (b,a)
			edge=edgecount.get(pt,[a,b,0])
			edge[2]+=1
			edgecount[pt]=edge
		x0,y0=0.0,0.0
		for char in text:
			data=font.get(char,None)
			if data is None:
				if char=="\n": x0,y0=0.0,y0+1.0
				elif char=="\t": x0+=width*4
				elif char==" ": x0+=width
				continue
			vertstr,facestr=data
			toparr,botarr=[],[]
			# Convert the font data to vertices.
			for i in range(0,len(vertstr),4):
				x=(base91inv[vertstr[i+0]]*91+base91inv[vertstr[i+1]])*(width/8281.0)+x0
				y=(base91inv[vertstr[i+2]]*91+base91inv[vertstr[i+3]])*(  1.0/8281.0)+y0
				toparr+=[self.addvertex([x,0.0,y],transform)]
				botarr+=[self.addvertex([x,-thickness,y],transform)]
			# Convert the font data to top and bottom faces.
			edgecount={}
			for i in range(0,len(facestr),3):
				v0=base91inv[facestr[i+0]]
				v1=base91inv[facestr[i+1]]
				v2=base91inv[facestr[i+2]]
				self.addface([toparr[v0],toparr[v1],toparr[v2]],mat)
				self.addface([botarr[v1],botarr[v0],botarr[v2]],mat)
				addedge(v0,v1)
				addedge(v2,v0)
				addedge(v1,v2)
			# Fill in the edges between the top and bottom faces.
			for edge in edgecount.values():
				a,b,count=edge
				if count==1:
					self.addface([toparr[b],toparr[a],botarr[a]],mat)
					self.addface([botarr[a],botarr[b],toparr[b]],mat)
			x0+=width


	def textdim(self,text,thickness):
		# Returns the physical dimensions for a block of text.
		width=0.520093
		maxx,x0,y0=0.0,0.0,1.0
		for char in text:
			if char=="\n": x0,y0=0.0,y0+1.0
			elif char=="\t": x0+=width*4
			else: x0+=width
			if maxx<x0: maxx=x0
		return Vector([maxx,thickness,y0],False)


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
				colsum=0.0
				for i in range(3):
					col[i]*=matcol[i]
					ret[i]+=matlum*col[i]
					colsum+=abs(col[i])
				if colsum<1e-5: break
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

