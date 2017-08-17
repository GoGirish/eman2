import weakref
from libpyTransform2 import Transform
from math import atan2, sin, cos, sqrt, pi

from OpenGL.GL import glRotate, glTranslate, glScale
from OpenGL.raw.GL.VERSION.GL_1_0 import glScalef
from PyQt4 import QtCore
from PyQt4.QtCore import Qt

from libpyEM.qtgui.emglobjects import viewport_height
from libpyEM.qtgui.cmp.Camera import Camera


class Camera2:
	"""\brief A camera object encapsulates 6 degrees of freedom, and a scale factor
	
	The camera object stores x,y,z coordinates and a single transform object.
	For instance, it can be used for positioning and moving the 'camera' in OpenGL,
	however, instead of literally moving a camera, in OpenGL the scene itself is moved
	and the camera is generally thought of as staying still.
	
	Use the public interface of setCamTrans and motion_rotate (which is based on mouse movement)_
	to move the camera position
	
	Then call 'position' in your main OpenGL draw function before drawing anything.
	
	"""
	def __init__(self,parent):
		self.emit_events = False
		# The magnification factor influences how the scale (zoom) is altered when a zoom event is received.
		# The equation is scale *= mag_factor or scale /= mag_factor, depending on the event.
		self.parent=weakref.ref(parent)
		self.mag_factor = 1.1
		
		self.t3d_stack = []
		self.loadIdentity()
		
		self.mmode = 0
		self.debug = False
		
		self.basicmapping = False
		self.plane = 'xy'
		
		self.motiondull = 8.0
		
		self.mpressx = -1
		self.mpressy = -1

		self.allow_rotations = True
		self.allow_translations = True
		self.allow_phi_rotations = True

	
	def enable_emit_events(self,val=True):
		#print "set emit events to",val
		self.emit_events = val
	def is_emitting(self): return self.emit_events	
		
	def get_emit_signals_and_connections(self):
		return  {"apply_rotation":self.apply_rotation,"apply_translation":self.apply_translation,"scale_delta":self.scale_delta}
		
	def set_plane(self,plane='xy'):
		'''
		plane should by xy,yx,xz,zx,yz, or zy. It should also be a string
		'''
		self.plane = plane
	
	def allow_camera_rotations(self,bool=True):
		self.allow_rotations = bool
		
	def enable_camera_translations(self,val):
		self.allow_translations = val
		
	def loadIdentity(self):
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
		
		self.allow_z_mouse_trans = True
		
		t3d = Transform()
		t3d.to_identity()
		self.t3d_stack.append(t3d)
	
	def undoScale(self):
		glScalef(1.0/self.scale,1.0/self.scale,1.0/self.scale)
			
	
	def undoRot(self):
		rot = self.t3d_stack[len(self.t3d_stack)-1].get_rotation()
		if ( self.allow_rotations ):
			glRotate(-float(rot["az"]),0,0,1)
			glRotate(-float(rot["alt"]),1,0,0)
			glRotate(-float(rot["phi"]),0,0,1)
		
	
	def translate_only(self):
		glTranslate(self.cam_x, self.cam_y, self.cam_z)
	
	def position(self,norot=False):
		# position the camera, regualar OpenGL movement.
		if (self.debug):
			print "Camera translational position",self.cam_x,self.cam_y,self.cam_z
		glTranslate(self.cam_x, self.cam_y, self.cam_z)
		
		if ( self.allow_rotations and not norot):
			rot = self.t3d_stack[len(self.t3d_stack)-1].get_rotation("eman")
			if (self.debug):
				print "Camera rotation ",float(rot["phi"]),float(rot["alt"]),float(rot["az"])
			glRotate(float(rot["phi"]),0,0,1)
			glRotate(float(rot["alt"]),1,0,0)
			glRotate(float(rot["az"]),0,0,1)
		
		if (self.debug):
			print "Camera scale ",self.scale
		# here is where zoom is applied
		glScale(self.scale,self.scale,self.scale)
		
	def scale_event(self,delta):
		self.scale_delta(delta)
		if self.emit_events:self.parent().emit(QtCore.SIGNAL("scale_delta"),delta)
		
	def scale_delta(self,delta):
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
			self.set_cam_z(0)
		else:
			print 'Error, the axis (%s) specified is unknown. No action was taken' %axis
	
	def set_cam_z(self,z):
		self.cam_z = self.default_z + z
		
	def set_cam_y(self,y):
		self.cam_y = self.default_y + y
		
	def set_cam_x(self,x):
		self.cam_x = self.default_x + x

	def motion_rotate(self,x,y,fac=1.0):
		# this function implements mouse interactive rotation
		# [x,y] is the vector generating by the mouse movement (in the plane of the screen)
		# Rotation occurs about the vector 90 degrees to [x,y,0]
		# The amount of rotation is linealy proportional to the length of [x,y]
		
		if ( x == 0 and y == 0): return
		
		if self.allow_phi_rotations:
			theta = atan2(-y,x)

			plane = self.plane
			if ( plane == 'xy' ):
				rotaxis_x = sin(theta)
				rotaxis_y = cos(theta)
				rotaxis_z = 0
			elif ( plane == 'yx' ):
				rotaxis_x = -sin(theta)
				rotaxis_y = cos(theta)
				rotaxis_z = 0
			elif ( plane == 'xz' ):
				rotaxis_x = sin(theta)
				rotaxis_y = 0
				rotaxis_z = cos(theta)
			elif ( plane == 'zx' ):
				rotaxis_x = sin(theta)
				rotaxis_y = 0
				rotaxis_z = -cos(theta)
			elif ( plane == 'yz' ):
				rotaxis_x = 0
				rotaxis_y = cos(theta)
				rotaxis_z = -sin(theta)
			elif ( plane == 'zy' ):
				rotaxis_x = 0
				rotaxis_y = cos(theta)
				rotaxis_z = sin(theta)
			
			length = sqrt(x*x + y*y)
			# motiondull is a magic number - things rotate more if they are closer and slower if they are far away in this appproach
			# This magic number could be overcome using a strategy based on the results of get_render_dims_at_depth
			angle = fac*length/self.motiondull*pi
			
			t3d = Transform()
			quaternion = {}
			quaternion["omega"] = angle
			quaternion["n1"] = rotaxis_x
			quaternion["n2"] = rotaxis_y
			quaternion["n3"] = rotaxis_z
			quaternion["type"] = "spin"
			t3d.set_params(quaternion)
			if self.emit_events: 
				self.parent().emit(QtCore.SIGNAL("apply_rotation"),t3d)
			
			self.t3d_stack[-1] = t3d*self.t3d_stack[-1]
		else :
			# if az is fixed then we rotate in alt/az space, not with quaternions
			t3d = self.t3d_stack[-1]
			p = t3d.get_params("eman")
			p["alt"] = p["alt"] + fac*y/self.motiondull*pi
			if p["alt"]<0 : p["alt"]=0
			p["az"]  = p["az"] -  fac*x/self.motiondull*pi
			p["phi"] = 180.0
			t3d.set_params(p)
			
			if self.emit_events: print "Warning: no events emitted in fixed phi mode"
		
		#if not self.allow_phi_rotations:
			#p = t3d.get_params("eman")
			#p["phi"] = 0
			#t3d.set_params(p)
	
		
	def apply_rotation(self,t3d):
		self.t3d_stack[-1] = t3d*self.t3d_stack[-1]
		
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
	
	def mousePressEvent(self, event):
		self.mpressx = event.x()
		self.mpressy = event.y()
		if event.button()==Qt.LeftButton and self.allow_rotations:
			if self.mmode==0:
				# this is just a way of duplicating the last copy
				tmp =self.t3d_stack.pop()
				t3d = Transform(tmp)
				self.t3d_stack.append(tmp)
				self.t3d_stack.append(t3d)
		
	def mouseMoveEvent(self, event):
		if event.buttons()&Qt.LeftButton and self.allow_rotations:
			if self.mmode==0:
				#if event.modifiers() == Qt.ControlModifier:
					#self.motion_translate(event.x()-self.mpressx, self.mpressy - event.y())
				#else:
				self.motion_rotate(self.mpressx - event.x(), self.mpressy - event.y(),sqrt(1.0/self.scale))
				
				self.mpressx = event.x()
				self.mpressy = event.y()
				return True
		elif self.mmode==0:
			if self.allow_translations:
				if event.buttons()&Qt.RightButton and event.modifiers()&Qt.ShiftModifier and self.allow_z_mouse_trans:
					
						self.motion_translate_z_only(self.mpressx, self.mpressy,event)
							
						self.mpressx = event.x()
						self.mpressy = event.y()
						return True
				elif event.buttons()&Qt.RightButton or (event.buttons()&Qt.LeftButton and not self.allow_rotations):
					if self.mmode==0:
						self.motion_translateLA(self.mpressx, self.mpressy,event)
							
						self.mpressx = event.x()
						self.mpressy = event.y()
						return True
				
		return False
	
	def mouseReleaseEvent(self, event):
			
		if event.button()==Qt.LeftButton:
			if self.mmode==0:
				return False
		elif event.button()==Qt.RightButton:
			if self.mmode==0:
				return False
			
	def wheelEvent(self, event):
		self.scale_event(event.delta())
		return True
	
	def motion_translate_z_only(self,prev_x,prev_y,event):
		if (self.basicmapping == False):
			[dx,dy] = self.parent().eye_coords_dif(prev_x,viewport_height()-prev_y,event.x(),viewport_height()-event.y())
		else:
			print "Camera2 (object).basicmapping==True"
			[dx,dy] = [event.x()-prev_x,prev_y-event.y()]

		d = abs(dx) + abs(dy)
		if dy > 0: d = -d 
		self.cam_z += d
		v = (0,0,d)
			
		if self.emit_events: 
			#print "emitting applyt translation"
			self.parent().emit(QtCore.SIGNAL("apply_translation"),v)
	
	def motion_translateLA(self,prev_x,prev_y,event):
		if (self.basicmapping == False):
			[dx,dy] = self.parent().eye_coords_dif(prev_x,viewport_height()-prev_y,event.x(),viewport_height()-event.y())
		else:
			print "Camera2 (object).basicmapping==True"
			[dx,dy] = [event.x()-prev_x,prev_y-event.y()]

		#[wx2,wy2,wz2] = self.parent.eyeCoords(event.x(),self.parent.parentHeight()-event.y())
		#[wx2,wy2,wz2] =  self.parent.mouseViewportMovement(event.x(),self.parent.parentHeight()-event.y(),wx1,wy1,wz1,zprime)
		#self.parent.mouseViewportMovement(1,2,3,4)
		#[wx1,wy1] = self.parent.mouseinwin(prev_x,self.parent.parentHeight()-prev_y)
		#[wx2,wy2] = self.parent.mouseinwin(event.x(),self.parent.parentHeight()-event.y())
		#self.cam_x += dx
		#self.cam_y += dy

		plane = self.plane
		if ( plane == 'xy' ):
			self.cam_x += dx
			self.cam_y += dy
			v = (dx,dy,0)
		elif ( plane == 'yx' ):
			self.cam_x -= dx
			self.cam_y += dy
			v = (-dx,dy,0)
		elif ( plane == 'xz' ):
			self.cam_x += dx
			self.cam_z -= dy
			v = (dx,-dy,0)
		elif ( plane == 'zx' ):
			self.cam_x += dx
			self.cam_z += dy
			v = (dx,0,dy)
		elif ( plane == 'yz' ):
			self.cam_y += dy
			self.cam_z -= dx
			v = (0,dy,-dx)
		elif ( plane == 'zy' ):
			self.cam_y += dy
			self.cam_z += dx
			v = (0,dy,dx)
			
		if self.emit_events: 
			#print "emitting applyt translation"
			self.parent().emit(QtCore.SIGNAL("apply_translation"),v)
	
	def explicit_translate(self,x,y,z):
		
		self.cam_x += x
		self.cam_y += y
		self.cam_z += z
		
		if self.emit_events: self.parent().emit(QtCore.SIGNAL("apply_translation"),(x,y,z))
			
	def apply_translation(self,v):
		self.cam_x += v[0]
		self.cam_y += v[1]
		self.cam_z += v[2]