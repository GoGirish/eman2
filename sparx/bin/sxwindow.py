#!/usr/bin/env python
#
# Author: T. Durmaz 08/29/2014 (tunay.durmaz@uth.tmc.edu)
# Copyright (c) 2014 The University of Texas - Houston Medical School
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
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307 USA

import os, sys
import json

from optparse import *
# from argparse import *
from EMAN2 import *
from EMAN2db import *
from EMAN2jsondb import *
from emboxerbase import *

from sparx import *

"""
This program is used to window particles from a micrograph. The coordinates of the particles are given as input.
"""

def baseroot(path):
	return os.path.splitext(os.path.basename(path))[0]

def build_micnames(options, args):
	# 	Build micrograph basename list
	extension = options.micsuffix
	if len(args) > 0:
		micnames = args
	else:
		import glob
		micnames = glob.glob(os.path.join(options.indir, options.nameroot + "*" + extension))

	micnames = [ baseroot(m) for m in micnames]

	return micnames

def check_options(options, progname):
	if options.outdir == None:
		print "\nOutput directory must be specified with option --outdir. Type %s -h for help.\n" % progname
		sys.exit()
		
	if  options.coordsdir == None:
		print "\nCoordinates directory must be specified with option --coords_dir. Type %s -h for help.\n" % progname
		sys.exit()

	if  options.coords_extension == None:
		print "\nExtension of coordinates file must be specified with option --coords_extension. Type %s -h for help.\n" % progname
		sys.exit()

	if options.coords_format == None:
		print "\nCoordinate file format must be specified with option --coords_format. Type %s -h for help.\n" % progname
		sys.exit()
		
	if not(options.coords_format.lower() == 'sparx' or options.coords_format.lower() == 'eman1' or options.coords_format.lower() == 'eman2' or options.coords_format.lower() == 'spider') :
		print "\nInvalid option value for --coords_format: %s Type %s -h for help.\n" % (options.coords_format.lower(), progname)
		sys.exit()

def main():
# 	parser1 = argparse.ArgumentParser(description='This program is used to window particles from a micrograph. The coordinates of the particles are given as input.')
# 	parser1.add_argument()

	progname = os.path.basename(sys.argv[0])
	usage = progname + " [micrographs list] ...  --coords_dir=coords_dir  --coords_suffix=coords_suffix" + \
	                                          "  --coords_extension=coords_extension  --coords_format=coords_format" + \
	                                          "  --indir=input_dir  --importctf=ctf_file  --limitctf" + \
	                                          "  --input_pixel=input_pixel  --new_pixel=new_pixel --box_size=box_size" + \
	                                          "  --outdir=outdir  --outsuffix=outsuffix  --micsuffix=micsuffix" + \
	                                          "  --nameroot=nameroot  --invert" + \
	                                          "  --defocuserror=defocuserror  --astigmatismerror=astigmatismerror"

	parser = OptionParser(usage, version=SPARXVERSION)

	parser.add_option('--coords_dir',       dest='coordsdir',                 help='Directory containing files with particle coordinates.')
	parser.add_option('--coords_suffix',                   default="",        help='Suffix of coordinate files. For example "_ptcls".')
	parser.add_option('--coords_extension',                                   help='File extension of coordinate files. e.g "box" for eman1, "json" for eman2, ...') # required
	parser.add_option('--coords_format',                                      help='Format of coordinates file: "sparx", "eman1", "eman2", or "spider". The coordinates of sparx, eman2, and spider format is particle center. The coordinates of eman1 format is particle box corner associated with the original box size.')	
	parser.add_option("--indir",            type="string", default= ".",      help="Directory containing micrographs to be processed. (Default: current directory)")
	parser.add_option('--importctf',                                          help='File name with CTF parameters produced by sxcter.')
	parser.add_option("--limitctf",         action="store_true", default=False,     help="Filter micrographs based on the CTF limit. (Default: no filter)")
	parser.add_option('--input_pixel',      type=float,    default=1.0,       help='input pixel size in Angstroms. (Default: 1.0A)')
	parser.add_option("--new_pixel",        type=float,    default=-1.0,      help="New pixel size to which the micrograph should be resampled. Default no resampling.")
	parser.add_option('--box_size',         type=int,      default=256,       help='x and y dimension in pixels of square area to be windowed. Pixel size is assumed to be new_pixel_size. (Default 256)')
	parser.add_option('--outdir',                                             help='Output directory')
	parser.add_option('--outsuffix',        type=str,      default="_ptcls",  help="Suffix for output stack. (Default '_ptcls' ")	
	parser.add_option("--micsuffix",        type=str,      default="hdf",     help="A string denoting micrograph type. (Default 'hdf')")
	parser.add_option("--nameroot",         type="string", default="",        help="Prefix of micrographs to be processed.")
	parser.add_option("--invert",           action="store_true", default=False, help="Invert image contrast (recommended for cryo data) (Default, no contrast inversion)")
	parser.add_option("--defocuserror",     type="float",  default=1000000.0, help="Exclude micrographs whose relative defocus error as estimated by sxcter is larger than defocuserror percent.  The error is computed as (std dev defocus)/defocus*100%.  (Default: include all irrespective of error values.)" )
	parser.add_option("--astigmatismerror", type="float",  default=360.0,     help="Set to zero astigmatism for micrographs whose astigmatism angular error as estimated by sxcter is larger than astigmatismerror degrees. (Default: include all irrespective of error values.)")

	(options, args) = parser.parse_args()
	
	box_size = options.box_size
	box_half = box_size // 2
	options.micsuffix = "." + options.micsuffix
	cterr = [options.defocuserror/100.0, options.astigmatismerror]
	
	new_pixel_size = options.new_pixel
	if new_pixel_size < 0: new_pixel_size = options.input_pixel
	
	check_options(options, progname)
	
	extension_coord = options.coords_suffix + "." + options.coords_extension
	
