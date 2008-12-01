#!/usr/bin/env python

#
# Author: David Woolford, 10/19/2007 (woolford@bcm.edu)
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


from EMAN2 import *
from optparse import OptionParser
from math import *
import os
import sys

def main():
	progname = os.path.basename(sys.argv[0])
	usage = """%prog [options] 
	EMAN2 iterative single particle reconstruction"""
	parser = OptionParser(usage=usage,version=EMANVERSION)
		
	#options associated with e2refine.py
	parser.add_option("--iter", dest = "iter", type = "int", default=0, help = "The total number of refinement iterations to perform")
	parser.add_option("--check", "-c", dest="check", default=False, action="store_true",help="Checks the contents of the current directory to verify that e2refine.py command will work - checks for the existence of the necessary starting files and checks their dimensions. Performs no work ")
	parser.add_option("--verbose","-v", dest="verbose", default=False, action="store_true",help="Toggle verbose mode - prints extra infromation to the command line while executing")
	parser.add_option("--nomirror", dest="nomirror", default=False, action="store_true",help="Turn projection over the mirror portion of the asymmetric unit off")
	parser.add_option("--input", dest="input", default=None,type="string", help="The name of the image containing the particle data")
	parser.add_option("--model", dest="model", default="threed.0a.mrc", help="The name 3D image that will seed the refinement")
	parser.add_option("--usefilt", dest="usefilt", default=None, help="Specify a particle data file that has been low pass or Wiener filtered. Has a one to one correspondence with your particle data. If specified will be used in projection matching routines, and elsewhere.")
	parser.add_option("--path", default=None, help="The name of a directory where results are placed. If unspecified will generate one automatically of type refine_??.")

	# options associated with e2project3d.py
	parser.add_option("--sym", dest = "sym", help = "Specify symmetry - choices are: c<n>, d<n>, h<n>, tet, oct, icos")
	parser.add_option("--projector", dest = "projector", default = "standard",help = "Projector to use")
	parser.add_option("--orientgen", type = "string",help = "The orientation generation argument for e2project3d.py")
		
	# options associated with e2simmx.py
	parser.add_option("--simalign",type="string",help="The name of an 'aligner' to use prior to comparing the images", default="rotate_translate_flip")
	parser.add_option("--simaligncmp",type="string",help="Name of the aligner along with its construction arguments",default="dot")
	parser.add_option("--simralign",type="string",help="The name and parameters of the second stage aligner which refines the results of the first alignment", default=None)
	parser.add_option("--simraligncmp",type="string",help="The name and parameters of the comparitor used by the second stage aligner. Default is dot.",default="dot")
	parser.add_option("--simcmp",type="string",help="The name of a 'cmp' to be used in comparing the aligned images", default="dot:normalize=1")
	parser.add_option("--shrink", dest="shrink", type = "int", default=None, help="Optionally shrink the input particles by an integer amount prior to computing similarity scores. For speed purposes.")
	
	# options associated with e2classify.py
	parser.add_option("--sep", type="int", help="The number of classes a particle can contribute towards (default is 2)", default=2)
	
	# options associated with e2classaverage.py
	parser.add_option("--classkeep",type="float",help="The fraction of particles to keep in each class, based on the similarity score generated by the --cmp argument.")
	parser.add_option("--classkeepsig", default=False, action="store_true", help="Change the keep (\'--keep\') criterion from fraction-based to sigma-based.")
	parser.add_option("--classiter", type="int", help="The number of iterations to perform. Default is 1.", default=3)
	parser.add_option("--classalign",type="string",help="If doing more than one iteration, this is the name and parameters of the 'aligner' used to align particles to the previous class average.", default="rotate_translate")
	parser.add_option("--classaligncmp",type="string",help="This is the name and parameters of the comparitor used by the fist stage aligner  Default is dot.",default="phase")
	parser.add_option("--classralign",type="string",help="The second stage aligner which refines the results of the first alignment in class averaging. Default is None.", default=None)
	parser.add_option("--classraligncmp",type="string",help="The comparitor used by the second stage aligner in class averageing. Default is dot:normalize=1.",default="dot:normalize=1")
	parser.add_option("--classaverager",type="string",help="The averager used to generate the class averages. Default is \'image\'.",default="image")
	parser.add_option("--classcmp",type="string",help="The name and parameters of the comparitor used to generate similarity scores, when class averaging. Default is \'dot:normalize=1\'", default="dot:normalize=1")
	parser.add_option("--classnormproc",type="string",default="normalize.edgemean",help="Normalization applied during class averaging")
	
	
	#options associated with e2make3d.py
	parser.add_option("--pad", type=int, dest="pad", help="To reduce Fourier artifacts, the model is typically padded by ~25% - only applies to Fourier reconstruction", default=0)
	parser.add_option("--recon", dest="recon", default="fourier", help="Reconstructor to use see e2help.py reconstructors -v")
	parser.add_option("--m3dkeep", type=float, help="The percentage of slices to keep in e2make3d.py")
	parser.add_option("--m3dkeepsig", default=False, action="store_true", help="The standard deviation alternative to the --m3dkeep argument")
	parser.add_option("--m3diter", type=int, default=4, help="The number of times the 3D reconstruction should be iterated")
	parser.add_option("--m3dpreprocess", type="string", default="normalize.edgemean", help="Normalization processor applied before 3D reconstruction")

	#lowmem!
	parser.add_option("--lowmem", default=False, action="store_true",help="Make limited use of memory when possible - useful on lower end machines")
	
	(options, args) = parser.parse_args()
	
	error = False
	if check(options,True) == True : 
		error = True
	if check_projection_args(options) == True : 
		error = True
	if check_simmx_args(options,True) == True :
		error = True
	if check_classify_args(options,True) == True :
		error = True
	if check_classaverage_args(options,True) == True :
		error = True
	if check_make3d_args(options,True) == True:
		error = True
	
	if error:
		print "Error encountered while checking command line, bailing"
		exit_refine(1,logid)
	
	if (options.check):
		exit_refine(0,logid)
	
	logid=E2init(sys.argv)
	
	if options.path == None:
		options.path = numbered_path("refine",True)
		
	#check_projection_args(options, parser)
	
	# this is the main refinement loop
	
	progress = 0.0
	total_procs = 5*options.iter
	for i in range(0,options.iter) :
		
		number_options_file(i,"projections",options,"projfile")
		if ( os.system(get_projection_cmd(options)) != 0 ):
			print "Failed to execute %s" %get_projection_cmd(options)
			exit_refine(1,logid)
		progress += 1.0
		E2progress(logid,progress/total_procs)
		
		number_options_file(i,"simmx",options,"simmxfile")
		if ( os.system(get_simmx_cmd(options)) != 0 ):
			print "Failed to execute %s" %get_simmx_cmd(options)
			exit_refine(1,logid)
		progress += 1.0
		E2progress(logid,progress/total_procs)
			
		number_options_file(i,"classify",options,"classifyfile")
		if ( os.system(get_classify_cmd(options)) != 0 ):
			print "Failed to execute %s" %get_classify_cmd(options)
			exit_refine(1,logid)
		progress += 1.0
		E2progress(logid,progress/total_procs)
			
		number_options_file(i,"classes",options,"cafile")
		number_options_file(i,"cls_result",options,"resultfile")
		if ( os.system(get_classaverage_cmd(options)) != 0 ):
			print "Failed to execute %s" %get_classaverage_cmd(options)
			exit_refine(1,logid)
		progress += 1.0
		E2progress(logid,progress/total_procs)
			
		
		number_options_file(i,"threed",options,"model")
		if ( os.system(get_make3d_cmd(options)) != 0 ):
			print "Failed to execute %s" %get_make3d_cmd(options)
			exit_refine(1,logid)
		progress += 1.0
		E2progress(logid,progress/total_procs)
	E2end(logid)

