#!/usr/bin/env python

#
# Author: David Woolford, 5/27/2008 (woolford@bcm.edu)
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

# e2stacksort.py  01/03/07  Steven Ludtke
# This program will sort a stack of images based on some similarity criterion


from EMAN2 import *
from optparse import OptionParser
from math import *
import os
import sys
import copy

def main():
	progname = os.path.basename(sys.argv[0])
	usage = """%prog [options]

	This program traces the orientation of particles through multiple iterations.
"""

	parser = OptionParser(usage=usage,version=EMANVERSION)

	parser.add_option("--sym",type="string",help="The symmetry to be used to nearness testing and, if it is specified, reduction", default="c1")
	parser.add_option("--verbose", "-v", dest="verbose", action="store", metavar="n", type="int", default=0, help="verbose level [0-9], higner number means higher level of verboseness")

	print "WARNING: this program may currently be broken. It is on a TODO list to fix..."
	
	(options, args) = parser.parse_args()
	
	if options.jwd and options.eman1data:
		parser.error("The jwd and eman1data options are mutually exclusive")
	
	if options.dtheta <= 0:
		print "error, you must specify a positive, non zero dtheta"
		exit(1)
		
	orienttracedata = []
	classtracedata = []
	if options.jwd != None:
		filenames = options.jwd.split(",")
		if len(filenames) <= 1:
			parser.error("You must supply atleast two filenames when using the --jwd argument")
		
		jwdata = JiangWenLstFile(filenames)
		orienttracedata = jwdata.euler_data
		classtracedata = jwdata.class_dummy_data
		options.convergence = len(filenames)
		dd=jwdata
		
	elif options.eman1data != None:
		if options.convergence <= 1:
			print "error, you must specify a positive convergence value greater than 1"
			exit(1)
		done = False
		s = str(options.eman1data)
		filenames = []
		while not done:
			idx =  s.find(',')
			if idx == -1:
				filenames.append(s)
				done = True
			else:
				filenames.append(s[0:idx])
				s = s[(idx+1):]
				#exit(1)		
		eman1data = Eman1Data(filenames)
		orienttracedata = eman1data.orienttracedata
		classtracedata = eman1data.classtracedata
		dd=eman1data
#		print "parsing data"
#		
#		for filename in filenames:
#			parsedata(filename,orienttracedata,classtracedata)
#			print "there is a total of",len(orienttracedata),"particles"
#			#print orienttracedata,classtracedata
			
		
		if options.convergence > len(classtracedata[0]):
			print "error, convergence must be less than or equal to the total iterations in the particle trace data"
			exit(1)
	else: 
		print "error, you must specifiy alteast eman1data or jwd"
		sys.exit(1)
		
	print "Detecting convergence without reduction"
	detect_convergence(options.convergence,options.dtheta,orienttracedata,classtracedata,dd)
	dd.finalize()
	
	if options.sym != "c1":
		orienttracedata = []
		classtracedata = []
		if options.eman1data != None:
			eman1data2 = Eman1Data(filenames,"reduced_em1d_")
			orienttracedata = eman1data2.orienttracedata
			classtracedata = eman1data2.classtracedata
			dd = eman1data2
		else:
			jwdata3 = JiangWenLstFile(filenames,"reduced_jwd_")
			orienttracedata = jwdata3.euler_data
			classtracedata = jwdata3.class_dummy_data
			dd = jwdata3
		print "you specified a symmetry, now I am reducing"
		sym = Symmetries.get(options.sym)
		reduce(orienttracedata,sym)
		
		print "Detecting convergence of reduced data",options.dtheta
		detect_convergence(options.convergence,options.dtheta,orienttracedata,classtracedata,dd)
		dd.finalize()
			
	E2n=E2init(sys.argv)
	E2end(E2n)


def detect_convergence(converge,dtheta,data,classdata,dd,optional=None):
	
	m = converge
	n = 0
	i = 0
	## a temporary hack, this value should be known
	while n <= 0 and i < len(data):
		n = len(data[i])
		i += 1
		
	if n == 0: return
	
	
	limit = (n-m)+1
	
	report_percentages = 20
	
	for number,d in enumerate(data):
		for i in range(report_percentages):
			if number == len(data)/(i+1):
				percent = 100.0/report_percentages*(report_percentages-i)
				print percent,"% "
				break
		if len(d) == 0:
			continue
		solution = []
		for i in range(0,limit):
			seed = d[i]
			soln_idx = []
			angle_solns = []
			angle_sum = 0
			while len(soln_idx) != (m-1):
				closest = -1
				idx = -1
				for j in range(i+1,n):
					if j in soln_idx:
						continue
					o2 = d[j]
					angle = angular_deviation_from_orient(seed,o2)
					if closest == -1 or angle < closest:
						closest = angle
						idx = j
				
				
				seed = d[idx]
				soln_idx.append(idx)
				#print closest
				angle_sum += closest
				angle_solns.append(closest)
			
			# determine the average angular separation
			angle_sum /= (m-1)
			if angle_sum <= dtheta:
				dd. write_good_output(i,idx,soln_idx,number,angle_solns,optional)
