/* jshint esversion: 6   */
/* jshint bitwise: false */
/* jshint eqeqeq: true   */
/* jshint curly: true    */


function PhyAssert(condition) {
	if (!condition) {
		throw new Error(condition);
	}
}


//---------------------------------------------------------------------------------
// PRNG


class PhyRand {


	constructor(seed) {
		this.acc=0;
		this.inc=1;
		this.seed(seed);
	}


	seed(seed) {
		if (seed===undefined || seed===null) {
			seed=performance.now();
		}
		this.acc=0;
		this.inc=seed>>>0;
		this.acc=this.getu32();
		this.inc=this.getu32()|1;
	}


	getu32() {
		var val=(this.acc+this.inc)>>>0;
		this.acc=val;
		val=(val+(val<<17))>>>0;val=(val^(val>>>11))>>>0;
		val=(val+(val<< 5))>>>0;val=(val^(val>>> 7))>>>0;
		val=(val+(val<< 9))>>>0;val=(val^(val>>>14))>>>0;
		val=(val+(val<<10))>>>0;val=(val^(val>>> 6))>>>0;
		val=(val+(val<< 7))>>>0;val=(val^(val>>> 9))>>>0;
		return val;
	}


	mod32(mod) {
		var rand,rem,nmod=(-mod)>>>0;
		do {
			rand=this.getu32();
			rem=rand%mod;
		} while (rand-rem>nmod);
		return rem;
	}


	getf64() {
		return this.getu32()*(1.0/4294967296.0);
	}


	static xmbarr=[
		0.0000000000,2.1105791e+05,-5.4199832e+00,0.0000056568,6.9695708e+03,-4.2654963e+00,
		0.0000920071,7.7912181e+02,-3.6959312e+00,0.0007516877,1.6937928e+02,-3.2375953e+00,
		0.0032102442,6.1190088e+01,-2.8902816e+00,0.0088150936,2.8470915e+01,-2.6018590e+00,
		0.0176252084,1.8800444e+01,-2.4314149e+00,0.0283040851,1.2373531e+01,-2.2495070e+00,
		0.0466319112,8.6534303e+00,-2.0760316e+00,0.0672857680,6.8979540e+00,-1.9579131e+00,
		0.0910495504,5.3823501e+00,-1.8199180e+00,0.1221801449,4.5224728e+00,-1.7148581e+00,
		0.1540346442,3.9141567e+00,-1.6211563e+00,0.1900229058,3.4575317e+00,-1.5343871e+00,
		0.2564543024,2.8079448e+00,-1.3677978e+00,0.3543675790,2.6047685e+00,-1.2957987e+00,
		0.4178358886,2.5233767e+00,-1.2617903e+00,0.5881852711,2.6379475e+00,-1.3291791e+00,
		0.6397157999,2.7530438e+00,-1.4028080e+00,0.7303095074,3.3480131e+00,-1.8373198e+00,
		0.7977016349,3.7812818e+00,-2.1829389e+00,0.8484734402,4.7872429e+00,-3.0364702e+00,
		0.8939255135,6.2138677e+00,-4.3117665e+00,0.9239453541,7.8175201e+00,-5.7934537e+00,
		0.9452687641,1.0404724e+01,-8.2390571e+00,0.9628624602,1.4564418e+01,-1.2244270e+01,
		0.9772883839,2.3567788e+01,-2.1043159e+01,0.9881715750,4.4573121e+01,-4.1800032e+01,
		0.9948144543,1.0046744e+02,-9.7404506e+01,0.9980488575,2.5934959e+02,-2.5597666e+02,
		0.9994697975,1.0783868e+03,-1.0745796e+03,0.9999882905,1.3881171e+05,-1.3880629e+05
	];
	getnorm() {
		// Returns a normally distributed random variable. This function uses a linear
		// piecewise approximation of sqrt(2)*erfinv((x+1)*0.5) to quickly compute values.
		// Find the greatest y[i]<=x, then return x*m[i]+b[i].
		var x=this.getf64(),xmb=PhyRand.xmbarr,i=48;
		i+=x<xmb[i]?-24:24;
		i+=x<xmb[i]?-12:12;
		i+=x<xmb[i]?-6:6;
		i+=x<xmb[i]?-3:3;
		i+=x<xmb[i]?-3:0;
		return x*xmb[i+1]+xmb[i+2];
	}
}


//---------------------------------------------------------------------------------


class PhyVec {
	static prng=new PhyRand();