def number_options_file(i,file,options,attr):
	name = "bdb:"+options.path+"#" + file+"_"
	if i < 10:
		name += "0"
	
	name += str(i)
	setattr(options,attr,name)
	
def exit_refine(n,logid):
	E2end(logid)
	exit(n)

def get_make3d_cmd(options,check=False,nofilecheck=False):
	e2make3dcmd = "e2make3d.py %s --sym=%s --iter=%d -f" %(options.cafile,options.sym,options.m3diter)
	
	e2make3dcmd += " --recon=%s --out=%s" %(options.recon,options.model)

	if str(options.m3dpreprocess) != "None":
		e2make3dcmd += " --preprocess=%s" %options.m3dpreprocess

	if (options.m3dkeepsig):
		e2make3dcmd += " --keepsig=%f" %options.m3dkeepsig
	elif (options.m3dkeep):
		e2make3dcmd += " --keep=%f" %options.m3dkeep
	
	if (options.lowmem): e2make3dcmd += " --lowmem"

	if (options.pad != 0):
		e2make3dcmd += " --pad=%d" %options.pad
		
	if (options.verbose):
		e2make3dcmd += " -v"
	
	if ( check ):
		e2make3dcmd += " --check"	
			
	if ( nofilecheck ):
		e2make3dcmd += " --nofilecheck"
	
	return e2make3dcmd