#				good.write(str(number) + "\tstart.hed\n")
#				
#				good_data.write(str(number) + '. ********\n')
#				if optional == None:
#					good_data.write(str(classdata[number][i][0]) +" -> "+str(classdata[number][i][1])+ " (" + str(d[i][0])+","+str(d[i][1])+","+str(d[i][2])+")\n")
#					for k,idx in enumerate(soln_idx):
#						good_data.write(str(classdata[number][idx][0]) + " -> "+str(classdata[number][idx][1])+ " (" + str(d[idx][0])+","+str(d[idx][1])+","+str(d[idx][2])+")\t"+str(angle_solns[k])+"\n")
#			 	else:
#				 	c = optional[number]
#		   	   	   	good_data.write(str(classdata[number][i][0]) +" -> "+str(classdata[number][i][1])+ " (" + str(c[i][0])+","+str(c[i][1])+","+str(c[i][2])+")\n")
#					for k,idx in enumerate(soln_idx):
#						good_data.write(str(classdata[number][idx][0]) + " -> "+str(classdata[number][idx][1])+ " (" + str(c[idx][0])+","+str(c[idx][1])+","+str(c[idx][2])+")\t"+str(angle_solns[k])+"\n")

			else:
				dd.write_bad_output(i,idx,soln_idx,number,angle_solns,optional)
	print "100%.... done"

def angular_deviation_from_orient(o1,o2):
	t1 = Transform({"type":"eman","az":o1[1],"alt":o1[0],"phi":o1[2]})
	t2 = Transform({"type":"eman","az":o2[1],"alt":o2[0],"phi":o2[2]})
	#t2 = Transform(o2[1],o2[0],o2[2])
	return angular_deviation(t1,t2)

def angular_deviation(t1,t2):

	v1 = Vec3f(0,0,1)*t1
	v2 = Vec3f(0,0,1)*t2
	t = v2.dot(v1)
	#print t
	if t > 1: 
		if t > 1.1:
			print "error, the precision is a problem, are things normalized?"
			exit(1)
		t = 1
	if t < -1:
		if t < -1.1:
			print "error, the precision is a problem, are things normalized?"
			exit(1)
		t = -1
				
	angle = acos(t)*180/pi
	
	return angle

def reduce(orienttracedata,sym):
	nn = 0
	for particle in orienttracedata:
		if len(particle) == 0:	continue
		nn += 1
		for orient in particle:
			t = Transform({"type":"eman","az":orient[1],"alt":orient[0],"phi":orient[2]})
			t = sym.reduce(t,0)
			d = t.get_rotation("eman")
			orient[1] = d["az"]
			orient[0] = d["alt"]
			orient[2] = d["phi"]
	
	print "reduced a total of",nn, "orientations"
	touching = sym.get_touching_au_transforms(False)
	
	for particle in orienttracedata:
		if len(particle) == 0:	continue
		n = len(particle)
		for i in range(1,n):
			o1 = particle[i-1]
			o2 = particle[i]
			t1 = Transform({"type":"eman","az":o1[1],"alt":o1[0],"phi":o1[2]})
			t2 = Transform({"type":"eman","az":o2[1],"alt":o2[0],"phi":o2[2]})
		
			angle = angular_deviation(t1,t2)
			
			for t in touching:
				t2 = Transform({"type":"eman","az":o2[1],"alt":o2[0],"phi":o2[2]})*t
				#t2 = Transform3D(o2[1],o2[0],o2[2])*t
				
				tmp = angular_deviation(t1,t2)
				
				if tmp < angle:
					angle = tmp
					
					d = t2.get_rotation("eman")
					particle[i][1] = d["az"]
					particle[i][0] = d["alt"]
					particle[i][2] = d["phi"]
	
				
def calc_angular_deviation(orienttracedata):
	
	data = []
	
	for particle in orienttracedata:
		n = len(particle)
		if n <= 1:
			data.append(0)
			continue
		angle = 0
		for i in range(0,n-1):
			o1 = particle[i]
			o2 = particle[i+1]
			t1 = Transform({"type":"eman","az":o1[1],"alt":o1[0],"phi":o1[2]})
			t2 = Transform({"type":"eman","az":o2[1],"alt":o2[0],"phi":o2[2]})
			angle += angular_deviation(t1,t2)

		angle /= (n-1)
		data.append(angle)

	return data

