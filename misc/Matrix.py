"""
Matrix.py - v1.08

Copyright 2020 Alec Dee - MIT license - SPDX: MIT
alecdee.github.io - akdee144@gmail.com

--------------------------------------------------------------------------------
Standards

Make no assumptions about the element types. Using aggregate functions like
sum() assumes int, float, etc.

Avoid performing a shallow copy and then performing an __i__ operation on each
element (ex: +=, -=, ...). If the elements are mutable types, then only their
references will be copied and the subsequent __i__ operations will modify both
the current and original elements.

--------------------------------------------------------------------------------
Properties

Matrix dimensions are given by (rows,cols). Coordinates are (r,c).
Let A=(Ar,Ac) and B=(Br,Bc), then AB=(Bc,Ac).
A*(B*(C*x))=(C*(B*A))*x
det(AB)=det(A)*det(B)
det(cA)=c^n*det(A)
det(A)!=0 iff rank(A)=n.
det()=1
Adding a multiple of one row to another will not change the determinant.
Swapping two rows will multiply the determinant by -1.
Multiplying a row by a constant c will multiply the determinant by c.
A matrix is orthogonal if A^-1=A^t.

--------------------------------------------------------------------------------
TODO

Increase inverse matrix stability.
Increase determinant algorithm stability. Ex: raytracer normal errors.
Division free determinant, Richard Bird or Samuelson-Berkowitz.
See: http://www.pkoprowski.eu/lcm/lcm.pdf
Add generalized inverse. Get rid of reduced().
Add example if name=main for solving polynomial.
"""

import math,random
from copy import deepcopy

class VecInterface(object):
	"""A helper class to allow rows and columns to be treated as vectors."""
	# Keep class definition here for compatibility with pickle.

	def __init__(self,elem,step,start,count,l):
		self.arr=[Vector(elem,False,i*step,start,count) for i in range(l)]

	def __getitem__(self,i):
		return self.arr[i]

	def __setitem__(self,i,v):
		u=self.arr[i]
		u.checkdims(v)
		for i in range(len(u)):
			u[i]=v[i]

	def __len__(self):
		return len(self.arr)

	def __iter__(self):
		return iter(self.arr)

