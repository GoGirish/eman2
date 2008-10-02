#!/usr/bin/env python

#
# Author: Steven Ludtke, 04/10/2003 (sludtke@bcm.edu)
# and David Woolford 10/26/2007 (woolford@bcm.edu)
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



from PyQt4 import QtCore, QtGui, QtOpenGL
from PyQt4.QtCore import Qt
from OpenGL import GL,GLU,GLUT
from OpenGL.GL import *
from OpenGL.GLU import *
from valslider import ValSlider
from math import *
from EMAN2 import *
import sys
import numpy
from weakref import WeakKeyDictionary
from time import time
from PyQt4.QtCore import QTimer

from time import *

from emglobjects import EMImage3DGUIModule, Camera, EMOpenGLFlagsAndTools, Camera2, EMViewportDepthTools
from emimageutil import ImgHistogram, EMEventRerouter, EMTransformPanel
from emapplication import EMStandAloneApplication, EMQtWidgetModule, EMGUIModule


MAG_INCREMENT_FACTOR = 1.1

class EM3DSliceViewerModule(EMImage3DGUIModule):
	
	def get_qt_widget(self):
		if self.parent == None:	
			self.parent = EM3DSliceViewerWidget(self)
			if isinstance(self.data,EMData):
				self.parent.set_camera_defaults(self.data)
		return self.parent
	
	def __init__(self,image=None, application=None):
		EMImage3DGUIModule.__init__(self,application)
		self.parent = None
		
		self.init()
		self.initialized = True
		
		self.inspector=None
	
		self.axes = []
		self.axes.append( Vec3f(1,0,0) )
		self.axes.append( Vec3f(0,1,0) )
		self.axes.append( Vec3f(0,0,1) )
		self.axes_idx = 2
		
		
		self.forceuse2dtextures = True	# This placed here by David Woolford - we get better performance
		
		self.track = False
		
		if image :
			self.set_data(image)
	
	def get_type(self):
		return "Slice Viewer"

	def init(self):
		self.data=None

		self.mmode=0
		self.cam = Camera2(self)
		
		self.vdtools = EMViewportDepthTools(self)
		
		self.cube = False
		self.inspector=None
		
		self.tex_name = 0
		self.tex_dl = 0

		self.glcontrast = 1.0
		self.glbrightness = 0.0
		
		self.rank = 1
		
		self.glflags = EMOpenGLFlagsAndTools()		# OpenGL flags - this is a singleton convenience class for testing texture support
	
	def updateGL(self):
		try: self.parent.updateGL()
		except: pass
	
	def eye_coords_dif(self,x1,y1,x2,y2,mdepth=True):
		return self.vdtools.eye_coords_dif(x1,y1,x2,y2,mdepth)
	
	def update_data(self,data):
		if data==None:
			print "Error, the data is empty"
			return
		
		if (isinstance(data,EMData) and data.get_zsize()<=1) :
			print "Error, the data is not 3D"
			return
		
		self.data = data.copy()
		
		min = self.data.get_attr("minimum")
		max = self.data.get_attr("maximum")
		
		self.data.add(-min)
		self.data.mult(1/(max-min))

		self.generate_current_display_list()
		self.updateGL()
		
	
	def set_data(self,data,fact=1.0):
		"""Pass in a 3D EMData object"""
		
		if data==None:
			print "Error, the data is empty"
			return
		
		if (isinstance(data,EMData) and data.get_zsize()<=1) :
			print "Error, the data is not 3D"
			return
		
		self.data = data.copy()
		
		min = self.data.get_attr("minimum")
		max = self.data.get_attr("maximum")
		
		self.data.add(-min)
		self.data.mult(1/(max-min))
		
		if not self.inspector or self.inspector ==None:
			self.inspector=EM3DSliceInspector(self)

		hist = self.data.calc_hist(256,0,1.0)
		self.inspector.set_hist(hist,0,1.0) 

		self.slice = data.get_zsize()/2
		self.zslice = data.get_zsize()/2
		self.yslice = data.get_ysize()/2
		self.xslice = data.get_xsize()/2
		self.trackslice = data.get_xsize()/2
		self.axis = 'z'
		self.inspector.set_sliceRange(0,data.get_zsize()-1)
		self.inspector.set_slice(self.zslice)
		self.generate_current_display_list()
		
	def get_eman_transform(self,p):
		
		if ( p[2] == 0 ):
			alt = 90
		else :
			alt = acos(p[2])*180.0/pi
		
		phi = atan2(p[0],p[1])
		phi *= 180.0/pi
		
		return [Transform({"type":"eman","alt":alt,"phi":phi}),alt,phi]
			
	def get_dimension_size(self):
		if ( self.axes_idx == 0 ):
			return self.data.get_xsize()
		elif ( self.axes_idx == 1 ):
			return self.data.get_ysize()
		elif ( self.axes_idx == 2 ):
			return self.data.get_zsize()
		else:
			#print "unsupported axis"
			# this is a hack and needs to be fixed eventually
			return self.data.get_xsize()
			#return 0
	def get_correct_dims_2d_emdata(self):
		if ( self.axes_idx == 0 ):
			return EMData(self.data.get_ysize(),self.data.get_zsize())
		elif ( self.axes_idx == 1 ):
			return EMData(self.data.get_xsize(),self.data.get_zsize())
		elif ( self.axes_idx == 2 ):
			return EMData(self.data.get_xsize(),self.data.get_ysize())
		else:
			#print "unsupported axis"
			# this is a hack and needs to be fixed eventually
			return EMData(self.data.get_xsize(),self.data.get_zsize())

	def generate_current_display_list(self):
		
		if ( self.tex_dl != 0 ): glDeleteLists( self.tex_dl, 1)
		
		self.tex_dl = glGenLists(1)

		if (self.tex_dl == 0): return #OpenGL is initialized yet
		
		if ( self.glflags.threed_texturing_supported() and not self.forceuse2dtextures ):
			self.get_3D_texture()
		else:
			self.gen_2D_texture()
	
	def get_3D_texture(self):

		glNewList(self.tex_dl,GL_COMPILE)
		
		if ( self.tex_name != 0 ): glDeleteTextures(self.tex_name)
		
		self.tex_name = self.glflags.gen_textureName(self.data)
		
		glEnable(GL_TEXTURE_3D)
		glBindTexture(GL_TEXTURE_3D, self.tex_name)
		#glPixelStorei(GL_UNPACK_ALIGNMENT, 1)
		glTexParameterf(GL_TEXTURE_3D, GL_TEXTURE_WRAP_S, GL_CLAMP)
		glTexParameterf(GL_TEXTURE_3D, GL_TEXTURE_WRAP_T, GL_CLAMP)
		glTexParameterf(GL_TEXTURE_3D, GL_TEXTURE_WRAP_R, GL_CLAMP)
		glTexParameterf(GL_TEXTURE_3D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
		if ( not data_dims_power_of(self.data,2) and self.glflags.npt_textures_unsupported()):
			glTexParameterf(GL_TEXTURE_3D, GL_TEXTURE_MIN_FILTER, GL_LINEAR_MIPMAP_LINEAR)
		else:
			glTexParameterf(GL_TEXTURE_3D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
			
		glTexEnvf(GL_TEXTURE_ENV, GL_TEXTURE_ENV_MODE, GL_REPLACE)
		
		glPushMatrix()
		glTranslate(0.5,0.5,0.5)
		
		glBegin(GL_QUADS)
		
		n = self.get_dimension_size()
		v = self.axes[self.axes_idx]
		[t,alt,phi] = self.get_eman_transform(v)
		v1 = t*Vec3f(-0.5,-0.5,0)
		v2 = t*Vec3f(-0.5, 0.5,0)
		v3 = t*Vec3f( 0.5, 0.5,0)
		v4 = t*Vec3f( 0.5,-0.5,0)
		vecs = [v1,v2,v3,v4]
		nn = float(self.slice)/float(n)

		trans = (nn-0.5)*v
		
		for r in vecs:
		
			w = [r[0] + trans[0], r[1] + trans[1], r[2] + trans[2]]
			t = [w[0]+0.5,w[1]+0.5,w[2]+0.5]
			glTexCoord3fv(t)
			glVertex3fv(w)
			
		glEnd()
		glPopMatrix()
		glDisable(GL_TEXTURE_3D)
		
		glEndList()
		
	def gen_2D_texture(self):
		glNewList(self.tex_dl,GL_COMPILE)
		
		n = self.get_dimension_size()
		v = self.axes[self.axes_idx]
		
		[t,alt,phi] = self.get_eman_transform(v)
			
		nn = float(self.slice)/float(n)
	
		tmp = self.get_correct_dims_2d_emdata() 

		trans = (nn-0.5)*v
		t.set_trans(2.0*int(n/2)*trans)
		tmp.cut_slice(self.data,t,True)
			
		if ( self.tex_name != 0 ): glDeleteTextures(self.tex_name)
		self.tex_name = 0
		
		self.tex_name = self.glflags.gen_textureName(tmp)
		
		glEnable(GL_TEXTURE_2D)
		glBindTexture(GL_TEXTURE_2D, self.tex_name)
			
		#glPixelStorei(GL_UNPACK_ALIGNMENT, 1)
		glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_CLAMP)
		glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_CLAMP)
		glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
		if ( not data_dims_power_of(self.data,2) and self.glflags.npt_textures_unsupported()):
			glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR_MIPMAP_LINEAR)
		else:
			glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
		glTexEnvf(GL_TEXTURE_ENV, GL_TEXTURE_ENV_MODE, GL_REPLACE)
		
			
		glPushMatrix()
		glTranslate(trans[0]+0.5,trans[1]+0.5,trans[2]+0.5)
		glRotatef(-phi,0,0,1)
		glRotatef(-alt,1,0,0)
		glBegin(GL_QUADS)
		glTexCoord2f(0,0)
		glVertex2f(-0.5,-0.5)
		
		glTexCoord2f(1,0)
		glVertex2f( 0.5,-0.5)
		
		glTexCoord2f(1,1)
		glVertex2f( 0.5, 0.5)
		
		glTexCoord2f(0,1)
		glVertex2f(-0.5, 0.5)
		glEnd()
		glPopMatrix()
		
		glDisable(GL_TEXTURE_2D)
		glEndList()
		
	def render(self):
		lighting = glIsEnabled(GL_LIGHTING)
		cull = glIsEnabled(GL_CULL_FACE)
		polygonmode = glGetIntegerv(GL_POLYGON_MODE)
		glDisable(GL_LIGHTING)
		glDisable(GL_CULL_FACE)
		
		glPolygonMode(GL_FRONT_AND_BACK,GL_FILL);
		
		glPushMatrix()
		self.cam.position(True)
		# the ones are dummy variables atm... they don't do anything
		self.vdtools.update(1,1)
		glPopMatrix()
		
		self.cam.position()
		self.vdtools.store_model()
		
		if ( self.track ):
			self.loadTrackAxis()
			self.generate_current_display_list()
		
		if ( self.tex_dl == 0 ):
			self.generate_current_display_list()
		
		glStencilFunc(GL_EQUAL,self.rank,0)
		glStencilOp(GL_KEEP,GL_KEEP,GL_REPLACE)
		glPushMatrix()
		glTranslate(-self.data.get_xsize()/2.0,-self.data.get_ysize()/2.0,-self.data.get_zsize()/2.0)
		glScalef(self.data.get_xsize(),self.data.get_ysize(),self.data.get_zsize())
		glCallList(self.tex_dl)
		glPopMatrix()
		
		glStencilFunc(GL_EQUAL,self.rank,self.rank)
		glStencilOp(GL_KEEP,GL_KEEP,GL_KEEP)
		glPushMatrix()
		glLoadIdentity()
		[width,height] = self.parent.get_near_plane_dims()
		z = self.parent.get_start_z()
		glTranslate(-width/2.0,-height/2.0,-z-0.01)
		glScalef(width,height,1.0)
		self.draw_bc_screen()
		glPopMatrix()
		
		glStencilFunc(GL_ALWAYS,1,1)
		glColor3f(1,1,1)
		if self.cube:
			glPushMatrix()
			self.draw_volume_bounds()
			glPopMatrix()
			
		if ( lighting ): glEnable(GL_LIGHTING)
		if ( cull ): glEnable(GL_CULL_FACE)
		
		if ( polygonmode[0] == GL_LINE ): glPolygonMode(GL_FRONT, GL_LINE)
		if ( polygonmode[1] == GL_LINE ): glPolygonMode(GL_BACK, GL_LINE)
	
	def set_slice(self,val):
		self.slice = val
		if self.axis == 'z':
			self.zslice = val
		elif self.axis == 'y':
			self.yslice = val
		elif self.axis == 'x':
			self.xslice = val
		else:
			self.trackslice = val
		
		self.generate_current_display_list()
		self.updateGL()
		
	def setAxis(self,val):
		self.axis = str(val).strip()
		
		if (self.inspector != None):
			if self.axis == 'z':
				self.inspector.set_sliceRange(0,self.data.get_zsize()-1)
				self.inspector.set_slice(self.zslice)
				self.axes_idx = 2
				self.track = False
			elif self.axis == 'y':
				self.inspector.set_sliceRange(0,self.data.get_ysize()-1)
				self.inspector.set_slice(self.yslice)
				self.axes_idx = 1
				self.track = False
			elif self.axis == 'x':
				self.inspector.set_sliceRange(0,self.data.get_xsize()-1)
				self.inspector.set_slice(self.xslice)
				self.axes_idx = 0
				self.track = False
			elif self.axis == 'track':
				self.track = True
				self.inspector.set_sliceRange(0,self.data.get_xsize()-1)
				self.inspector.set_slice(self.trackslice)
				self.axes_idx = 3
				
				self.loadTrackAxis()
			else:
				print "Error, unknown axis", self.axis, val
		
		self.generate_current_display_list()
		self.updateGL()

	def update_inspector(self,t3d):
		if not self.inspector or self.inspector ==None:
			self.inspector=EM3DSliceInspector(self)
		self.inspector.update_rotations(t3d)
	
	def get_inspector(self):
		if not self.inspector : self.inspector=EM3DSliceInspector(self)
		return self.inspector

	def loadTrackAxis(self):
		t3d = self.vdtools.getEmanMatrix()
		#at3d = self.cam.t3d_stack[len(self.cam.t3d_stack)-1]
		
		point = Vec3f(0,0,1)
		
		point *= 1.0/self.vdtools.getCurrentScale()
		
		point = point*t3d
		
		#if ( point[2] != 0 ): point[2] = -point[2]
		
		if len(self.axes) == 3 :
			self.axes.append(point)
		else:
			self.axes[3] = point

	def resizeEvent(self,width=0,height=0):
		self.vdtools.set_update_P_inv()
		