def parsedata(filename,orienttracedata,classtracedata):
	try:
		f=file(filename,'r')
	except:
		print "couldn't read",filename
		return 0
	lines=f.readlines()

	for line in lines:
		s = str.split(str.strip(line))
		if s[1] == '********':
			fs_idx = s[0].find('.') # fullstop idx
			if fs_idx == -1:
				print "error, the format of the input file is unexpected, couldn't find a number followed by a fullstop in",s[0]
			else:
				idx = s[0][0:fs_idx]
				n = int(idx)+1
				if len(orienttracedata) < n:
					for i in range(len(orienttracedata),n):
						orienttracedata.append([])
				if len(classtracedata) < n:
					for i in range(len(classtracedata),n):
						classtracedata.append([])
		elif s[1] == '->':
			idx = str.find(s[3],',')
			alt = float(s[3][1:idx])
			az = float(s[3][idx+1:len(s[3])-1])
			orienttracedata[n-1].append([alt,az,0])
			cls = int(s[2])
			it = int(s[0])
			classtracedata[n-1].append([it,cls])

class TraceOuputMixin:
	'''
	Mixin encapsulates output files
	'''
	def __init__(self,output_tag):
		self.good_ofiles = PtclTraceOutput(output_tag)
		self.bad_ofiles = PtclTraceOutput("bad_"+output_tag)
		
		self.good_lst = self.good_ofiles.get_lst_file()
		self.good_data = self.good_ofiles.get_ptcl_data_file()
		self.good_ang_data = self.good_ofiles.get_ang_data_file()
		
		self.bad_lst = self.bad_ofiles.get_lst_file()
		self.bad_data = self.bad_ofiles.get_ptcl_data_file()
		self.bad_ang_data = self.bad_ofiles.get_ang_data_file()
		
		self.num_good_written = 0
		self.num_bad_written = 0
		
	def finalize(self):
		self.good_ofiles.finalize()
		self.bad_ofiles.finalize()
		
class Eman1Data(TraceOuputMixin):
	
	def __init__(self,filenames,output_tag="em1d_"):
		TraceOuputMixin.__init__(self,output_tag)
		self.filenames=filenames
		self.parse_data(filenames)
		
	def parse_data(self,filenames):
		self.orienttracedata = []
		self.classtracedata = []
		for filename in filenames:
			parsedata(filename,self.orienttracedata,self.classtracedata)
			
	def write_good_output(self,i,idx,soln_idx,number,angle_solns,optional=None):
		self.__write_output(i,idx,soln_idx,number,angle_solns,optional,True)
	
	def write_bad_output(self,i,idx,soln_idx,number,angle_solns,optional=None):
		self.__write_output(i,idx,soln_idx,number,angle_solns,optional,False)
		
	def __write_output(self,i,idx,soln_idx,number,angle_solns,optional=None,good=True):
		if good:
			lst = self.good_lst
			good_data = self.good_data
			ang_data = self.good_ang_data
			n = self.num_good_written
		else:
			lst = self.bad_lst
			good_data = self.bad_data
			ang_data = self.bad_ang_data
			n = self.num_bad_written
		
		classdata = self.classtracedata
		d = self.orienttracedata[number]
		
		lst.write(str(number) + "\tstart.hed\n")
				
		good_data.write(str(number) + '. ********\n')
		if optional == None:
			good_data.write(str(classdata[number][i][0]) +" -> "+str(classdata[number][i][1])+ " (" + str(d[i][0])+","+str(d[i][1])+","+str(d[i][2])+")\n")
			for k,idx in enumerate(soln_idx):
				good_data.write(str(classdata[number][idx][0]) + " -> "+str(classdata[number][idx][1])+ " (" + str(d[idx][0])+","+str(d[idx][1])+","+str(d[idx][2])+")\t"+str(angle_solns[k])+"\n")
	 	else:
		 	c = optional[number]
   	   	   	good_data.write(str(classdata[number][i][0]) +" -> "+str(classdata[number][i][1])+ " (" + str(c[i][0])+","+str(c[i][1])+","+str(c[i][2])+")\n")
			for k,idx in enumerate(soln_idx):
				good_data.write(str(classdata[number][idx][0]) + " -> "+str(classdata[number][idx][1])+ " (" + str(c[idx][0])+","+str(c[idx][1])+","+str(c[idx][2])+")\t"+str(angle_solns[k])+"\n")

		ang_data.write(str(n)+"\t"+str(angle_solns[k])+"\n")
		
		if good: self.num_good_written += 1
		else:self.num_bad_written += 1

