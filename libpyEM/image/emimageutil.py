#!/usr/bin/env python
#
# Author: Steven Ludtke, 04/10/2003 (sludtke@bcm.edu)
# Copyright (c) 2000-2006 Baylor College of Medicine
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
# Foundation, Inc., 59 Temple Place, Suite 330, Boston MA 02111-1307 USA
#
#

from PyQt4 import QtGui,QtCore
from PyQt4.QtCore import Qt
from math import *
import numpy
from EMAN2 import *
from gui.valslider import ValSlider
from qtgui.emanimationutil import Animator
import weakref
import copy
import sys
import math

class EMTransformPanel:
	def __init__(self,target,parent):
		self.target = weakref.ref(target)
		self.parent = weakref.ref(parent)
		
		self.label_src = QtGui.QLabel(parent)
		self.label_src.setText('Rotation Convention')
		
		self.src = QtGui.QComboBox(parent)
		self.load_src_options(self.src)
		
		self.x_label = QtGui.QLabel()
		self.x_label.setText('x')
		
		self.x_trans = QtGui.QDoubleSpinBox(parent)
		self.x_trans.setMinimum(-10000)
		self.x_trans.setMaximum(10000)
		self.x_trans.setValue(0.0)
	
		self.y_label = QtGui.QLabel()
		self.y_label.setText('y')
		
		self.y_trans = QtGui.QDoubleSpinBox(parent)
		self.y_trans.setMinimum(-10000)
		self.y_trans.setMaximum(10000)
		self.y_trans.setValue(0.0)
		
		self.z_label = QtGui.QLabel()
		self.z_label.setText('z')
		
		self.z_trans = QtGui.QDoubleSpinBox(parent)
		self.z_trans.setMinimum(-10000)
		self.z_trans.setMaximum(10000)
		self.z_trans.setValue(0.0)
		
		self.az = ValSlider(parent,(-360.0,360.0),"az",-1)
		self.az.setObjectName("az")
		self.az.setValue(0.0)
		
		self.alt = ValSlider(parent,(-180.0,180.0),"alt",-1)
		self.alt.setObjectName("alt")
		self.alt.setValue(0.0)
		
		self.phi = ValSlider(parent,(-360.0,360.0),"phi",-1)
		self.phi.setObjectName("phi")
		self.phi.setValue(0.0)
		
		self.scale = ValSlider(parent,(0.01,30.0),"Zoom:")
		self.scale.setObjectName("scale")
		self.scale.setValue(1.0)
		
		self.n3_showing = False
		
		self.current_src = "eman"
		
		QtCore.QObject.connect(self.az, QtCore.SIGNAL("valueChanged"), self.slider_rotate)
		QtCore.QObject.connect(self.alt, QtCore.SIGNAL("valueChanged"), self.slider_rotate)
		QtCore.QObject.connect(self.phi, QtCore.SIGNAL("valueChanged"), self.slider_rotate)
		QtCore.QObject.connect(self.src, QtCore.SIGNAL("currentIndexChanged(QString)"), self.set_src)
		QtCore.QObject.connect(self.scale, QtCore.SIGNAL("valueChanged"), self.target().set_scale)
		QtCore.QObject.connect(self.x_trans, QtCore.SIGNAL("valueChanged(double)"), self.target().set_cam_x)
		QtCore.QObject.connect(self.y_trans, QtCore.SIGNAL("valueChanged(double)"), self.target().set_cam_y)
		QtCore.QObject.connect(self.z_trans, QtCore.SIGNAL("valueChanged(double)"), self.target().set_cam_z)
		
		
	def set_defaults(self):
		self.x_trans.setValue(0.0)
		self.y_trans.setValue(0.0)
		self.z_trans.setValue(0.0)
		self.scale.setValue(1.0)
		self.az.setValue(0.0)
		self.alt.setValue(0.0)
		self.phi.setValue(0.0)
		
	def slider_rotate(self):
		self.target().load_rotation(self.get_current_rotation())
		
	def get_current_rotation(self):
		convention = self.src.currentText()
		rot = {}
		if ( self.current_src == "spin" ):
			rot[self.az.getLabel()] = self.az.getValue()
			
			n1 = self.alt.getValue()
			n2 = self.phi.getValue()
			n3 = self.n3.getValue()
			
			norm = sqrt(n1*n1 + n2*n2 + n3*n3)
			
			n1 /= norm
			n2 /= norm
			n3 /= norm
			
			rot[self.alt.getLabel()] = n1
			rot[self.phi.getLabel()] = n2
			rot[self.n3.getLabel()] = n3
			
		else:
			rot[self.az.getLabel()] = self.az.getValue()
			rot[self.alt.getLabel()] = self.alt.getValue()
			rot[self.phi.getLabel()] = self.phi.getValue()
		
		rot["type"] = self.current_src
		
		return Transform(rot)
	
	def addWidgets(self,target):
		
		target.addWidget(self.scale)
		self.hbl_trans = QtGui.QHBoxLayout()
		self.hbl_trans.setMargin(0)
		self.hbl_trans.setSpacing(6)
		self.hbl_trans.setObjectName("Trans")
		self.hbl_trans.addWidget(self.x_label)
		self.hbl_trans.addWidget(self.x_trans)
		self.hbl_trans.addWidget(self.y_label)
		self.hbl_trans.addWidget(self.y_trans)
		self.hbl_trans.addWidget(self.z_label)
		self.hbl_trans.addWidget(self.z_trans)
		
		target.addLayout(self.hbl_trans)
		
		self.hbl_src = QtGui.QHBoxLayout()
		self.hbl_src.setMargin(0)
		self.hbl_src.setSpacing(6)
		self.hbl_src.setObjectName("hbl")
		self.hbl_src.addWidget(self.label_src)
		self.hbl_src.addWidget(self.src)
		
		
		target.addLayout(self.hbl_src)
		target.addWidget(self.az)
		target.addWidget(self.alt)
		target.addWidget(self.phi)
	
	def set_src(self, val):
		t3d = self.get_current_rotation()
		
		if (self.n3_showing) :
			self.parent().get_transform_layout().removeWidget(self.n3)
			self.n3.deleteLater()
			self.n3_showing = False
			self.az.setRange(-360,360)
			self.alt.setRange(-180,180)
			self.phi.setRange(-360,660)
		
		if ( self.src_map[str(val)] == "spider" ):
			self.az.setLabel('phi')
			self.alt.setLabel('theta')
			self.phi.setLabel('psi')
		elif ( self.src_map[str(val)] == "eman" ):
			self.az.setLabel('az')
			self.alt.setLabel('alt')
			self.phi.setLabel('phi')
		elif ( self.src_map[str(val)] == "imagic"):
			self.az.setLabel('alpha')
			self.alt.setLabel('beta')
			self.phi.setLabel('gamma')
		elif ( self.src_map[str(val)] == "xyz"):
			self.az.setLabel('xtilt')
			self.alt.setLabel('ytilt')
			self.phi.setLabel('ztilt')
		elif ( self.src_map[str(val)] == "mrc" ):
			self.az.setLabel('phi')
			self.alt.setLabel('theta')
			self.phi.setLabel('omega')
		elif ( self.src_map[str(val)] == "spin" ):
			self.az.setLabel('omega')
			self.alt.setRange(-1,1)
			self.phi.setRange(-1,1)
			
			self.alt.setLabel('n1')
			self.phi.setLabel('n2')
			
			self.n3 = ValSlider(self.parent(),(-360.0,360.0),"n3",-1)
			self.n3.setRange(-1,1)
			self.n3.setObjectName("n3")
			self.parent().get_transform_layout().addWidget(self.n3)
			QtCore.QObject.connect(self.n3, QtCore.SIGNAL("valueChanged"), self.slider_rotate)
			self.n3_showing = True
		
		self.current_src = self.src_map[str(val)]
		self.update_rotations(t3d)
	
	def load_src_options(self,widgit):
		self.load_src()
		for i in self.src_strings:
			widgit.addItem(i)
			
	def load_src(self):
		# supported_rot_conventions
		src_flags = []
		src_flags.append("eman")
		src_flags.append("spider")
		src_flags.append("imagic")
		src_flags.append("mrc")
		src_flags.append("spin")
		src_flags.append("xyz")
		
		self.src_strings = []
		self.src_map = {}
		for i in src_flags:
			self.src_strings.append(str(i))
			self.src_map[str(i)] = i
			
	def update_rotations(self,t3d):
		rot = t3d.get_rotation(self.src_map[str(self.src.itemText(self.src.currentIndex()))])
		
		convention = self.src.currentText()
		if ( self.src_map[str(convention)] == "spin" ):
			self.n3.setValue(rot[self.n3.getLabel()],True)
		
		self.az.setValue(rot[self.az.getLabel()],True)
		self.alt.setValue(rot[self.alt.getLabel()],True)
		self.phi.setValue(rot[self.phi.getLabel()],True)
		
	def set_scale(self,newscale):
		self.scale.setValue(newscale)
		
	def set_xy_trans(self, x, y):
		self.x_trans.setValue(x)
		self.y_trans.setValue(y)
		
	def set_xyz_trans(self, x, y,z):
		self.x_trans.setValue(x)
		self.y_trans.setValue(y)
		self.z_trans.setValue(z)
	
