import weakref
from libpyTransform2 import Vec3f, Transform, Vec2f
from libpyUtils2 import Util
from math import sqrt, atan2, pi

import numpy
from OpenGL.GL import glColor, glMaterial, glTranslate, glGetDoublev
from OpenGL.GLU import gluProject
from OpenGL.raw.GL.VERSION.GL_1_0 import glMatrixMode, glPushMatrix, glLoadIdentity, glOrtho, glPopMatrix, glTranslated, \
    glRotated, glScaled, glCallList, glScalef
from OpenGL.raw.GL.VERSION.GL_1_1 import GL_FRONT, GL_AMBIENT_AND_DIFFUSE, GL_SPECULAR, GL_SHININESS, GL_PROJECTION, \
    GL_MODELVIEW, GL_AMBIENT, GL_MODELVIEW_MATRIX

from libpyEM.qtgui.emglobjects import EMBasicOpenGLObjects


class EMViewportDepthTools2:
	"""
	This class provides important tools for EMAN2 floating widgets -
	these are either qt widgets that get mapped as textures to
	polygons situated in OpenGL volumes, or are OpenGL objects themselves
	(such as a 2D image texture, or a 3D isosurface), that get drawn
	within a frame somewhere in the 3D world.
	
	These objects need to have mouse events (etc) correctly rerouted to them,
	and this is not trivial (but not difficult) to do, considering that the
	mouse events are always in terms of the viewport, but the texture mapped
	widget is somewhere in 3D space. The function eye_coords_dif is primarily
	for positioning the widgits in 3D space (translation), whereas the 
	mouseinwin function is specifically for mapping the mouse event coordinates
	into the widgit's transformed coordinate system.

	This class also provides important collision detection functionality - it
	does this by mapping the corners of the (widgit mapped) polygon to the viewport,
	and then determing if the (mouse) coordinate is within this area. Mapping 
	polygon vertices to the veiwport is done using gluUnproject, whereas converting
	viewport coordinates into polygon coordinates is done doing something similar to
	gluProject (the opposite operation).

	This class also provides widget frame drawing functionality (which may become redundant)
	It does this by drawing cylinders in terms of how the polygon corners mapped
	to the viewport - this causes the loss of depth information
	
	The only important behaviour expected of something that uses this class is
	1 - you must call update() just before you draw the textured widgit polygon
	other object (i.e. when the contents of the OpenGL modelview matrix reflect 
	all of the operations that are applied before rendering)
	2 - you should call set_update_P_inv() if the OpenGL projection matrix is altered,
	this typically happens when resizeGL is called in the root widgit.
	"""
	def __init__(self, parent):
		
		self.glbasicobjects = EMBasicOpenGLObjects()		# need basic objects for drawing the frame
		self.matrices = weakref.ref(parent)			# an object that stores static instances of the important viewing matrices
		self.borderwidth = 3.0								# effects the border width of the frame decoration
		
	def set_update_P_inv(self,val=True):
		self.matrices().set_projection_view_update(val)
	
	def get_viewport_dimensions(self):
		return self.matrices().get_viewport_matrix()
	
	def draw_frame(self, ftest=False):
		
		if (ftest):
			a = Vec3f(self.mc10[0]-self.mc00[0],self.mc10[1]-self.mc00[1],self.mc10[2]-self.mc00[2])
			b = Vec3f(self.mc01[0]-self.mc00[0],self.mc01[1]-self.mc00[1],self.mc01[2]-self.mc00[2])
			c = a.cross(b)
			if ( c[2] < 0 ):
				#print "facing backward"
				return False
			
		glColor(.9,.2,.8)
		# this is a nice light blue color (when lighting is on)
		# and is the default color of the frame
		glMaterial(GL_FRONT,GL_AMBIENT_AND_DIFFUSE,(.2,.2,.8,1.0))
		glMaterial(GL_FRONT,GL_SPECULAR,(.8,.8,.8,1.0))
		glMaterial(GL_FRONT,GL_SHININESS,50.0)
		
		glMatrixMode(GL_PROJECTION)
		glPushMatrix()
		glLoadIdentity()
		glOrtho(0.0,self.matrices().viewport_width(),0.0,self.matrices().viewport_height(),-5,5)

		glMatrixMode(GL_MODELVIEW)
		glPushMatrix()
		glLoadIdentity()
		
		glColor(.9,.2,.8)
		# this is a nice light blue color (when lighting is on)
		# and is the default color of the frame
		glMaterial(GL_FRONT,GL_AMBIENT,(.2,.2,.8,1.0))
		glMaterial(GL_FRONT,GL_SPECULAR,(.8,.8,.8,1.0))
		glMaterial(GL_FRONT,GL_SHININESS,50.0)
		
		#draw the cylinders around the edges of the frame
		glPushMatrix()
		self.cylinderToFrom(self.mc00,self.mc10)
		glPopMatrix()
		glPushMatrix()
		self.cylinderToFrom(self.mc10,self.mc11)
		glPopMatrix()
		glPushMatrix()
		self.cylinderToFrom(self.mc11,self.mc01)
		glPopMatrix()
		glPushMatrix()
		self.cylinderToFrom(self.mc01,self.mc00)
		glPopMatrix()
		
		# draw spheres as nodes at the corners of the frame
		glPushMatrix()
		self.sphereAt(self.mc00)
		glPopMatrix()
		glPushMatrix()
		self.sphereAt(self.mc10)
		glPopMatrix()
		glPushMatrix()
		self.sphereAt(self.mc11)
		glPopMatrix()
		glPushMatrix()
		self.sphereAt(self.mc01)
		glPopMatrix()
		
		glPopMatrix()
		
		glMatrixMode(GL_PROJECTION)
		# pop the temporary orthographic matrix from the GL_PROJECTION stack
		glPopMatrix()
		glMatrixMode(GL_MODELVIEW)
		
		return True
	def cylinderToFrom(self,To,From):
		#print "To",To[0],To[1]
		#print "From",From[0],From[1]
		# draw a cylinder to To from From
		dx = To[0] - From[0]
		dy = To[1] - From[1]
		
		length = sqrt(dx*dx+dy*dy)
		
		angle = 180.0*atan2(dy,dx)/pi
		
		glTranslated(From[0],From[1],0)
		glRotated(90.0+angle,0.,0.,1.0)
		glRotated(90.,1.,0.,0.)
		glTranslated(0.0,0.0,length/2.0)
		glScaled(self.borderwidth,self.borderwidth,length)
		glTranslated(0.0,0.0,-0.5)
		glCallList(self.glbasicobjects.getCylinderDL())
		
	def sphereAt(self,at):
		glTranslate(at[0],at[1],0)
		glScalef(3.0*self.borderwidth,3.0*self.borderwidth,3.0*self.borderwidth)
		glCallList(self.glbasicobjects.getSphereDL())
	
	def update(self,width,height):
		
		self.wmodel= glGetDoublev(GL_MODELVIEW_MATRIX)
		self.wproj = self.matrices().get_proj_matrix()
		self.wview = self.matrices().get_viewport_matrix()

		try:
			self.mc00=gluProject(-width,-height,0.,self.wmodel,self.wproj,self.wview)
			self.mc10=gluProject( width,-height,0.,self.wmodel,self.wproj,self.wview)
			self.mc11=gluProject( width, height,0.,self.wmodel,self.wproj,self.wview)
			self.mc01=gluProject(-width, height,0.,self.wmodel,self.wproj,self.wview)
			
		except:
			self.mc00 = [0,0,0]
			self.mc10 = [0,0,0]
			self.mc11 = [0,0,0]
			self.mc01 = [0,0,0]
	
	def unproject_points(self,points):
		unprojected = []
		self.wmodel= glGetDoublev(GL_MODELVIEW_MATRIX)
		self.wproj = self.matrices().get_proj_matrix()
		self.wview = self.matrices().get_viewport_matrix()
		for p in points:
			unprojected.append(gluProject(p[0],p[1],p[2],self.wmodel,self.wproj,self.wview))
			
		return unprojected
	
	def set_mouse_coords(self,mc00,mc10,mc11,mc01):
		self.mc00 = mc00
		self.mc10 = mc10
		self.mc11 = mc11
		self.mc01 = mc01
	
	def update_points(self,p1,p2,p3,p4):
		
		self.wmodel= glGetDoublev(GL_MODELVIEW_MATRIX)
		self.wproj = self.matrices().get_proj_matrix()
		self.wview = self.matrices().get_viewport_matrix()

		try:
			self.mc00=gluProject(p1[0],p1[1],p1[2],self.wmodel,self.wproj,self.wview)
			self.mc10=gluProject(p2[0],p2[1],p2[2],self.wmodel,self.wproj,self.wview)
			self.mc11=gluProject(p3[0],p3[1],p3[2],self.wmodel,self.wproj,self.wview)
			self.mc01=gluProject(p4[0],p4[1],p4[2],self.wmodel,self.wproj,self.wview)
			
		except:
			self.mc00 = [0,0,0]
			self.mc10 = [0,0,0]
			self.mc11 = [0,0,0]
			self.mc01 = [0,0,0]
			
	def get_corners(self):
		return [self.mc00,self.mc01,self.mc11,self.mc10]
	
	def getEmanMatrix(self):
	
		t = Transform([ self.wmodel[0][0], self.wmodel[1][0], self.wmodel[2][0], 0,
						self.wmodel[0][1], self.wmodel[1][1], self.wmodel[2][1], 0,
						self.wmodel[0][2], self.wmodel[1][2], self.wmodel[2][2], 0 ])
		return t
	
	def getCurrentScale(self):
		return sqrt(self.wmodel[0][0]**2 + self.wmodel[0][1]**2 + self.wmodel[0][2]**2)
	
	def getModelMatrix(self):
		return self.wmodel
	
	def setModelMatrix(self, model):
		self.wmodel = model
	
	def setCorners(self,points):
		self.mc00 = points[0]
		self.mc01 = points[1]
		self.mc11 = points[2]
		self.mc10 = points[3]
		
	def store_model(self):
		self.wmodel= glGetDoublev(GL_MODELVIEW_MATRIX)
	
	def printUnproj(self,x,y):
		self.wmodel= glGetDoublev(GL_MODELVIEW_MATRIX)
		self.wproj = self.matrices().get_proj_matrix()
		self.wview = self.matrices().get_viewport_matrix()
	
		t = gluProject(x,y,0.,self.wmodel,self.wproj,self.wview)
		print t[0],t[1],t[2]
		
		
	def getMappedWidth(self):
		return int(self.mc11[0]-self.mc00[0])
		
	def getMappedHeight(self):
		return int(self.mc11[1]-self.mc00[1])
	
	def isinwinpoints(self,x,y,points):
		
		return Util.point_is_in_convex_polygon_2d(Vec2f(points[0][0],points[0][1]),Vec2f(points[1][0],points[1][1]),Vec2f(points[2][0],points[2][1]),Vec2f(points[3][0],points[3][1]),Vec2f(x,y))
		
		
		#try:
			#a = [points[0][0]-x, points[0][1]-y]
			#b = [points[1][0]-x, points[1][1]-y]
			#c = [points[2][0]-x, points[2][1]-y]
			#d = [points[3][0]-x, points[3][1]-y]
			
			#aeb = self.getsubtendingangle(a,b)
			#bec = self.getsubtendingangle(b,c)
			#ced = self.getsubtendingangle(c,d)
			#dea = self.getsubtendingangle(d,a)
			#if abs(aeb + bec + ced + dea) > 0.1:
				#return True 
			#else:
				#return False
		#except:
			#return False
	
	def isinwin(self,x,y):
		return Util.point_is_in_convex_polygon_2d(Vec2f(self.mc00[0],self.mc00[1]),Vec2f(self.mc01[0],self.mc01[1]),Vec2f(self.mc11[0],self.mc11[1]),Vec2f(self.mc10[0],self.mc10[1]),Vec2f(x,y))
		
	#def isinwin(self,x,y):
		## this function can be called to determine
		## if the event at x,y (in terms of the viewport)
		## was within the frame of the object being drawn
		
		##print x,y
		##print self.mc00,self.mc11
		
		#try:
			#a = [self.mc00[0]-x, self.mc00[1]-y]
			#b = [self.mc01[0]-x, self.mc01[1]-y]
			#c = [self.mc11[0]-x, self.mc11[1]-y]
			#d = [self.mc10[0]-x, self.mc10[1]-y]
			
			#aeb = self.getsubtendingangle(a,b)
			#bec = self.getsubtendingangle(b,c)
			#ced = self.getsubtendingangle(c,d)
			#dea = self.getsubtendingangle(d,a)
			#if abs(aeb + bec + ced + dea) > 0.1:
				#return True 
			#else:
				#return False
		#except:
	
	def getsubtendingangle(self,a,b):
		sinaeb = a[0]*b[1]-a[1]*b[0]
		cosaeb = a[0]*b[0]+a[1]*b[1]
		
		return atan2(sinaeb,cosaeb)
	
	def eye_coords_dif(self,x1,y1,x2,y2,maintaindepth=True):
		self.wview = self.matrices().get_viewport_matrix()
		# get x and y normalized device coordinates
		xNDC1 = 2.0*(x1-self.wview[0])/self.wview[2] - 1
		yNDC1 = 2.0*(y1-self.wview[1])/self.wview[3] - 1
		
		xNDC2 = 2.0*(x2-self.wview[0])/self.wview[2] - 1
		yNDC2 = 2.0*(y2-self.wview[1])/self.wview[3] - 1
		
		self.P_inv = self.matrices().get_proj_inv_matrix()
		
		try:
			M = numpy.matrix(self.wmodel)
		except:
			self.store_model()
			M = numpy.matrix(self.wmodel)
		M_inv = M.I
		
		#PM_inv = numpy.matrixmultiply(P_inv,M_inv)
		PM_inv = self.P_inv*M_inv
		
		# If the widget is planar (which obviosuly holds), and along z=0, then the following holds
		zNDC1 = (PM_inv[0,2]*xNDC1 + PM_inv[1,2]*yNDC1 + PM_inv[3,2])/(-PM_inv[2,2])
		if ( maintaindepth == False):
			zNDC2 = (PM_inv[0,2]*xNDC2 + PM_inv[1,2]*yNDC2 + PM_inv[3,2])/(-PM_inv[2,2])
		else:
			zNDC2 = zNDC1
	
		# We need zprime, which is really 'eye_z' in OpenGL lingo
		zprime1 = 1.0/(xNDC1*self.P_inv[0,3]+yNDC1*self.P_inv[1,3]+zNDC1*self.P_inv[2,3]+self.P_inv[3,3])
		zprime2 = 1.0/(xNDC2*self.P_inv[0,3]+yNDC2*self.P_inv[1,3]+zNDC2*self.P_inv[2,3]+self.P_inv[3,3])

		ex1 = (self.P_inv[0,0]*xNDC1 + self.P_inv[1,0]*yNDC1 + self.P_inv[2,0]*zNDC1+self.P_inv[3,0])*zprime1;
		ey1 = (self.P_inv[0,1]*xNDC1 + self.P_inv[1,1]*yNDC1 + self.P_inv[2,1]*zNDC1+self.P_inv[3,1])*zprime1;
		#ez1 = (self.P_inv[0,2]*xNDC1 + self.P_inv[1,2]*yNDC1 + self.P_inv[2,2]*zNDC1+self.P_inv[3,2])*zprime1;
		
		ex2 = (self.P_inv[0,0]*xNDC2 + self.P_inv[1,0]*yNDC2 + self.P_inv[2,0]*zNDC2+self.P_inv[3,0])*zprime2;
		ey2 = (self.P_inv[0,1]*xNDC2 + self.P_inv[1,1]*yNDC2 + self.P_inv[2,1]*zNDC2+self.P_inv[3,1])*zprime2;
		
		return [ex2-ex1,ey2-ey1]

	def mouseinwin(self,x,y,width,height):
		self.wview = self.matrices().get_viewport_matrix()
		# to determine the mouse coordinates in the window we carefully perform
		# linear algebra similar to what's done in gluUnProject

		# the problem is determining what the z coordinate of the mouse event should have
		# been, given that we know that the widget itself is located in the x,y plane, along z=0.
		
		# get x and y normalized device coordinates
		xNDC = 2.0*(x-self.wview[0])/self.wview[2] - 1
		yNDC = 2.0*(y-self.wview[1])/self.wview[3] - 1
		
		# invert the projection and model view matrices, they will be used shortly
		# note the OpenGL returns matrices are in column major format -  the calculations below 
		# are done with this in  mind - this saves the need to transpose the matrices
		self.P_inv = self.matrices().get_proj_inv_matrix()
		
		try:
			M = numpy.matrix(self.wmodel)
		except:
			self.store_model()
			M = numpy.matrix(self.wmodel)
		M_inv = M.I
		#PM_inv = numpy.matrixmultiply(P_inv,M_inv)
		PM_inv = self.P_inv*M_inv
		
		# If the widget is planar (which obviosuly holds), and along z=0, then the following holds
		zNDC = (PM_inv[0,2]*xNDC + PM_inv[1,2]*yNDC + PM_inv[3,2])/(-PM_inv[2,2])
	
		# We need zprime, which is really 'eye_z' in OpenGL lingo
		zprime = 1.0/(xNDC*self.P_inv[0,3]+yNDC*self.P_inv[1,3]+zNDC*self.P_inv[2,3]+self.P_inv[3,3])
		
		# Now we compute the x and y coordinates - these are precisely what we're after
		xcoord = zprime*(xNDC*PM_inv[0,0]+yNDC*PM_inv[1,0]+zNDC*PM_inv[2,0]+PM_inv[3,0])
		ycoord = zprime*(xNDC*PM_inv[0,1]+yNDC*PM_inv[1,1]+zNDC*PM_inv[2,1]+PM_inv[3,1])

		return (xcoord, height-ycoord)