class PtclTraceOutput:
	'''
	An encapsulation of the output files generated by
	'''
	def __init__(self,output_tag="ptcl_trace_output"):
		self.__lst=open(output_tag+'.lst','w') # used to be callled "good"
		self.__lst.write("#LST\n")
		self.__data = open(output_tag+'trace_data.txt','w') # used to be called "good_data"
		self.__data.write("#e2ptcltrace.py data file\n")
		self.__angle_data = open(output_tag+'angle_data.txt','w')
		self.__angle_data.write("#e2ptcltrace.py angular data file\n")
	
	def get_lst_file(self): return self.__lst
	def get_ptcl_data_file(self): return self.__data
	def get_ang_data_file(self): return self.__angle_data
	
	def finalize(self):
		self.__lst.close()
		self.__data.close()
		self.__angle_data.close()

class JiangWenLstFile(TraceOuputMixin):
	'''
	File parsing based on Rui Zhang's code
	'''
	def __init__(self,filenames,output_tag="jwd_"):
		TraceOuputMixin.__init__(self,output_tag)
		self.filenames = filenames
		self.parse_data(self.filenames)
		
	def parse_data(self,filenames):
		
		self.data = []
		
		for name in filenames:
			table = {}
			file = open(name)
			lines = file.readlines()
			for i in lines:
				if i[0] == "#": continue # will ignore the "#LST" and any other line that starts with #
				tmp=i.split()
				index='%s\t%s'%(tmp[0],tmp[1])
				parm1=[float(tmp[2]),float(tmp[3]),float(tmp[4]),float(tmp[5]),float(tmp[6])]
				table[index]=parm1
			
			self.data.append(table)
		
		common_keys = []
		 
		for i in range(len(filenames)):
			if i == 0:
				common_keys = set(self.data[0].keys())
			else:
				common_keys = common_keys & set(self.data[i].keys())
		
		self.key_list = list(common_keys)
		self.euler_data = []
		self.trans_data = []
		self.class_dummy_data = []
		for k in self.key_list:
			orient_data = []
			trans_data = []
			dummy_data = []
			for i in range(len(filenames)):
				[alt,az,phi,dx,dy]=self.data[i][k]
				orient_data.append([alt,az,phi])
				trans_data.append([dx,dy])
				dummy_data.append([0,0])
			self.euler_data.append(orient_data)
			self.trans_data.append(trans_data)
			self.class_dummy_data.append(dummy_data)
			
	def write_lst_idx_entry(self,number,file):
		file.write(self.key_list[number]+"\n")

	def write_good_output(self,i,idx,soln_idx,number,angle_solns,optional=None):
		self.__write_output(i,idx,soln_idx,number,angle_solns,optional,True)
	
	def write_bad_output(self,i,idx,soln_idx,number,angle_solns,optional=None):
		self.__write_output(i,idx,soln_idx,number,angle_solns,optional,False)
		
	def __write_output(self,i,idx,soln_idx,number,angle_solns,optional=None,good=True):
		if good:
			lst = self.good_lst
			good_data = self.good_data
			ang_data = self.good_ang_data
			n = self.num_good_written
		else:
			lst = self.bad_lst
			good_data = self.bad_data
			ang_data = self.bad_ang_data
			n = self.num_bad_written
			
		classdata = self.class_dummy_data
		d = self.euler_data[number]
		
		s = self.data[0][self.key_list[number]]
		ss ='%-8.3f%-8.3f%-8.3f%-8.3f%-8.3f'%(s[0],s[1],s[2],s[3],s[4])
		
		lst.write(self.key_list[number]+"\t"+ss+"\n")
				
		good_data.write(str(number) + '. ******** ' + self.key_list[number] + '\n')
		if optional == None:
			good_data.write(str(classdata[number][i][0]) +" -> "+str(classdata[number][i][1])+ " (" + str(d[i][0])+","+str(d[i][1])+","+str(d[i][2])+")\n")
			for k,idx in enumerate(soln_idx):
				good_data.write(str(classdata[number][idx][0]) + " -> "+str(classdata[number][idx][1])+ " (" + str(d[idx][0])+","+str(d[idx][1])+","+str(d[idx][2])+")\t"+str(angle_solns[k])+"\n")
	 	else:
		 	c = optional[number]
   	   	   	good_data.write(str(classdata[number][i][0]) +" -> "+str(classdata[number][i][1])+ " (" + str(c[i][0])+","+str(c[i][1])+","+str(c[i][2])+")\n")
			for k,idx in enumerate(soln_idx):
				good_data.write(str(classdata[number][idx][0]) + " -> "+str(classdata[number][idx][1])+ " (" + str(c[idx][0])+","+str(c[idx][1])+","+str(c[idx][2])+")\t"+str(angle_solns[k])+"\n")
			
		ang_data.write(str(n)+"\t"+str(angle_solns[k])+"\n")
		
		if good: self.num_good_written += 1
		else:self.num_bad_written += 1
		
if __name__ == "__main__":
    main()