# 	Build micrograph basename list
	micnames = build_micnames(options, args)
# 	If there is no micrographs, exit
	if len(micnames) == 0:
		print usage
		sys.exit()
	
# 	Load CTFs
	if options.importctf:
		ctfs0 = read_text_row(options.importctf)

		ctfs={}
		for i in xrange(len(ctfs0)):
			ctf=ctfs0[i]
			basemic = baseroot(ctf[-1])

			if(ctf[8]/ctf[0] > cterr[0]):
				print_msg('Defocus error %f exceeds the threshold. Micrograph %s rejected.\n'%(ctf[8]/ctf[0], basemic))
			else:
				if(ctf[10] > cterr[1] ):
					ctf[6] = 0.0
					ctf[7] = 0.0
				ctfs[basemic] = ctf

	mask = model_circle(box_size//2, box_size, box_size)

# 	Loop over micrographs
	for k in range(len(micnames)):
		# basename is name of micrograph minus the path and extension
		basename = micnames[k]
		f_mic    = os.path.join(os.path.abspath(options.indir), basename + options.micsuffix)
		f_info   = os.path.join(options.coordsdir, basename + extension_coord)

# 		CHECKS: BEGIN
# 		IF micrograph exists
		if not os.path.exists(f_mic):
			print "\n    Cannot read %s. Skipping %s ..." % (f_mic, basename)
			continue
		
# 		IF coordinates file exists
		if not os.path.exists(f_info):
			print "\n    Cannot read %s. Skipping %s ..." % (f_info, basename)
			continue
		
# 		IF micrograph is in CTER results
		if options.importctf:
			if basename not in ctfs:
				print "\nMicrograph %s not listed in CTER results, skipping ....\n" % basename
				continue
			else:
				ctf = ctfs[basename]
# 		CHECKS: END

		print "\nProcessing micrograph %s... Path: %s... Coordinates file %s" % (basename, f_mic, f_info)
	
		if options.coords_format.lower() == 'sparx' :
			coords = read_text_row(f_info)
		elif options.coords_format.lower() == 'eman1':
			coords = read_text_row(f_info)
			for i in range(len(coords)):
				coords[i] = [coords[i][0] + coords[i][2]//2  ,coords[i][1] + coords[i][3]//2]
		elif options.coords_format.lower() == 'eman2':
			coords = js_open_dict(f_info)["boxes"]
			for i in range(len(coords)):
				coords[i] = [coords[i][0],coords[i][1]]
		elif options.coords_format.lower() == 'spider':
			coords = read_text_row(f_info)
			for i in range(len(coords)):
				coords[i] = [coords[i][2] ,coords[i][3]]
		else:
			assert(False) # Unreachable code
		
		immic = get_im(f_mic)
		
		resample_ratio = options.input_pixel/new_pixel_size
		fftip(immic)
		if options.limitctf:
			q1, q2 = ctflimit(box_size,ctf[0],ctf[1],ctf[2],new_pixel_size)
			# This is absolute frequency of the CTF limit in the scale of original micrograph
			q1 = (ctf[3] / new_pixel_size) * q1/float(box_size)
			immic = filt_tanl(immic, q1, 0.01)
		immic = fft(filt_gaussh( immic, resample_ratio/box_size ))
		
		if new_pixel_size != options.input_pixel:
			# Resample micrograph, map coordinates, and window segments from resampled micrograph using new coordinates
			# Set ctf along with new pixel size in resampled micrograph
			print_msg('Resample micrograph to pixel size %f and window segments from resampled micrograph\n'%new_pixel_size)
			# after resampling by resample_ratio, new pixel size will be pixel_size/resample_ratio = new_pixel_size
			nx = immic.get_xsize()
			ny = immic.get_ysize()
			immic = resample(immic, resample_ratio)
			if options.importctf: ctf[3] = new_pixel_size
			# New coords
			for i in range(len(coords)):
				coords[i][0] *= resample_ratio
				coords[i][1] *= resample_ratio
		else:
			resample_ratio = 1.0
		
		if options.invert:
			stt = Util.infomask(immic, None, True)
			Util.mul_scalar(immic, -1.0)
			immic += 2*stt[0]
		
		if options.importctf:
			from utilities import generate_ctf
			ctf = generate_ctf(ctf)

		x0 = immic.get_xsize()//2
		y0 = immic.get_ysize()//2

		otcl_images  = "bdb:%s/" % options.outdir + basename + options.outsuffix
		ind = 0
		for i in range(len(coords)):

			x = int(coords[i][0])
			y = int(coords[i][1])
			if( (x-x0-box_half >= 0) and ( x-x0+box_half <= x0 ) and (y-y0-box_half >= 0) and ( y-y0+box_half <= y0 ) ):
				imw = Util.window(immic, box_size, box_size, 1, x-x0, y-y0)
			else:
				continue
			
			imw = ramp(imw)
			stat = Util.infomask( imw, mask, False )
			imw -= stat[0]
			imw /= stat[1]
			
			if options.importctf:
				imw.set_attr("ctf",ctf)
				imw.set_attr("ctf_applied", 0)
			
			imw.set_attr("ptcl_source_coord", [int(round(x/resample_ratio)),int(round(y/resample_ratio))])
			imw.set_attr("pixel_size_orig", options.input_pixel)
			imw.set_attr("ptcl_source_image", f_mic)

			imw.write_image(otcl_images, ind)
			ind += 1

if __name__=='__main__':
	main()