class EM3DSliceViewerWidget(QtOpenGL.QGLWidget,EMEventRerouter):
	
	allim=WeakKeyDictionary()
	def __init__(self, em_slice_viewer_module):
		assert(isinstance(em_slice_viewer_module,EM3DSliceViewerModule))
		EM3DSliceViewerWidget.allim[self]=0
		
		fmt=QtOpenGL.QGLFormat()
		fmt.setDoubleBuffer(True)
		fmt.setDepth(1)
		fmt.setSampleBuffers(True)
		QtOpenGL.QGLWidget.__init__(self,fmt)
		EMEventRerouter.__init__(self)
		
		self.fov = 50 # field of view angle used by gluPerspective
		self.startz = 1
		self.endz = 5000
		self.cam = Camera()
		self.target = em_slice_viewer_module
		
	def set_camera_defaults(self,data):
		self.cam.default_z = -1.25*data.get_zsize()
		self.cam.cam_z = -1.25*data.get_zsize()
		
	def set_data(self,data):
		self.target.set_data(data)
		self.set_camera_defaults(data)
		
	def initializeGL(self):
		glEnable(GL_NORMALIZE)
		glEnable(GL_LIGHT0)
		glEnable(GL_DEPTH_TEST)
		#print "Initializing"
		glLightfv(GL_LIGHT0, GL_AMBIENT, [0.9, 0.9, 0.9, 1.0])
		glLightfv(GL_LIGHT0, GL_DIFFUSE, [1.0, 1.0, 1.0, 1.0])
		glLightfv(GL_LIGHT0, GL_SPECULAR, [1.0, 1.0, 1.0, 1.0])
		glLightfv(GL_LIGHT0, GL_POSITION, [0.5,0.7,11.,0.])
		GL.glHint(GL_PERSPECTIVE_CORRECTION_HINT, GL_NICEST)
		
		GL.glClearColor(0,0,0,0)
		#GL.glClearAccum(0,0,0,0)
	
		glShadeModel(GL_SMOOTH)
		
		glClearStencil(0)
		glEnable(GL_STENCIL_TEST)
		
	def paintGL(self):
		#glClear(GL_ACCUM_BUFFER_BIT)
		glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT | GL_STENCIL_BUFFER_BIT )
		
		glMatrixMode(GL_MODELVIEW)
		glLoadIdentity()
		
		self.cam.position()
		
		glPushMatrix()
		self.target.render()
		glPopMatrix()
		
		#glAccum(GL_ADD, self.target.glbrightness)
		#glAccum(GL_ACCUM, self.target.glcontrast)
		#glAccum(GL_RETURN, 1.0)
		
	def resizeGL(self, width, height):
		if width<=0 or height<=0 : 
			print "bad size"
			return
		# just use the whole window for rendering
		glViewport(0,0,self.width(),self.height())
		
		# maintain the aspect ratio of the window we have
		self.aspect = float(self.width())/float(self.height())
		
		glMatrixMode(GL_PROJECTION)
		glLoadIdentity()
		# using gluPerspective for simplicity
		gluPerspective(self.fov,self.aspect,self.startz,self.endz)
		
		# switch back to model view mode
		glMatrixMode(GL_MODELVIEW)
		glLoadIdentity()
		
		
		self.target.resizeEvent()

	def get_start_z(self):
		return self.startz
	
	def get_near_plane_dims(self):
		height = 2.0 * self.startz*tan(self.fov/2.0*pi/180.0)
		width = self.aspect * height
		return [width,height]

	def show_inspector(self,force=0):
		self.target.show_inspector(self,force)

	def get_render_dims_at_depth(self,depth):
		# This function returns the width and height of the renderable 
		# area at the origin of the data volume
		height = -2*tan(self.fov/2.0*pi/180.0)*(depth)
		width = self.aspect*height
		
		return [width,height]
	