def check_make3d_args(options, nofilecheck=False):
	
	cmd = get_make3d_cmd(options,True,nofilecheck)
	print ""
	print "#### Test executing make3d command: %s" %cmd
	return ( os.system(cmd) != 0)

def get_classaverage_cmd(options,check=False,nofilecheck=False):
	
	e2cacmd = "e2classaverage.py %s %s %s" %(options.input,options.classifyfile,options.cafile)
	
	e2cacmd += " --ref=%s --iter=%d -f --result=%s --normproc=%s" %(options.projfile,options.classiter,options.resultfile,options.classnormproc)
	
	
	if (options.classkeep):
		e2cacmd += " --keep=%f" %options.classkeep
	if (options.classkeepsig):
		e2cacmd += " --keepsig"
	
	if (options.classiter > 1 ):
		e2cacmd += " --cmp=%s --align=%s --aligncmp=%s" %(options.classcmp,options.classalign,options.classaligncmp)

		if (options.classralign != None):
			e2cacmd += " --ralign=%s --raligncmp=%s" %(options.classralign,options.classraligncmp)
	
	if options.usefilt != None:
		e2cacmd += " --usefilt=%s" %options.usefilt
	
	if (options.verbose):
		e2cacmd += " -v"
		
	if (options.lowmem): e2cacmd += " --lowmem"
	
	if ( check ):
		e2cacmd += " --check"	
			
	if ( nofilecheck ):
		e2cacmd += " --nofilecheck"
	
	return e2cacmd

def check_classaverage_args(options, nofilecheck=False):
	if not hasattr(options,"cafile"): setattr(options,"cafile","dummy")
	if not hasattr(options,"resultfile"): setattr(options,"resultfile","dummy")
	cmd = get_classaverage_cmd(options,True,nofilecheck)
	print ""
	print "#### Test executing classaverage command: %s" %cmd
	return ( os.system(cmd) != 0)

def get_classify_cmd(options,check=False,nofilecheck=False):
	e2classifycmd = "e2classify.py %s %s --sep=%d -f" %(options.simmxfile,options.classifyfile,options.sep)
	
	if (options.verbose):
		e2classifycmd += " -v"
	
	if ( check ):
		e2classifycmd += " --check"	
			
	if ( nofilecheck ):
		e2classifycmd += " --nofilecheck"
	
	return e2classifycmd

def check_classify_args(options, nofilecheck=False):
	if not hasattr(options,"classifyfile"): setattr(options,"classifyfile","dummy")
	cmd = get_classify_cmd(options,True,nofilecheck)
	print ""
	print "#### Test executing classify command: %s" %cmd
	return ( os.system(cmd) != 0)

def get_simmx_cmd(options,check=False,nofilecheck=False):
	
	if options.usefilt != None:
		image = options.usefilt
	else:
		image = options.input
	
	e2simmxcmd = "e2simmx.py %s %s %s -f --saveali --cmp=%s --align=%s --aligncmp=%s"  %(options.projfile, image,options.simmxfile,options.simcmp,options.simalign,options.simaligncmp)
	
	if ( options.simralign != None ):
		e2simmxcmd += " --ralign=%s --raligncmp=%s" %(options.simralign,options.simraligncmp)
	
	if (options.verbose):
		e2simmxcmd += " -v"
	
	if (options.lowmem): e2simmxcmd += " --lowmem"	
	
	if (options.shrink):
		e2simmxcmd += " --shrink="+str(options.shrink)
		
	if ( check ):
		e2simmxcmd += " --check"	
			
	if ( nofilecheck ):
		e2simmxcmd += " --nofilecheck"
		
	
	return e2simmxcmd

