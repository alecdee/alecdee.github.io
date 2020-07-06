import subprocess,os,filecmp,math,random

def calgarytable():
	print("<table class=\"datatable calgarytable\">")
	print("<tr><td>file</td><td>original size</td><td>compressed size</td><td>ratio</td></tr>")
	root=os.path.join(os.path.expanduser("~"),"Downloads/calgary")
	encpath=os.path.join(root,"enc.dat")
	decpath=os.path.join(root,"dec.dat")
	origsum,encsum=0,0
	for dirpath,dnames,fnames in os.walk(root):
		fnames.sort()
		for fname in fnames:
			path=os.path.join(dirpath,fname)
			if path==encpath or path==decpath: continue
			subprocess.call("pypy ./RangeEncoder.py -c "+   path+" "+encpath,shell=True)
			subprocess.call("pypy ./RangeEncoder.py -d "+encpath+" "+decpath,shell=True)
			assert(filecmp.cmp(path,decpath,False))
			origsize=os.path.getsize(path)
			encsize=os.path.getsize(encpath)
			origsum+=origsize
			encsum+=encsize
			print("<tr><td>{0}</td><td>{1:,}</td><td>{2:,}</td><td>{3}%</td></tr>".format(fname,origsize,encsize,int(100.0-encsize*100.0/origsize)))
	print("<tr><td>{0}</td><td>{1:,}</td><td>{2:,}</td><td>{3}%</td></tr>".format("=",origsum,encsum,int(100.0-encsum*100.0/origsum)))
	print("</table>")

def examplediagrams(encoding,decodecode):
	symprob=(0.0,0.2,0.3,0.55,1.0)
	low,rang=0.0,1.0
	msg="ABAD"
	msglen=len(msg)
	worky,workheight=580,580
	linewidth,minheight=5,22
	rectarr=[]
	symarr=[]
	valarr=[]
	colors=["ff0000","008000","0000ff","ffa000"]
	for i in range(msglen):
		s=ord(msg[i])-65
		if i+1<msglen:
			fillh=[minheight]*4
			fillh[s]=workheight-linewidth*5-minheight*3
		else:
			space=workheight-5*linewidth
			fillh=[(symprob[j+1]-symprob[j])*space for j in range(4)]
		x=20+130*i
		sepy=[worky-(j+1)*linewidth-sum(fillh[:j]) for j in range(5)]
		for i in range(3,-1,-1):
			y=sepy[i+1]+linewidth
			rectarr.append('<rect x="{0}" y="{1}" width="{2}" height="{3}" fill="#{4}"/>'.format(x,round(y),linewidth,round(fillh[i]+1),colors[i]))
			symarr.append('<text x="{0}" y="{1}" dy="0.4em">{2}</text>'.format(x-20,round(y+fillh[i]*0.5),chr(65+i)))
		scale=[j*rang+low for j in symprob]
		pad=0
		for j in scale: pad=max(pad,len(str(j))-2)
		for j in range(4,-1,-1):
			y=sepy[j]
			rectarr.append('<rect x="{0}" y="{1}" width="{2}" height="{3}"/>'.format(x,round(y),22,linewidth))
			valarr.append('<text x="{0}" y="{1}" dy="0.4em">{2:.{3}f}</text>'.format(x+26,round(y+linewidth*0.5),scale[j],pad))
		worky=sepy[s]+linewidth
		workheight=fillh[s]+linewidth*2
		low=scale[s]
		rang=scale[s+1]-low
	print('<svg version="1.1" viewBox="0 0 1000 600">')
	print('<rect x="0" y="0" width="2000" height="1000" fill="#eeeeee"/>')
	print('<g transform="translate(0,10)">')
	if encoding:
		x=20+130*msglen
		y=worky-linewidth
		print('\t<line x1="{0}" y1="{1}" x2="{0}" y2="{2}" stroke="#000000" stroke-dasharray="6,6" stroke-width="3"/>'.format(x,y+linewidth,round(y-workheight+linewidth)))
		valarr.append('<text x="{0}" y="{1}" dy="0.4em">range</text>'.format(x+7,round(y-workheight*0.5+linewidth)))
		valarr.append('<text x="{0}" y="{1}" dy="0.4em">low</text>'.format(x+7,round(y+linewidth)))
	else:
		x=8+130*msglen
		y=worky-workheight*(decodecode-low)/rang-5+linewidth*0.5
		print('\t<line x1="0" y1="{0}" x2="{1}" y2="{0}" stroke="#000000" stroke-dasharray="6,6" stroke-width="3"/>'.format(y,x))
		valarr.append('<text x="{0}" y="{1}" dy="0.4em">{2}</text>'.format(x+7,y,decodecode))
	for r in rectarr: print("\t"+r)
	print('\t<g style="font-size:125%">')
	for s in symarr: print("\t\t"+s)
	print('\t</g>')
	print('\t<g style="font-size:85%">')
	for v in valarr: print("\t\t"+v)
	print('\t</g>')
	print('</g>')
	print('</svg>')

