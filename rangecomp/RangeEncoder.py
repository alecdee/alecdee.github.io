"""
RangeEncoder.py - v1.01

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
This range encoder will convert a sequence of intervals to and from a binary
coded fraction. When these intervals are mapped to cumulative symbol
probabilities, we can compress or decompress data.

Usage:
python RangeEncoder.py -c image.bmp compress.dat
python RangeEncoder.py -d compress.dat decompress.bmp

--------------------------------------------------------------------------------
TODO

Determine if assert(self.low>=off) is necessary.
Figure out a simpler bit queuing system.
"""

class RangeEncoder(object):
	def __init__(self,encoding,bits=32):
		"""If encoding=True, intialize and support encoding operations. Otherwise,
		support decoding operations. More state bits will give better encoding
		accuracy at the cost of speed."""
		assert(encoding==False or encoding==True)
		assert(bits>0)
		self.encoding=encoding
		self.finished=False
		#Range state.
		self.bits=bits
		self.norm=1<<bits
		self.half=self.norm>>1
		self.low=0
		self.range=self.norm if encoding else 1
		#Bit queue for data we're ready to input or output.
		qmask=(bits*4-1)|8
		while qmask&(qmask+1): qmask|=qmask>>1
		self.qmask=qmask
		self.qcount=[0]*(qmask+1)
		self.qlen=0
		self.qpos=0

	def encode(self,intlow,inthigh,intden):
		"""Encode an interval into the range."""
		assert(self.encoding and self.finished==False)
		assert(0<=intlow and intlow<inthigh and inthigh<=intden and intden<=self.half+1)
		assert(self.qlen<=(self.qmask>>1))
		qmask=self.qmask
		qcount=self.qcount
		qpos=self.qpos
		qlen=self.qlen
		#Shift the range.
		half=self.half
		low=self.low
		range=self.range
		while range<=half:
			#Push a settled state bit the to queue.
			dif=qpos^((low&half)!=0)
			qpos=(qpos+(dif&1))&qmask
			qlen+=qcount[qpos]==0
			qcount[qpos]+=1
			low+=low
			range+=range
		norm=self.norm
		low&=norm-1
		#Scale the range to fit in the interval.
		off=(range*intlow)//intden
		low+=off
		range=(range*inthigh)//intden-off
		#If we need to carry.
		if low>=norm:
			#Propagate a carry up our queue. If the previous bits were 0's, flip one to 1.
			#Otherwise, flip all 1's to 0's.
			low-=norm
			#If we're on an odd parity, align us with an even parity.
			odd=qpos&1
			ones=qcount[qpos]&-odd
			qcount[qpos]-=ones
			qpos-=odd
			#Even parity carry operation.
			qcount[qpos]-=1
			inc=1 if qcount[qpos] else -1
			qpos=(qpos+inc)&qmask
			qcount[qpos]+=1
			#Length correction.
			qlen+=inc
			qlen+=qlen<=odd
			#If we were on an odd parity, add in the 1's-turned-0's.
			qpos=(qpos+odd)&qmask
			qcount[qpos]+=ones
		self.low=low
		self.range=range
		self.qpos=qpos
		self.qlen=qlen

	def finish(self):
		"""Flush the remaining data from the range."""
		if self.finished: return
		self.finished=True
		if self.encoding==False:
			#We have no more data to decode. Pad the queue with 1's from now on.
			return
		assert(self.qlen<=(self.qmask>>1))
		#We have no more data to encode. Flush out the minimum number of bits necessary
		#to satisfy low<=flush+1's<low+range. Then pad with 1's till we're byte aligned.
		qmask=self.qmask
		qcount=self.qcount
		qpos=self.qpos
		qlen=self.qlen
		low=self.low
		norm=self.norm
		dif=low^(low+self.range)
		while dif<norm:
			low+=low
			dif+=dif
			flip=qpos^((low&norm)!=0)
			qpos=(qpos+(flip&1))&qmask
			qlen+=qcount[qpos]==0
			qcount[qpos]+=1
		#Calculate how many bits need to be appended to be byte aligned.
		pad=0
		for i in range(qlen):
			pad-=qcount[(qpos-i)&qmask]
		pad&=7
		#If we're not byte aligned.
		if pad!=0:
			#Align us with an odd parity and add the pad. Add 1 to qlen if qpos&1=0.
			qlen-=qpos
			qpos|=1
			qlen+=qpos
			qcount[qpos]+=pad
		self.qpos=qpos
		self.qlen=qlen

	def hasbyte(self):
		"""Is a byte ready to be output?"""
		return self.qlen>=10 or (self.finished and self.qlen)

	def getbyte(self):
		"""If data is ready to be output, returns an integer in the interval
		[0,256). Otherwise, returns None."""
		assert(self.encoding)
		qlen=self.qlen
		if qlen<10 and (self.finished==False or qlen==0):
			return None
		#Go back from the end of the queue and shift bits into ret. If we use all bits at
		#a position, advance the position.
		qmask=self.qmask
		orig=self.qpos+1
		qpos=orig-qlen
		qcount=self.qcount
		ret=0
		for i in range(8):
			ret+=ret+(qpos&1)
			pos=qpos&qmask
			qcount[pos]-=1
			qpos+=qcount[pos]==0
		self.qlen=orig-qpos
		return ret

	def decode(self,intden):
		"""Given an interval denominator, find a value in [0,intden) that will fall
		in to some interval. Returns None if more data is needed."""
		assert(self.encoding==False)
		assert(intden<=self.half+1)
		qmask=self.qmask
		qpos=self.qpos
		qlen=(self.qlen-qpos)&qmask
		qcount=self.qcount
		if qlen<self.bits:
			#If the input has not signaled it is finished, request more bits.
			if self.finished==False: return None
			#If we are reading from a finished stream, pad the entire queue with 1's.
			qlen=self.qlen
			while True:
				qcount[qlen]=1
				qlen=(qlen+1)&qmask
				if qlen==qpos: break
			self.qlen=(qpos-1)&qmask
		#Shift the range.
		half=self.half
		low=self.low
		range=self.range
		while range<=half:
			low+=low+qcount[qpos]
			qpos=(qpos+1)&qmask
			range+=range
		self.qpos=qpos
		self.low=low
		self.range=range
		#Scale low to yield our desired code value.
		return (low*intden+intden-1)//range

	def scale(self,intlow,inthigh,intden):
		"""Given an interval, scale the range to fit in the interval."""
		assert(self.encoding==False)
		assert(0<=intlow and intlow<inthigh and inthigh<=intden and intden<=self.half+1)
		range=self.range
		off=(range*intlow)//intden
		assert(self.low>=off)
		self.low-=off
		self.range=(range*inthigh)//intden-off

	def addbyte(self,byte):
		"""Add an input byte to the decoding queue."""
		assert(self.encoding==False and self.finished==False)
		assert(((self.qlen-self.qpos)&self.qmask)<=self.qmask-8)
		qmask=self.qmask
		qlen=self.qlen
		qcount=self.qcount
		for i in range(7,-1,-1):
			qcount[qlen]=(byte>>i)&1
			qlen=(qlen+1)&qmask
		self.qlen=qlen