def check_simmx_args(options, nofilecheck=False):
	if not hasattr(options,"simmxfile"): setattr(options,"simmxfile","dummy")
	cmd = get_simmx_cmd(options,True,nofilecheck)
	print ""
	print "#### Test executing simmx command: %s" %cmd
	return ( os.system(cmd) != 0)

def get_projection_cmd(options,check=False):
	
	e2projcmd = "e2project3d.py %s -f --sym=%s --projector=%s --out=%s --orientgen=%s" %(options.model,options.sym,options.projector,options.projfile,options.orientgen)
		
	if ( check ):
		e2projcmd += " --check"	
		
	if (options.verbose):
		e2projcmd += " -v"
	
	return e2projcmd
	
def check_projection_args(options):
	if not hasattr(options,"projfile"): setattr(options,"projfile","dummy")
	cmd = get_projection_cmd(options,True)
	print ""
	print "#### Test executing projection command: %s" %cmd
	return ( os.system(cmd) != 0 )

def check(options,verbose=False):
	if (verbose):
		print ""
		print "#### Testing directory contents and command line arguments for e2refine.py"
	
	error = False
	if options.input == None or not file_exists(options.input):
		print "Error: failed to find input file %s" %options.input
		error = True
	
	if options.usefilt != None:
		if not file_exists(options.usefilt):
			print "Error: failed to find usefilt file %s" %options.usefilt
			error = True
		n1 = EMUtil.get_image_count(options.usefilt)
		n2 = EMUtil.get_image_count(options.input)
		if n1 != n2:
			print "Error, the number of images in the starting particle set:",n2,"does not match the number in the usefilt set:",n1
			error = True
		read_header_only=True
		img1 = EMData()
		img1.read_image(options.input,0,read_header_only)
		img2 = EMData()
		img2.read_image(options.usefilt,0,read_header_only)
		
		nx1 = img1.get_attr("nx") 
		nx2 = img2.get_attr("nx") 
		
		ny1 = img1.get_attr("ny") 
		ny2 = img2.get_attr("ny") 
		
		if nx1 != nx2 or ny1 != ny2:
			error = True
			if verbose: print "Error, the dimensions of particle data (%i x %i) and the usefilt data (%i x %i) do not match" %(nx1,ny1,nx2,ny2)
	
	if not file_exists(options.model):
		print "Error: 3D image %s does not exist" %options.model
		error = True
		
	if not options.iter:
		print "Error: you must specify the --it argument"
		error = True
		
	if ( file_exists(options.model) and options.input != None and file_exists(options.input)):
		(xsize, ysize ) = gimme_image_dimensions2D(options.input);
		(xsize3d,ysize3d,zsize3d) = gimme_image_dimensions3D(options.model)
		
		if (verbose):
			print "%s contains %d images of dimensions %dx%d" %(options.input,EMUtil.get_image_count(options.input),xsize,ysize)
			print "%s has dimensions %dx%dx%d" %(options.model,xsize3d,ysize3d,zsize3d)
		
		if ( xsize != ysize ):
			if ( ysize == zsize3d and xsize == ysize3d and ysize3D == xsize3d ):
				print "Error: it appears as though you are trying to do helical reconstruction. This is not supported"
				error = True
			else:
				print "Error: images dimensions (%d x %d) of %s are not identical. This mode of operation is not supported" %(xsize,ysize,options.input)
				error = True
		
		if ( xsize3d != ysize3d or ysize3d != zsize3d ):
			print "Error: image dimensions (%dx%dx%d) of %s are not equal" %(xsize3d,ysize3d,zsize3d,options.model)
			error = True
			
		if ( xsize3d != xsize ) :
			print "Error: the dimensions of %s (%d) do not match the dimension of %s (%d)" %(options.input,xsize,options.model,xsize3d)
			error = True
			
	if options.path != None:
		if not os.path.exists(options.path):
			print "Error: the path %s does not exist" %options.path
			error = True
	
	if (verbose):
		if (error):
			s = "FAILED"
		else:
			s = "PASSED"
			
		print "e2refine.py test.... %s" %s

	return error == True
	
if __name__ == "__main__":
    main()
