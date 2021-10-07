#background.py -- v1.00 -- Alec Dee, akdee144@gmail.com
#Public domain. This code is provided without warranty; use at your own risk!

#opacity="0.1"
#filter

#id |        desc         | prob |   radius
# 0 | circle              | 0.1  |  0.1+x*1.0
# 1 | circle + small halo | 0.2  |  1.0+x*10.0
# 2 | circle + large halo | 0.3  |  5.0+x*20.0
# 3 | diffraction spikes  | 0.1  | 10.0+x*50.0

import random

stars=1000
w=1000
h=1000

infoarr=[
	[0.1,1.0],
	[0.2,1.0],
	[0.3,1.5],
	[0.05,28.0]
]

header='''<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" viewBox="0 0 {0} {1}">
<defs>
	<g id="star0">
		<circle cx="0" cy="0" r="1.0" stroke-width="0" fill="#ffffff"/>
	</g>
	<g id="star1">
		<circle cx="0" cy="0" r="1.0" stroke-width="0" fill="#ff80ff"/>
	</g>
	<g id="star2">
		<circle cx="0" cy="0" r="1.0" stroke-width="0" fill="#ffa0ff"/>
	</g>
	<radialGradient id="radgrad3">
		<stop offset="0%"   stop-color="#ffffff" stop-opacity="1.0"/>
		<stop offset="10%"  stop-color="#ffffff" stop-opacity="1.0"/>
		<stop offset="11%"  stop-color="#ff00ff" stop-opacity="0.1"/>
		<stop offset="100%" stop-color="#ff00ff" stop-opacity="0.0"/>
	</radialGradient>
	<linearGradient id="repgrad3">
		<stop offset="0%"   stop-color="#ff00ff" stop-opacity="0.00"/>
		<stop offset="9%"   stop-color="#ff00ff" stop-opacity="0.20"/>
		<stop offset="18%"  stop-color="#ff00ff" stop-opacity="0.00"/>
		<stop offset="27%"  stop-color="#ff00ff" stop-opacity="0.60"/>
		<stop offset="36%"  stop-color="#ff00ff" stop-opacity="0.00"/>
		<stop offset="45%"  stop-color="#ffffff" stop-opacity="0.90"/>
		<stop offset="54%"  stop-color="#ffffff" stop-opacity="0.90"/>
		<stop offset="63%"  stop-color="#ff00ff" stop-opacity="0.00"/>
		<stop offset="72%"  stop-color="#ff00ff" stop-opacity="0.60"/>
		<stop offset="81%"  stop-color="#ff00ff" stop-opacity="0.00"/>
		<stop offset="90%"  stop-color="#ff00ff" stop-opacity="0.20"/>
		<stop offset="100%" stop-color="#ff00ff" stop-opacity="0.00"/>
	</linearGradient>
	<g id="star3" transform="rotate(-15)">
		<circle cx="0" cy="0" r="0.8" stroke-width="0" fill="url(#radgrad3)"/>
		<rect x="-1.0" y="-0.01" width="2.0" height="0.02" stroke-width="0" fill="url(#repgrad3)"/>
		<rect x="-1.0" y="-0.01" width="2.0" height="0.02" stroke-width="0" fill="url(#repgrad3)" transform="rotate(90)"/>
	</g>
</defs>'''.format(w,h)

footer='''</svg>
'''

print(header)
for s in range(stars):
	type=0
	while True:
		type=random.randrange(len(infoarr))
		prob,rad=infoarr[type]
		if random.random()<=prob: break
	x=random.randrange(w)
	y=random.randrange(h)
	r=(abs(random.random())*0.8+0.4)*rad
	fmt='<use xlink:href="#star{0}" transform="translate({1},{2}) scale({3:.4f})" opacity="{4:.4f}"/>'
	fmt=fmt.format(type,"{0}","{1}",r,min(1.0,random.random()*0.9+0.5)*0.5)
	print(fmt.format(x,y))
	if x<r  : print(fmt.format(w+x,y))
	if y<r  : print(fmt.format(x,h+y))
	if x>w-r: print(fmt.format(w-x,y))
	if y>h-r: print(fmt.format(x,h-y))
print(footer)