if __name__=="__main__":
	#Example compressor and decompressor using an adaptive order-0 symbol model.
	import os,sys,struct

	#Parse arguments.
	if len(sys.argv)!=4:
		print("3 arguments expected\npython RangeEncoder.py [-c|-d] infile outfile")
		exit()
	mode,infile,outfile=sys.argv[1:]
	if mode!="-c" and mode!="-d":
		print("mode must be -c or -d")
		exit()

	#Adaptive order-0 symbol model.
	prob=list(range(0,257*32,32))
	def incprob(sym):
		#Increment the probability of a given symbol.
		for i in range(sym+1,257): prob[i]+=32
		if prob[256]>=65536:
			#Periodically halve all probabilities to help the model forget old symbols.
			for i in range(256,0,-1): prob[i]-=prob[i-1]-1
			for i in range(1,257): prob[i]=prob[i-1]+(prob[i]>>1)
	def findsym(code):
		#Find the symbol who's cumulative interval encapsulates the given code.
		for sym in range(1,257):
			if prob[sym]>code: return sym-1

	instream=open(infile,"rb")
	outstream=open(outfile,"wb")
	insize=os.path.getsize(infile)
	buf=bytearray(1)
	if mode=="-c":
		#Compress a file.
		enc=RangeEncoder(True)
		outstream.write(struct.pack(">i",insize))
		for inpos in range(insize+1):
			if inpos<insize:
				#Encode a symbol.
				byte=ord(instream.read(1))
				enc.encode(prob[byte],prob[byte+1],prob[256])
				incprob(byte)
			else:
				enc.finish()
			#While the encoder has bytes to output, output.
			while enc.hasbyte():
				buf[0]=enc.getbyte()
				outstream.write(buf)
	else:
		#Decompress a file.
		dec=RangeEncoder(False)
		outsize=struct.unpack(">i",instream.read(4))[0]
		inpos,outpos=4,0
		while outpos<outsize:
			decode=dec.decode(prob[256])
			if decode!=None:
				#We are ready to decode a symbol.
				buf[0]=sym=findsym(decode)
				dec.scale(prob[sym],prob[sym+1],prob[256])
				incprob(sym)
				outstream.write(buf)
				outpos+=1
			elif inpos<insize:
				#We need more input data.
				dec.addbyte(ord(instream.read(1)))
				inpos+=1
			else:
				#Signal that we have no more input data.
				dec.finish()
	outstream.close()
	instream.close()

