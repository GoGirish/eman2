#!/usr/bin/env python

#
# Author: Steven Ludtke, 01/03/07 (sludtke@bcm.edu)
# Copyright (c) 2000-2007 Baylor College of Medicine
#
# This software is issued under a joint BSD/GNU license. You may use the
# source code in this file under either license. However, note that the
# complete EMAN2 and SPARX software packages have some GPL dependencies,
# so you are responsible for compliance with the licenses of these packages
# if you opt to use BSD licensing. The warranty disclaimer below holds
# in either instance.
#
# This complete copyright notice must be included in any revised version of the
# source code. Additional authorship citations may be added, but existing
# author citations must be preserved.
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  2111-1307 USA
#
#

# e2stacktoanim.py  01/03/07  Steven Ludtke
# This program will convert a 2D image stack into a GIF animation


from EMAN2 import *
from optparse import OptionParser
from math import *
import os
import sys

def stacktoanim(stack,outpath):
	"""Takes an input list of images and and output pathname. Converts each image to a standard 2D image
	format, then produces a GIF animation. Requires functional ImageMagick installation."""
	for i,im in enumerate(stack):
		im.set_attr("render_min",im.get_attr("mean")-im.get_attr("sigma")*3.0)
		im.set_attr("render_max",im.get_attr("mean")+im.get_attr("sigma")*3.0)
		im.write_image("tmp_img-%03d.pgm"%i)
		print "%d. %1.3f - %1.3f"%(i,im.get_attr("render_min"),im.get_attr("render_max"))
	os.system("convert -delay 10 tmp_img-*.pgm %s "%outpath)
	
	for i in range(len(stack)):
		os.unlink("tmp_img-%03d.pgm"%i)

def main():
	progname = os.path.basename(sys.argv[0])
	usage = """%prog [options] input_stack.hed output.(gif:pnm)
	
Converts a 2D image stack into a GIF/PNM animation using ImageMagick"""

	parser = OptionParser(usage=usage,version=EMANVERSION)

	parser.add_option("--scale", "-S", type="float", help="Scale factor",default=1.0)
#	parser.add_option("--maxshift","-M", type="int", help="Maximum translational error between images (pixels), default=64",default=64.0)
#	parser.add_option("--mode",type="string",help="centering mode 'modeshift', 'censym' or 'region,<x>,<y>,<clipsize>,<alisize>",default="censym")
#	parser.add_option("--twopass",action="store_true",default=False,help="Skip automatic tilt axis location, use fixed angle from x")
	
	(options, args) = parser.parse_args()
	if len(args)<2 : parser.error("Input and output files required")
	
	a=EMData.read_images(args[0])
	
	# rescale images if requested
	if options.scale!=1.0 :
		olds=(a[0].get_xsize(),a[0].get_ysize())
		news=(int(olds[0]*options.scale),int(olds[1]*options.scale))
		for i in range(len(a)):
			if options.scale<1.0: a[i].scale(options.scale)
			a[i]=a[i].get_clip(Region((olds[0]-news[0])/2.0,(olds[1]-news[1])/2.0,news[0],news[1]))
			if options.scale>1.0: a[i].scale(options.scale)
			
	stacktoanim(a,args[1])

if __name__ == "__main__":
    main()