	constructor(elem,nocopy) {
		if (elem===undefined) {
			this.elem=[];
		} else if (elem instanceof PhyVec) {
			this.elem=nocopy?elem.elem:elem.elem.slice();
		} else if (elem.length!==undefined) {
			this.elem=nocopy?elem:elem.slice();
		} else if (typeof(elem)==="number") {
			this.elem=Array(elem).fill(0.0);
		} else {
			console.log("unrecognized vector: ",elem);
			throw "unrecognized vector";
		}
	}



	tostring() {
		return "("+this.elem.join(", ")+")";
	}


	length() {
		return this.elem.length;
	}


	//----------------------------------------
	// Algebra


	neg() {
		return new PhyVec(this.elem.map((x)=>-x),true);
	}


	set(v) {
		this.elem=v.elem.slice();
		return this;
	}


	iadd(v) {
		// u+=v
		var ue=this.elem,ve=v.elem,elems=ue.length;
		for (var i=0;i<elems;i++) {ue[i]+=ve[i];}
		return this;
	}


	add(v) {
		// u+v
		var ue=this.elem,ve=v.elem,elems=ue.length,re=new Array(elems);
		for (var i=0;i<elems;i++) {re[i]=ue[i]+ve[i];}
		return new PhyVec(re,true);
	}


	isub(v) {
		// u-=v
		var ue=this.elem,ve=v.elem,elems=ue.length;
		for (var i=0;i<elems;i++) {ue[i]-=ve[i];}
		return this;
	}



	sub(v) {
		// u-v
		var ue=this.elem,ve=v.elem,elems=ue.length,re=new Array(elems);
		for (var i=0;i<elems;i++) {re[i]=ue[i]-ve[i];}
		return new PhyVec(re,true);
	}



	iscale(s) {
		// u*=s
		var ue=this.elem,elems=ue.length;
		for (var i=0;i<elems;i++) {ue[i]*=s;}
		return this;
	}



	scale(s) {
		// u*s
		var ue=this.elem,elems=ue.length,re=new Array(elems);
		for (var i=0;i<elems;i++) {re[i]=ue[i]*s;}
		return new PhyVec(re,true);
	}



	dot(v) {
		// u*v
		var ue=this.elem,ve=v.elem,elems=ue.length,dot=0;
		for (var i=0;i<elems;i++) {dot+=ue[i]*ve[i];}
		return dot;
	}


	//----------------------------------------
	// Geometry


	sqr() {
		// u*u
		var ue=this.elem,elems=ue.length,dot=0;
		for (var i=0;i<elems;i++) {dot+=ue[i]*ue[i];}
		return dot;
	}


	mag() {
		// sqrt(u*u)
		var ue=this.elem,elems=ue.length,dot=0;
		for (var i=0;i<elems;i++) {dot+=ue[i]*ue[i];}
		return Math.sqrt(dot);
	}


	randomize() {
		var ue=this.elem,elems=ue.length;
		var mag,i,x,prng=PhyVec.prng;
		do {
			mag=0;
			for (i=0;i<elems;i++) {
				x=prng.getnorm();
				ue[i]=x;
				mag+=x*x;
			}
		} while (mag<1e-10);
		mag=1.0/Math.sqrt(mag);
		for (i=0;i<elems;i++) {
			ue[i]*=mag;
		}
		return this;
	}


	static random(dim) {
		return (new PhyVec(dim)).randomize();
	}


	normalize() {
		var ue=this.elem,elems=ue.length,mag=0,i,x;
		for (i=0;i<elems;i++) {
			x=ue[i];
			mag+=x*x;
		}
		if (mag<1e-10) {
			this.randomize();
		} else {
			mag=1.0/Math.sqrt(mag);
			for (i=0;i<elems;i++) {
				ue[i]*=mag;
			}
		}
		return this;
	}


	norm() {
		return (new PhyVec(this)).normalize();
	}
}


//---------------------------------------------------------------------------------


function PhyCreate(displayid) {
	var display=document.getElementById(displayid);
	var self={
		display:   display,
		update:    0,
		dim:       2,
		steps:     8,
		deltatime: 1.0/60.0,
		rnd:       new PhyRand(),
		//gravity:   PhyVecCreate(2)
	};
	var vec=new PhyVec([1.0,-3.0,2.11111]);
	var neg=vec.neg();
	console.log(vec.norm().tostring());
	console.log(vec.tostring());
	console.log(neg.tostring());
	return self;
}