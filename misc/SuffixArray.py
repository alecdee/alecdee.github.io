# SuffixArray.py - v1.00
#
# Copyright 2022 Alec Dee - MIT license - SPDX: MIT
# alecdee.github.io - akdee144@gmail.com

# Python2 compatibility.
import sys
if sys.version_info[0]<=2:
	range=xrange

# A suffix array should only be concerned with one sequence. Multiple concatenated
# sequences can be decoded by the invoking program.

# TODO:
# longest palindrome
# count palindromes
# get BWT
# maximum unique matching
# substring counting for n=aaaaa... and n=abcde...

class SuffixArray(object):
	def __init__(self,*args):
		self.sentinels=[]
		self.sufs=0
		self.seq=[]
		self.sa=[]
		self.inv=[]
		self.lcp=[]
		self.la=[]
		if args:
			self.addstr(*args)
			self.sort()

	def addstr(self,*args):
		"""Adds any number of sequences. Returns the first index."""
		sumlen=0
		argcnt=len(args)
		for arg in args:
			sumlen+=len(arg)+1
		sufs=self.sufs
		self.seq+=[None]*sumlen
		self.sa+=list(range(sufs,sufs+sumlen))
		self.inv+=list(range(sufs,sufs+sumlen))
		self.lcp+=[0]*sumlen
		self.la+=[0]*sumlen
		seq=self.seq
		la=self.la
		for arg in args:
			l=len(arg)
			for a in arg:
				seq[sufs]=a
				la[sufs]=l
				l-=1
				sufs+=1
			self.sentinels.append(sufs)
			seq[sufs]=None
			sufs+=1
		base=self.sufs
		self.sufs=sufs
		return base

	def sufstr(self,i):
		# Print suffix i.
		suf=self.sa[i]
		l=self.la[i]
		line="{0:02d}: ".format(suf)
		for j in range(suf,suf+l):
			line+=str(self.seq[j])+","
		line+="$"+str(suf+l)
		return line

	#---------------------------------------------------------------------------------
	# Construction
	#---------------------------------------------------------------------------------

	def sort(self):
		# Sort the suffixes and compute the inverse and lcp arrays. We use Larsson and
		# Sadakane's run algorithm.
		sufs=self.sufs
		if sufs==0:
			return
		sents=len(self.sentinels)
		seq=self.seq
		sa=self.sa
		inv=self.inv
		lcp=self.lcp
		# Set up the sa array and move the sentinels out of it so they aren't used in any
		# comparisons. Since we know sentinel Sx<Sy for x<y, and S[x]<any character, we
		# know that they would be sorted such that sa=[S0,S1,...,SN,actual characters].
		for i in range(sufs):
			sa[i]=i
		for i in range(sents):
			s=self.sentinels[i]
			inv[s]=i
			sa[s]=sa[i]
			sa[i]=s
			lcp[i]=s
		# Sort the first characters of the suffixes. Skip the sentinels.
		step=1
		while step<sufs:
			dst,stop1=sents,0
			while dst<sufs:
				if dst>=stop1:
					start0=dst
					stop0=dst+step
					start1=stop0
					stop1=min(stop0+step,sufs)
				if start0<stop0 and (start1>=stop1 or seq[sa[start0]]<seq[sa[start1]]):
					lcp[dst]=sa[start0]
					start0+=1
				else:
					lcp[dst]=sa[start1]
					start1+=1
				dst+=1
			sa,lcp=lcp,sa
			step+=step
		self.sa,self.lcp=sa,lcp
		# Identify runs of characters in the sorted suffixes and mark them such that
		# inv[sa[i]]=start for i>=start and seq[sa[i]]=seq[sa[start]]. As the array gets
		# sorted, the inv array will be refined to the individual inverse positions. Also
		# mark each group of runs such that group[start,start+1]=[next,stop]. Groups are
		# stored in the lcp array.
		prev,start=0,sents
		for i in range(start,sufs+1):
			if i==sufs or seq[sa[i]]!=seq[sa[start]]:
				if i-start>1:
					lcp[prev]=start
					prev=start
					lcp[prev+1]=i
				start=i
			if i<sufs:
				inv[sa[i]]=start
		lcp[prev]=sufs
		# Begin sorting each run until there are no runs left.
		bits=(sufs-1).bit_length()
		count=[0]*256
		step=1
		while lcp[0]<sufs:
			prev,start=0,lcp[0]
			while start<sufs:
				# Assume all suffixes have been step-sorted. We can now sort 2 suffixes by
				# assuming their tails have been sorted and comparing them. The relative ranking
				# of their tails is given by inv[sa[i]+step]. If the 2 suffixes have the same tail
				# rank, they will be regrouped later and will require additional sorting passes.
				next,stop=lcp[start],lcp[start+1]
				src,dst=sa,lcp
				if stop-start<30:
					# Sort small groups by insertion sort.
					for i in range(start+1,stop):
						j,s=i,src[i]
						r=inv[s+step]
						while j>start and r<inv[src[j-1]+step]:
							src[j]=src[j-1]
							j-=1
						src[j]=s
				else:
					# Sort large groups by radix sort.
					for shift in range(0,bits,8):
						for i in range(256):
							count[i]=0
						for i in range(start,stop):
							v=(inv[src[i]+step]>>shift)&255
							count[v]+=1
						total=start
						for i in range(256):
							tmp=count[i]
							count[i]=total
							total+=tmp
						for i in range(start,stop):
							v=(inv[src[i]+step]>>shift)&255
							dst[count[v]]=src[i]
							count[v]+=1
						src,dst=dst,src
				# Store the ranking of each suffix's tail ahead of time, since some suffixes in
				# the group may also have tails in this group.
				for i in range(start,stop):
					sa[i]=src[i]
					lcp[i]=inv[src[i]+step]
				# Identify groups that have the same rank and add them for further sorting. Also
				# recompute the new ranking of each suffix in the group.
				for i in range(start+1,stop+1):
					if i==stop or lcp[i]!=lcp[start]:
						if i-start>1:
							lcp[prev]=start
							prev=start
							lcp[prev+1]=i
						start=i
					if i<stop:
						inv[sa[i]]=start
				lcp[prev]=next
				start=next
			step+=step
		# Update the suffix length array to the new sorted positions.
		la=self.la
		spos,sval=-1,-1
		for i in range(sufs):
			if i>sval:
				spos+=1
				sval=self.sentinels[spos]
			la[inv[i]]=sval-i
		# Given the inverse suffix table, perform Kasai's LCP construction.
		l=0
		for a in range(sufs):
			i=inv[a]
			if i:
				b=sa[i-1]
				m=min(la[i],la[i-1])
				while l<m and seq[a+l]==seq[b+l]:
					l+=1
			lcp[i]=l
			l-=l>0

	#---------------------------------------------------------------------------------
	# Sequence Operations
	#---------------------------------------------------------------------------------

	def findfirst(self,s):
		"""Finds the first i such that sa[i][0,1,2,...]=s."""
		# When performing a binary search we may set lo=i if sa[i]<s or sa[i]<=s. If we
		# choose sa[i]<=s, then the first instance where sa[i]=s will set lo and restrict
		# us from finding any sa[j]=s for j<i. Thus we set lo on sa[i]<s.
		#
		# As we run the binary search, track the matching length for the lo and hi bounds.
		# Then at any given step, we will know that the first min(loeq,hieq) values in
		# sa[i], for lo<=i<=hi, already match the string.
		#
		# When the binary search completes, lo will equal hi, but only hieq will be set to
		# the true matching length. Furthermore, hi will only be set less than sufs if we
		# find an i such that sa[i]>=s. Thus, if hi=sufs, then sa[i]<s for all i and we
		# know the string isn't in sa. Otherwise, check if hieq=slen.
		#
		# Complexity: |s|*log2(|sa|).
		lo,hi=0,self.sufs
		loeq,hieq=0,0
		seq=self.seq
		sa,la=self.sa,self.la
		slen=len(s)
		while lo<hi:
			mid=(lo+hi)//2
			mlen=min(la[mid],slen)
			suf=sa[mid]
			lt=mlen<slen
			eq=min(loeq,hieq)
			while eq<mlen:
				if seq[suf+eq]!=s[eq]:
					lt=seq[suf+eq]<s[eq]
					break
				eq+=1
			if lt:
				lo=mid+1
				loeq=eq
			else:
				hi=mid
				hieq=eq
		if hi>=self.sufs or hieq<slen:
			return None
		return hi

	def findlast(self,s):
		"""Finds the last i such that sa[i][0,1,2,...]=s."""
		# Same as findfirst.
		lo,hi=-1,self.sufs-1
		loeq,hieq=0,0
		seq=self.seq
		sa,la=self.sa,self.la
		slen=len(s)
		while lo<hi:
			mid=(lo+hi+1)//2
			mlen=min(la[mid],slen)
			suf=sa[mid]
			le=mlen<=slen
			eq=min(loeq,hieq)
			while eq<mlen:
				if seq[suf+eq]!=s[eq]:
					le=seq[suf+eq]<s[eq]
					break
				eq+=1
			if le:
				lo=mid
				loeq=eq
			else:
				hi=mid-1
				hieq=eq
		if lo<0 or loeq<slen:
			return None
		return lo

	def substrings(self):
		"""Count all unique substrings."""
		# Minimum is n when sa="aaaaaa...".
		# Maximum is n*(n+1)/2 when sa="abcde...".
		sufs=self.sufs
		la,lcp=self.la,self.lcp
		cnt=0
		for i in range(sufs):
			cnt+=la[i]-lcp[i]
		return cnt