def accuracydiagram():
	import matplotlib.pyplot as plt
	def theorybits(seq,symprob):
		syms=len(symprob)-1
		cnt=[0]*syms
		for s in seq: cnt[s]+=1
		bits,lg2=0.0,math.log(2.0)
		for s in range(syms):
			prob=float(symprob[s+1]-symprob[s])/symprob[syms]
			bits-=cnt[s]*(math.log(prob)/lg2)
		return bits
	def imprecisebits(seq,symprob,bits):
		norm=1<<bits
		low,rang,half=0,norm,norm//2
		bits=0
		den=symprob[-1]
		for s in seq:
			rang//=den
			low+=rang*symprob[s]
			rang*=symprob[s+1]-symprob[s]
			while rang<=half:
				bits+=1
				low+=low
				rang+=rang
			low&=norm-1
		dif=low^(low+rang)
		while dif<norm:
			bits+=1
			dif+=dif
		return bits+1
	def precisebits(seq,symprob,bits):
		norm=1<<bits
		low,rang,half=0,norm,norm//2
		bits=0
		den=symprob[-1]
		for s in seq:
			off=(rang*symprob[s])//den
			low+=off
			rang=(rang*symprob[s+1])//den-off
			while rang<=half:
				bits+=1
				low+=low
				rang+=rang
			low&=norm-1
		dif=low^(low+rang)
		while dif<norm:
			bits+=1
			dif+=dif
		return bits+1
	random.seed(0)
	trials=10000
	maxprob=1<<31
	datapoint=[]
	for bits in range(32,45):
		theorysum,precisesum,imprecisesum=0.0,0.0,0.0
		for trial in range(trials):
			syms=random.randrange(256)+1
			symprob=set([0])
			while len(symprob)<=syms:
				symprob.add(random.randrange(maxprob+1))
			symprob=sorted(list(symprob))
			seqlen=random.randrange(1000)+100
			seq=[random.randrange(syms) for i in range(seqlen)]
			theorysum+=theorybits(seq,symprob)
			precisesum+=precisebits(seq,symprob,bits)
			imprecisesum+=imprecisebits(seq,symprob,bits)
		theorysum/=trials
		precisesum/=trials
		imprecisesum/=trials
		preciseerr=(precisesum-theorysum)/theorysum
		impreciseerr=(imprecisesum-theorysum)/theorysum
		datapoint.append((bits,preciseerr,impreciseerr))
	for data in datapoint:
		print(data)
	fig=plt.figure(figsize=(12,6),dpi=100)
	plt.xlabel("bits",fontsize=15)
	plt.ylabel("error",fontsize=15)
	xform=plt.gca()
	xform.get_xaxis().get_major_formatter().set_scientific(False)
	maxy=datapoint[0][2]*1.01
	plt.xlim(datapoint[0][0],datapoint[-1][0])
	plt.ylim(0,maxy)
	legend=[]
	for i in range(2):
		xaxis=[data[0] for data in datapoint]
		yaxis=[data[i+1] for data in datapoint]
		name=["accurate","innacurate"][i]
		legend.append(plt.plot(xaxis,yaxis,label=name)[0])
	plt.legend(handles=legend)
	plt.show()

#calgarytable()
examplediagrams(False,0.0422)
#accuracydiagram()

