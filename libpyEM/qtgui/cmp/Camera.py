from libpyTransform2 import Transform
from math import atan2, sin, cos, sqrt, pi

from OpenGL.GL import glRotate
from OpenGL.raw.GL.VERSION.GL_1_0 import glTranslated, glScalef


class Camera:
	"""\brief A camera object encapsulates 6 degrees of freedom, and a scale factor
	
	The camera object stores x,y,z coordinates and a single transform object.
	For instance, it can be used for positioning and moving the 'camera' in OpenGL,
	however, instead of literally moving a camera, in OpenGL the scene itself is moved
	and the camera is generally thought of as staying still.
	
	Use the public interface of setCamTrans and motion_rotate (which is based on mouse movement)_
	to move the camera position
	
	Then call 'position' in your main OpenGL draw function before drawing anything.
	
	"""
	def __init__(self):
		# The magnification factor influences how the scale (zoom) is altered when a zoom event is received.
		# The equation is scale *= mag_factor or scale /= mag_factor, depending on the event.
		self.mag_factor = 1.1
		self.scale = 1.0
		
		# The camera coordinates
		self.cam_x = 0
		self.cam_y = 0
		self.cam_z = 0
		
		# Camera offsets - generally you want to set default_z to some negative
		# value the OpenGL scene is viewable.
		self.default_x = 0
		self.default_y = 0
		self.default_z = 0
		
		# The Transform3D object stores the rotation
		t3d = Transform()
		#t3d.to_identity()
	
		# At the moment there is a stack of Transform3D objects, this is for the purposes
		# of undoing actions. If the undo functionality was not required, the stack could be
		# removed.
		self.t3d_stack = []
		self.t3d_stack.append(t3d)
		
	def printme(self):
		print "translating to",self.cam_x, self.cam_y, self.cam_z
		rot = self.t3d_stack[len(self.t3d_stack)-1].get_rotation()
		print "rotatint",rot["phi"],rot["alt"],rot["az"]
		print "scale",self.scale
		
	def position(self):
		# position the camera, regular OpenGL movement.
		glTranslated(self.cam_x, self.cam_y, self.cam_z)
		
		rot = self.t3d_stack[len(self.t3d_stack)-1].get_rotation("eman")
		glRotate(float(rot["phi"]),0,0,1)
		glRotate(float(rot["alt"]),1,0,0)
		glRotate(float(rot["az"]),0,0,1)
		
		# here is where zoom is applied
		glScalef(self.scale,self.scale,self.scale)
		
	def scale_event(self,delta):
		if delta > 0:
			self.scale *= self.mag_factor
		elif delta < 0:
			self.scale *= 1.0/self.mag_factor
	
	def setCamTrans(self,axis,value):
		if ( axis == 'x'):
			self.set_cam_x(value)
		elif ( axis == 'y'):
			self.set_cam_y(value)
		elif ( axis == 'z'):
			self.set_cam_z(value)
		elif ( axis == 'default_x'):
			self.default_x = value
		elif ( axis == 'default_y'):
			self.default_y = value
		elif ( axis == 'default_z'):
			self.default_z = value
			self.set_cam_z(self.cam_z)
		else:
			print 'Error, the axis (%s) specified is unknown. No action was taken' %axis
	
	def set_cam_z(self,z):
		self.cam_z = self.default_z + z
		
	def set_cam_y(self,y):
		self.cam_y = self.default_y + y
		
	def set_cam_x(self,x):
		self.cam_x = self.default_x + x

	def motion_rotate(self,x,y):
		# this function implements mouse interactive rotation
		# [x,y] is the vector generating by the mouse movement (in the plane of the screen)
		# Rotation occurs about the vector 90 degrees to [x,y,0]
		# The amount of rotation is linealy proportional to the length of [x,y]
		
		if ( x == 0 and y == 0): return
		
		theta = atan2(-y,x)

		rotaxis_x = sin(theta)
		rotaxis_y = cos(theta)
		rotaxis_z = 0
		
		length = sqrt(x*x + y*y)
		# 8.0 is a magic number - things rotate more if they are closer and slower if they are far away in this appproach
		# Or does it?
		# This magic number could be overcome using a strategy based on the results of get_render_dims_at_depth
		angle = length/8.0*pi
		
		#t3d = Transform3D()
		t3d = Transform()
		quaternion = {}
		quaternion["omega"] = angle
		quaternion["n1"] = rotaxis_x
		quaternion["n2"] = rotaxis_y
		quaternion["n3"] = rotaxis_z
		quaternion["type"] = "spin"
		
		#t3d.set_rotation( EULER_SPIN, quaternion )
		t3d.set_params(quaternion)
		size = len(self.t3d_stack)
		self.t3d_stack[size-1] = t3d*self.t3d_stack[size-1]
		
	def set_scale(self,val):
		self.scale = val
	
	def load_rotation(self,t3d):
		self.t3d_stack.append(t3d)

	def get_thin_copy(self):
		# this is called a thin copy because it does not copy the entire t3d stack, just the last t3d
		cam = Camera()
		size = len(self.t3d_stack)
		cam.load_rotation(self.t3d_stack[size-1])
		
		cam.scale =	self.scale
		cam.cam_x = self.cam_x
		cam.cam_y = self.cam_y
		cam.cam_z = self.cam_z
		
		cam.default_x = self.default_x
		cam.default_y = self.default_y
		cam.default_z = self.default_z
		
		return cam