class EM3DSliceInspector(QtGui.QWidget):
	def __init__(self,target) :
		QtGui.QWidget.__init__(self,None)
		self.rotation_sliders = EMTransformPanel(target,self)
		self.target=target
		
		self.vbl = QtGui.QVBoxLayout(self)
		self.vbl.setMargin(0)
		self.vbl.setSpacing(6)
		self.vbl.setObjectName("vbl")
		
		self.hbl = QtGui.QHBoxLayout()
		self.hbl.setMargin(0)
		self.hbl.setSpacing(6)
		self.hbl.setObjectName("hbl")
		self.vbl.addLayout(self.hbl)
		
		self.hist = ImgHistogram(self)
		self.hist.setObjectName("hist")
		self.hbl.addWidget(self.hist)
		
		self.vbl2 = QtGui.QVBoxLayout()
		self.vbl2.setMargin(0)
		self.vbl2.setSpacing(6)
		self.vbl2.setObjectName("vbl2")
		self.hbl.addLayout(self.vbl2)
	
		self.cubetog = QtGui.QPushButton("Cube")
		self.cubetog.setCheckable(1)
		self.vbl2.addWidget(self.cubetog)
		
		self.defaults = QtGui.QPushButton("Defaults")
		self.vbl2.addWidget(self.defaults)
		
		self.vbl.addWidget(self.get_main_tab())
		
		self.n3_showing = False
		
		self.current_src = EULER_EMAN
		
		QtCore.QObject.connect(self.slice, QtCore.SIGNAL("valueChanged"), target.set_slice)
		QtCore.QObject.connect(self.glcontrast, QtCore.SIGNAL("valueChanged"), target.set_GL_contrast)
		QtCore.QObject.connect(self.glbrightness, QtCore.SIGNAL("valueChanged"), target.set_GL_brightness)
		QtCore.QObject.connect(self.axisCombo, QtCore.SIGNAL("currentIndexChanged(QString)"), target.setAxis)
		QtCore.QObject.connect(self.cubetog, QtCore.SIGNAL("toggled(bool)"), target.toggle_cube)
		QtCore.QObject.connect(self.defaults, QtCore.SIGNAL("clicked(bool)"), self.set_defaults)
	
	def update_rotations(self,t3d):
		self.rotation_sliders.update_rotations(t3d)
	
	def set_scale(self,val):
		self.rotation_sliders.set_scale(val)
	
	def set_xy_trans(self, x, y):
		self.rotation_sliders.set_xy_trans(x,y)
		
	def get_transform_layout(self):
		return self.maintab.vbl
	
	def set_defaults(self):
		self.glcontrast.setValue(1.0)
		self.glbrightness.setValue(0.0)
		self.rotation_sliders.set_defaults()

	def get_main_tab(self):
	
		self.maintab = QtGui.QWidget()
		maintab = self.maintab
		maintab.vbl = QtGui.QVBoxLayout(self.maintab)
		maintab.vbl.setMargin(0)
		maintab.vbl.setSpacing(6)
		maintab.vbl.setObjectName("Main")
		
		self.hbl_slice = QtGui.QHBoxLayout()
		self.hbl_slice.setMargin(0)
		self.hbl_slice.setSpacing(6)
		self.hbl_slice.setObjectName("Axis")
		maintab.vbl.addLayout(self.hbl_slice)
		
		self.slice = ValSlider(maintab,(0.0,10.0),"Slice:")
		self.slice.setObjectName("slice")
		self.slice.setValue(1.0)
		self.hbl_slice.addWidget(self.slice)
		
		self.axisCombo = QtGui.QComboBox(maintab)
		self.axisCombo.addItem(' z ')
		self.axisCombo.addItem(' y ')
		self.axisCombo.addItem(' x ')
		self.axisCombo.addItem(' track ')
		self.hbl_slice.addWidget(self.axisCombo)
		
		self.glcontrast = ValSlider(maintab,(1.0,5.0),"GLShd:")
		self.glcontrast.setObjectName("GLShade")
		self.glcontrast.setValue(1.0)
		maintab.vbl.addWidget(self.glcontrast)
		
		self.glbrightness = ValSlider(maintab,(-1.0,0.0),"GLBst:")
		self.glbrightness.setObjectName("GLBoost")
		self.glbrightness.setValue(0.1)
		self.glbrightness.setValue(0.0)
		maintab.vbl.addWidget(self.glbrightness)
	
		self.rotation_sliders.addWidgets(maintab.vbl)
		
		return maintab
	
	def slider_rotate(self):
		self.target.load_rotation(self.get_current_rotation())

	def set_hist(self,hist,minden,maxden):
		self.hist.set_data(hist,minden,maxden)
		
	def set_slice(self,val):
		self.slice.setValue(val)
	
	def set_sliceRange(self,min,max):
		self.slice.setRange(min,max)
	
		
	
if __name__ == '__main__':
	em_app = EMStandAloneApplication()
	window = EM3DSliceViewerModule(application=em_app)
	
	if len(sys.argv)==1 : 
		data = []
		#for i in range(0,200):
		e = EMData(64,64,64)
		e.process_inplace('testimage.axes')
		window.set_data(e)
	else :
		a=EMData(sys.argv[1])
		window.set_file_name(sys.argv[1])
		window.set_data(a)
		
	em_app.show()
	em_app.execute()