import weakref

class EMParentWin(QtGui.QWidget,Animator):
	"""
	This class adds a status bar with a size grip to QGLWidgets on Mac OS X, 
	to provide a visual cue that the window can be resized. This is accomplished
	by placing a QGLWidget and a QStatusBar onto a QWidget. The EMGLWidget 
	class hides the fact that this workaround is required.
	"""
	
	def __init__(self,enable_timer=False):
		"""
		@param child: the central GL display widget
		@type child: EMGLWidget
		@param enable_timer: not used... historical purposes???
		"""
		#TODO: figure out why the enable_timer parameter isn't being used
		QtGui.QWidget.__init__(self,None)
		Animator.__init__(self)


		self.setMaximumSize(8000,8000)
		self.hbl = QtGui.QVBoxLayout(self)
		
		self.hbl.setSpacing(0)
		if get_platform() == "Darwin": # because OpenGL widgets in Qt don't leave room in the bottom right hand corner for the resize tool
			self.status = QtGui.QStatusBar()
			self.status.setSizeGripEnabled(True)
			self.hbl.addWidget(self.status,0)
			self.margin = 0
		else:
			self.margin = 5
		self.hbl.setMargin(self.margin)
		
		
	def __del__(self):
		pass
	
	def setup(self,child):
		"""__init__ has to be called before the widget is fully ready for display, so this completes the setup process"""

		self.resize(640,640)
		self.child = weakref.ref(child) # Either EMGLWidget.parent_widget or EMParentWin.child must be a weakref for garbage collection purposes.
		self.hbl.addWidget(self.child(),100)
#		self.resize(self.child().width(),self.child().height())
	
	def get_margin(self):
		return 50
	

	def closeEvent(self, e):
		try:
			self.child().closeEvent(e)
			#self.child.inspector.close()
		except: pass
		QtGui.QWidget.closeEvent(self,e)
		
#	def resizeEvent(self,event):
#		self.child().resizeEvent(event)
	
	def get_qt_widget(self):
		return self.child()
	
	def update(self):
		self.child().updateGL()
		
	def updateGL(self):
		self.child().updateGL()
	
	def keyPressEvent(self,event):
		self.child().keyPressEvent(event)

	#def mousePressEvent(self, event):
		#print "mouse",event
		#self.child().mousePressEvent(event)


	#def width(self):
		##print "asked for width!"
		#return self.child.width()
	
	#def height(self):
		##print "asked for height!"
		#return self.child.height()
		
	def initGL(self):
		self.child().glInit()