class Matrix(object):
	"""
	Generic matrix class.
	Makes no assumptions about element types.
	"""

	#---------------------------------------------------------------------------------
	# Management
	#---------------------------------------------------------------------------------

	def __init__(self,rows=None,cols=None,copy=True):
		if hasattr(rows,"__getitem__"):
			mat=rows
			if isinstance(mat,Matrix):
				rows,cols=mat.rows,mat.cols
			elif cols:
				rows,cols=cols
			else:
				rows=len(mat)
				cols=len(mat[0]) if mat else 0
			elem=mat
			if copy:
				elem,i=[0]*(rows*cols),0
				dcopy=Matrix.dcopy
				assert(len(mat)==rows)
				for r in mat:
					assert(len(r)==cols)
					for e in r:
						elem[i]=dcopy(e)
						i+=1
		elif rows is not None:
			if cols is None: cols=0
			zero=Matrix.getzero
			elem=[zero() for i in range(rows*cols)]
		else:
			rows,cols,elem=0,0,[]
		self.elem,self.elems=elem,rows*cols
		self.rows,self.cols=rows,cols
		# Allow rows and columns to function as vectors.
		self.row=VecInterface(elem,cols,1,cols,rows)
		self.col=VecInterface(elem,1,cols,rows,cols)

	def __getitem__(self,r):
		return self.row[r]

	def __setitem__(self,r,v):
		self.row[r]=v

	def __len__(self):
		return self.rows

	def __iter__(self):
		return iter(self.row)

	def __repr__(self):
		def rp(r): return "["+",".join([repr(e) for e in r])+"]"
		return "Matrix(["+",".join([rp(r) for r in self])+"])"

	def __str__(self):
		"""String representation. Each row and column are padded individually."""
		rows,cols=self.rows,self.cols
		rpad,cpad=[1]*rows,[0]*cols
		cell=[[0]*cols for r in range(rows)]
		for r in range(rows):
			for c in range(cols):
				# Convert the element value into a string and split it by eol's.
				s=self[r][c]
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

	#---------------------------------------------------------------------------------
	# Helper Functions
	#---------------------------------------------------------------------------------

	_zero=0
	_one=1

	@staticmethod
	def dcopy(e):
		if not type(e) in (int,bool,float,str):
			return deepcopy(e)
		return e

	@staticmethod
	def getinverse(x):
		if type(x) in (int,bool,float):
			y=abs(x)
			if y<1e-20 or y>1e20:
				return None
			return 1.0/x
		try:
			return x**-1
		except (ArithmeticError,ZeroDivisionError,TypeError):
			return None

	@staticmethod
	def setunit(unit):
		Matrix._zero=unit-unit
		Matrix._one=Matrix._zero+unit

	@staticmethod
	def getzero():
		return Matrix._zero+Matrix._zero

	@staticmethod
	def getone():
		return Matrix._zero+Matrix._one

	def checkdims(a,r,c):
		if a.rows!=r or a.cols!=c:
			raise AttributeError("Bad dimensions: ("+str(a.rows)+","+str(a.cols)+")!=("+str(r)+","+str(c)+")")

	def replace(a,b):
		assert(isinstance(b,Matrix))
		a.elem,a.elems=b.elem,b.elems
		a.rows,a.cols=b.rows,b.cols
		a.row.arr=b.row.arr
		a.col.arr=b.col.arr
		return a

	#---------------------------------------------------------------------------------
	# Basic
	#---------------------------------------------------------------------------------

	def __eq__(a,b):
		rows,cols=a.rows,a.cols
		if isinstance(b,Matrix):
			if b.rows!=rows or b.cols!=cols:
				return False
			ae,be=a.elem,b.elem
			for i in range(a.elems):
				if ae[i]!=be[i]:
					return False
			return True
		elif b==0 or b==1:
			# For identity and 0-matrix comparisons.
			unit=[Matrix._zero,Matrix._one]
			unit[1]=unit[b]
			for r in range(rows):
				arow=a.row[r]
				for c in range(cols):
					if arow[c]!=unit[r==c]:
						return False
			return True
		return False

	def __ne__(a,b):
		return not a==b

	def dist(a,b):
		"""Frobenius norm."""
		a.checkdims(b.rows,b.cols)
		dist=Matrix.getzero()
		ae,be=a.elem,b.elem
		for i in range(a.elems):
			dif=ae[i]-be[i]
			dist+=dif*dif
		return dist**0.5

	def one(a):
		"""Make A the identity matrix."""
		a.zero()
		elem,one=a.elem,Matrix.getone
		n,cols=min(a.rows,a.cols),a.cols
		for i in range(n):
			elem[i*cols+i]=one()
		return a

	def zero(a):
		"""Zeroize matrix A."""
		elem,zero=a.elem,Matrix.getzero
		for i in range(a.elems):
			elem[i]=zero()
		return a

	#---------------------------------------------------------------------------------
	# Algebra
	#---------------------------------------------------------------------------------

	def __add__(a,b):
		# Return A+B as a separate matrix.
		a.checkdims(b.rows,b.cols)
		ae,be=a.elem,b.elem
		return Matrix([ae[i]+be[i] for i in range(a.elems)],(a.rows,a.cols),False)

	def __iadd__(a,b):
		# Calculate A+=B.
		a.checkdims(b.rows,b.cols)
		ae,be=a.elem,b.elem
		for i in range(a.elems): ae[i]+=be[i]
		return a

	def __sub__(a,b):
		# Return A-B as a separate matrix.
		a.checkdims(b.rows,b.cols)
		ae,be=a.elem,b.elem
		return Matrix([ae[i]-be[i] for i in range(a.elems)],(a.rows,a.cols),False)

	def __isub__(a,b):
		# Calculate A-=B.
		a.checkdims(b.rows,b.cols)
		ae,be=a.elem,b.elem
		for i in range(a.elems): ae[i]-=be[i]
		return a

	def __neg__(a):
		return Matrix([-e for e in a.elem],(a.rows,a.cols),False)

	def __mul__(a,b):
		if isinstance(b,Vector):
			# Vector A*v.
			return Vector([u*b for u in a.row],False)
		elif not isinstance(b,Matrix):
			# If b is not a matrix, perform a scalar multiplication.
			return Matrix([e*b for e in a.elem],(a.rows,a.cols),False)
		# a*b yields (rows(a),cols(b)). Need cols(a)=rows(b).
		if a.cols!=b.rows:
			raise AttributeError("A*B needs cols(A)=rows(B): "+str(a.cols)+","+str(b.rows))
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

	def __rmul__(a,b):
		# We will only get here if b is not a matrix.
		return Matrix([b*e for e in a.elem],(a.rows,a.cols),False)

	def __truediv__(a,b):
		if not isinstance(b,Matrix):
			return Matrix([e/b for e in a.elem],(a.rows,a.cols),False)
		return a*b.inv()

	def __itruediv__(a,b):
		return a.replace(a/b)

	def __rtruediv__(a,b):
		# We will only get here if b is not a matrix.
		return b*a.inv()

	# python2 mappings for a/b.
	__div__=__truediv__
	__idiv__=__itruediv__
	__rdiv__=__rtruediv__

	def __floordiv__(a,b):
		if not isinstance(b,Matrix):
			return Matrix([e//b for e in a.elem],(a.rows,a.cols),False)
		return a*b.inv()

	def __ifloordiv__(a,b):
		return a.replace(a//b)

	__rfloordiv__=__rtruediv__

	#---------------------------------------------------------------------------------
	# Exponentiation
	#---------------------------------------------------------------------------------

	def inv(a):
		"""Returns the multiplicative inverse of A."""
		rows,cols=a.rows,a.cols
		if rows!=cols:
			raise AttributeError("Can only invert square matrices: ("+str(rows)+","+str(cols)+")")
		ret=Matrix(a)
		getinverse=Matrix.getinverse
		elem=ret.elem
		perm=list(range(cols))
		for i in range(rows):
			# Find a row with an invertible element in column i.
			dval=i*cols
			sval=dval
			inv=None
			for j in range(i,rows):
				inv=getinverse(elem[sval+i])
				if inv is not None: break
				sval+=cols
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

	def __pow__(a,exp):
		# exp=-1,0,+1 should evaluate in one operation.
		# Need A=(V^-1)*P*V decomposition or ln(A) for non integer exp.
		iexp=int(exp)
		if abs(iexp-exp)>=1e-20:
			raise NotImplementedError("Exponent must be an integer: "+str(exp))
		rows,cols=a.rows,a.cols
		if rows!=cols:
			raise AttributeError("Can only raise square matrices to powers: ("+str(rows)+","+str(cols)+")")
		# A^0 always returns the identity - even if A^-1 doesn't exist.
		if rows==0 or iexp==0:
			return Matrix(rows,rows).one()
		if iexp<0:
			# A^-n=(A^-1)^n.
			iexp=-iexp
			val=a.inv()
		else:
			val=Matrix(a)
		iexp-=1
		pot=val
		while True:
			if iexp&1: val=val*pot
			if iexp<2: break
			pot=pot*pot
			iexp>>=1
		return val

	#---------------------------------------------------------------------------------
	# Misc
	#---------------------------------------------------------------------------------

	def T(a):
		"""Transposition of A."""
		elem,r,c,dcopy=a.elem,a.rows,a.cols,Matrix.dcopy
		return Matrix([dcopy(elem[(i%r)*c+i//r]) for i in range(a.elems)],(c,r),False)

	def __abs__(a):
		"""Returns the determinant of A."""
		cols=a.cols
		if a.rows!=cols:
			# It may be acceptable to return sqrt(abs(A^t*A)) here. This would coincide with
			# finding the magnitude of a column vector.
			raise AttributeError("Determinant is only defined for square matrices: ("+str(a.rows)+","+str(cols)+")")
		if cols==0:
			# The empty matrix has a determinant of 1.
			return Matrix.getone()
		# Copy the matrix. Use the upper triangular form to compute the determinant.
		m=Matrix(a)
		elem,elems=m.elem,m.elems
		getinverse=Matrix.getinverse
		sign,dval=0,0
		for i in range(cols-1):
			dval=i*cols
			sval=dval
			inv=None
			while sval<elems:
				inv=getinverse(elem[sval+i])
				if inv is not None: break
				sval+=cols
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

	def reduced(a):
		"""Returns the matrix in reduced row echelon form."""
		rows,cols=a.rows,a.cols
		ret=Matrix(a)
		elem=ret.elem
		for i in range(min(rows,cols)):
			# Find a row with an invertible element in column i.
			dval=i*cols
			sval=dval
			inv=None
			for j in range(i,rows):
				inv=getinverse(elem[sval+i])
				if inv is not None: break
				sval+=cols
			if inv is None:
				raise ZeroDivisionError("Unable to find an invertible element.")
			# Swap the desired row with row i.
			if sval!=dval:
				for c in range(i,cols):
					elem[sval+c],elem[dval+c]=elem[dval+c],elem[sval+c]
			# Put the row into reduced echelon form.
			for c in range(i,cols):
				elem[dval+c]*=inv
			# Perform row operations with row i to clear column i for all other rows in A.
			for r in range(rows):
				if r==i: continue
				sval=r*cols
				mul=elem[sval+i]
				for c in range(i,cols):
					elem[sval+c]-=elem[dval+c]*mul
		return ret

	#---------------------------------------------------------------------------------
	# Geometry
	#---------------------------------------------------------------------------------

	def ortho(a):
		"""Returns the orthonormal basis of the matrix. Non orthogonal rows are
		sorted to the bottom."""
		# Returns the orthonormal basis of the matrix. Zero-rows are sorted to the bottom.
		# Orthonormal matrices have the following properties:
		#
		#      det(A)=+-1
		#      A^-1=A^t
		#      A row vector, u, is normal if u*u=1.
		#      Two row vectors, u and v, are orthographic if u*v=0.
		#      All row vectors are orthonormal iff all columns are orthonormal.
		#
		# We use the Gram-Schmidt process to orthogonalize the matrix.
		rows,cols=a.rows,a.cols
		ret=Matrix(a)
		if rows==0 or cols==0:
			return ret
		elem,rank=ret.elem,0
		zero=Matrix.getzero
		for i in range(rows):
			dval,sval=0,i*cols
			for r in range(rank):
				# Get the projection of u onto the previous vectors.
				# ui-(ui*uj)*uj/(uj*uj)
				norm=zero()
				for c in range(cols):
					norm+=elem[sval+c]*elem[dval+c]
				for c in range(cols):
					elem[sval+c]-=elem[dval+c]*norm
				dval+=cols
			# Normalize u. If it is a non-zero vector, move it up.
			norm=zero()
			for c in range(cols):
				norm+=elem[sval+c]*elem[sval+c]
			try:
				norm=norm**-0.5
				for c in range(cols):
					elem[dval+c]=elem[sval+c]*norm
				rank+=1
			except (ArithmeticError,ZeroDivisionError):
				dval-=cols
			if sval!=dval:
				for c in range(cols):
					elem[sval+c]=zero()
		return ret

	def rotate(a,angs):
		# Perform a counter-clockwise, right-hand rotation given n*(n-1)/2 angles. In 3D,
		# angles are expected in ZYX order.
		#
		# Rotation is about a plane, not along an axis. For a 2D space, we may only rotate
		# about the XY plane, thus there is 1 axis of rotation. Given an angle, a, we have
		# the rotation matrix:
		#
		#      M = [ cos(a) -sin(a) ]
		#          [ sin(a)  cos(a) ]
		#
		# For a 3D space, we have rotations about the XY, XZ, and YZ planes. Given angles
		# a, b, and c, we have the rotation matrix:
		#
		#                   XY                       XZ                       YZ
		#          [ cos(a) -sin(a)  0 ]   [  cos(b)  0  sin(b) ]   [ 1    0       0    ]
		#      M = [ sin(a)  cos(a)  0 ] * [    0     1    0    ] * [ 0  cos(c) -sin(c) ]
		#          [   0       0     1 ]   [ -sin(b)  0  cos(b) ]   [ 0  sin(c)  cos(c) ]
		#
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
	"""
	n-dimensional vector class.
	Makes no assumptions about element types.
	"""

	#---------------------------------------------------------------------------------
	# Management
	#---------------------------------------------------------------------------------

	def __init__(self,x=None,copy=True,start=0,step=1,elems=None):
		"""
		Initialize the vector. If only x is given, it will be checked if it is a
		vector or can be indexed, and a copy will be made.
		"""
		if hasattr(x,"__getitem__"):
			elem=x
			if copy:
				if elems is None: elems=len(x)
				dcopy=Matrix.dcopy
				elem=[dcopy(x[start+i*step]) for i in range(elems)]
				start,step=0,1
		elif isinstance(x,int):
			zero=Matrix.getzero
			elem=[zero() for i in range(x)]
		else:
			elem=[]
		if elems is None: elems=len(elem)
		self.elem=elem
		self.start=start
		self.step=step
		self.elems=elems

	def __str__(self):
		return str(Matrix(self,(1,len(self)),False))

	def __repr__(self):
		return "Vector(["+",".join([repr(x) for x in self])+"])"

	def __len__(self):
		return self.elems

	def __getitem__(self,i):
		assert(i>=0 and i<self.elems)
		return self.elem[self.start+i*self.step]

	def __setitem__(self,i,v):
		assert(i>=0 and i<self.elems)
		self.elem[self.start+i*self.step]=v

	def __iter__(self):
		elem=self.elem
		pos,step=self.start,self.step
		for i in range(self.elems):
			yield elem[pos]
			pos+=step

	def checkdims(u,v):
		ul,vl=len(u),len(v)
		if ul!=vl:
			raise AttributeError("Vector lengths different: "+str(ul)+"!="+str(vl))

	#---------------------------------------------------------------------------------
	# Basic
	#---------------------------------------------------------------------------------

	def __eq__(u,v):
		if not isinstance(v,Vector):
			return False
		n=len(u)
		if len(v)!=n:
			return False
		for i in range(n):
			if u[i]!=v[i]:
				return False
		return True

	def __ne__(a,b):
		return not a==b

	def dist(u,v):
		return abs(u-v)

	def randomize(u):
		"""Turn u into a random unit vector."""
		n=len(u)
		if n==0: return u
		mag=0.0
		while mag<=1e-20:
			mag=0.0
			for i in range(n):
				r=random.gauss(0.0,1.0)
				u[i]=r
				mag+=r*r
		mag=1.0/math.sqrt(mag)
		for i in range(n): u[i]*=mag
		return u

	def zero(u):
		zero=Matrix.getzero
		for i in range(len(u)):
			u[i]=zero()
		return u

	#---------------------------------------------------------------------------------
	# Algebra
	#---------------------------------------------------------------------------------

	def __add__(u,v):
		u.checkdims(v)
		return Vector([u[i]+v[i] for i in range(len(u))],False)

	def __iadd__(u,v):
		u.checkdims(v)
		for i in range(len(u)): u[i]+=v[i]
		return u

	def __sub__(u,v):
		u.checkdims(v)
		return Vector([u[i]-v[i] for i in range(len(u))],False)

	def __isub__(u,v):
		u.checkdims(v)
		for i in range(len(u)): u[i]-=v[i]
		return u

	def __neg__(u):
		return Vector([-x for x in u],False)

	def __mul__(u,v):
		"""Returns the scalar dot product if v is a vector: u.x*v.x+u.y*v.y+...
		Returns the elementwise scalar product otherwise: (u.x*v,u.y*v,...)"""
		if isinstance(v,Vector):
			# Vector dot product u*v=u.x*v.x+u.y*v.y+...
			u.checkdims(v)
			s=Matrix.getzero()
			for i in range(len(u)):
				x=u[i]*v[i]
				s=s+x if i else x
			return s
		# Elementwise scalar product u*s.
		return Vector([x*v for x in u],False)

	def __rmul__(u,v):
		# Make sure to use the scalar on the left side (s*u instead of u*s).
		return Vector([v*x for x in u],False)

	def __imul__(u,v):
		for i in range(len(u)): u[i]*=v
		return u

	def __truediv__(u,v):
		return Vector([x/v for x in u],False)

	def __itruediv__(u,v):
		for i in range(len(u)): u[i]/=v
		return u

	# python2 mappings for a/b.
	__div__=__truediv__
	__idiv__=__itruediv__

	def __floordiv__(u,v):
		return Vector([x//v for x in u],False)

	def __ifloordiv__(u,v):
		for i in range(len(u)): u[i]//=v
		return u

	@staticmethod
	def cross(vecarr):
		n=len(vecarr)+1
		ret=Vector(n)
		if n==0: return ret
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

	#---------------------------------------------------------------------------------
	# Misc
	#---------------------------------------------------------------------------------

	def sqr(u):
		return u*u

	def __abs__(u):
		s=u*u
		try:
			return math.sqrt(s)
		except TypeError:
			return s**0.5

	def norm(u): return Vector(u).normalize()

	def normalize(u):
		mag=Matrix.getinverse(abs(u))
		if mag is None: u.randomize()
		else: u*=mag
		return u

	def angle(u,v):
		return math.acos((u*v)/(abs(u)*abs(v)))

	def randomangle(ret,norm,ang):
		# Generate a random vector R such that acos(R*N)<=ang.
		#
		# We do this by generating a random unit vector on the dim-1 sphere that's
		# perpendicular to N. We then rotate the random vector towards N along the
		# plane between the two unit vectors.
		#
		# Given
		#
		#      R=rand vec
		#      C=cos(rand()*ang)
		#      P=(N+(R-N)*u)/|N+(R-N)*u|
		#
		# We want u such that N*P=C.
		dim=len(ret)
		if dim<2:
			for i in range(dim): ret[i]=norm[i]
			return
		# Generate a random vector that's not colinear with norm.
		while True:
			ret.randomize()
			dot=ret*norm
			if dot>-0.9999 and dot<0.9999: break
		# Make ret perpendicular to norm. ret=ret-norm*(ret*norm).
		ret=ret-norm*dot
		ret.normalize()
		# Randomly rotate towards norm. ret=norm+(ret-norm)*u.
		while True:
			cs =cos(random.random()*ang)
			sn2=1.0-cs*cs
			u  =(sn2-cs*math.sqrt(sn2))/(sn2*2-1)
			if u>-1e-10 and u<=1.0: break
		ret=norm+(ret-norm)*u
		ret.normalize()

