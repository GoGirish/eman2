import os
from libpyEMData2 import EMData
from libpyGeometry2 import Region
from libpyUtils2 import EMUtil

from EMAN2 import get_header, gimme_image_dimensions3D
from EMAN2db import db_check_dict, db_open_dict
from PyQt4 import QtGui
from PyQt4.QtCore import Qt


class EMMXDataCache:
	"""
	Base class for EMMXDataCaches
	"""
	def __init__(self):
		self.excluded_list = []  # a list of excluded idxs, used when saving the data to disk


class EMLightWeightParticleCache(EMMXDataCache):
	"""
	A light weight particle cache is exactly that and more. 
	Initialize it with a list of filenames and particle indices
	corresponding to the particles that you want to view. 
	So the calling function doesn't do any image reading, you just tell this
	thing what will need to be (or not) read.

	Primary data is basically a list like this: 
	[[filename, idx, [func1,func2,...]], [filename, idx2, [func1,func2,...]],...]
	the filename and idx variables should be obvious, 
	however the extra list contains functions that take an EMData as the argument -
	I used this, for example, for assignint attributes to images once they are in memory, 
	and for transforming them, etc.

	A big advantage of this cache is that it only displays the images that are asked for. 
	Additionally, it has a maximum cache size,
	and refocuses the cache when asked for an image outside its current index bounds. 
	This makes this cache only suitable for linear access schemes, not random.

	"""
	@staticmethod
	def from_file(file_name):
		"""
		If this was C++ this would be the constructor for this class that took a single file name
		@param file_name the name of a particle stack file
		"""

		n = EMUtil.get_image_count(file_name)
		data = [[file_name,i,[]] for i in xrange(n)]

		return EMLightWeightParticleCache(data,len(data))

	def __init__(self,data,cache_max=2048):
		"""
		@param data list of lists - lists in in the list are of the form [image_name, idx, [list of functions that take an EMData as the first argument]]
		@param cache_max the maximum number of stored images - you might have to shorten this if you have very large images
		"""
		EMMXDataCache.__init__(self)
		self.data = data
		self.cache_start = 0
		self.cache_max = cache_max
		self.cache = [None for i in range(self.cache_max)]
		self.xsize = None
		self.ysize = None
		self.zsize = None
		self.header_keys = None
		# set stuff
		self.visible_sets = []
		self.sets = {}

	def __len__(self):
		"""
		support for len
		"""
		return len(self.data)

	def is_complex(self): return False

	def delete_box(self,idx):
		"""
		@ must return a value = 1 indicates the box is permanently gone, 0 indicates the class is happy to do nothing
		and let the calling program display the deleted box differently
		"""
		return 0

	def get_xsize(self):
		"""
		Get the get_xsize of the particles. Assumes all particle have the same size, which is potentially flawed
		"""
		if self.xsize is None:
			image = self[self.cache_start]
			self.xsize = image.get_xsize()

		return self.xsize

	def get_ysize(self):
		"""
		Get the get_ysize of the particles. Assumes all particle have the same size, which is potentially flawed
		"""
		if self.ysize is None:
			image = self[self.cache_start]
			self.ysize = image.get_ysize()

		return self.ysize

	def get_zsize(self):
		"""
		Get the get_ysize of the particles. Assumes all particle have the same size, which is potentially flawed
		"""
		if self.zsize is None:
			image = self[self.cache_start]
			self.zsize = image.get_zsize()

		return self.zsize

	def get_image_header(self,idx):
		"""
		Gets the header of the ith particle. Does not read the full image into memory if it's not stored, instead
		just reading the header and returning it. This can give significant speeds ups where only headers are needed,
		i.e. e2eulerxplor
		"""
#		return self[idx].get_attr_dict()
		adj_idx = idx-self.cache_start
		image = self.cache[adj_idx]
		if image is None:
			data = self.data[idx]
			h = get_header(data[0],data[1])
			return h
			#e.read_image(data[0],data[1],True)
			#return e.get_attr_dict()
		else:return image.get_attr_dict()

	def get_image_header_keys(self):
		"""
		Gets the keys in the header of the first image
		"""
		if self.header_keys is None:
			self.header_keys = self.get_image_header(self.cache_start).keys()
		return self.header_keys

	def refocus_cache(self,new_focus):
		"""
		Called internally to refocus the cache on a new focal point.
		@param new_focus the value at which the current cache failed 
		- i.e. the first value that was beyond the current cache limits
		"""
		new_cache_start = new_focus-self.cache_max/2
		# Don't let cache start go negative; it will break.
		if new_cache_start < 0:
			new_cache_start = 0
		if new_cache_start < self.cache_start < new_cache_start + self.cache_max:
			overlap = new_cache_start + self.cache_max - self.cache_start
			cache = [None for i in range(self.cache_max-overlap)]
			cache.extend(self.cache[0:overlap])
			self.cache = cache
		elif self.cache_start < new_cache_start < self.cache_start + self.cache_max:
			cache = self.cache[new_cache_start:self.cache_start+self.cache_max]
			overlap =self.cache_max - ( new_cache_start - self.cache_start)
			cache = [None for i in range(self.cache_max-overlap)]
			cache.extend(self.cache[0:overlap])
			self.cache = cache
		else:
			self.cache = [None for i in range(self.cache_max)]

		self.cache_start = new_cache_start

	def __getitem__(self,idx):
		"""
		operator[] support - the main interface
		"""
		if idx < self.cache_start or idx > self.cache_start+self.cache_max:
			self.refocus_cache(idx)

		adj_idx = idx-self.cache_start
		try: image = self.cache[adj_idx]
		except: image=None
		if image is None:
			try: a = self.__load_item(idx,adj_idx)
			except: a=None
			return a
		else: return image

	def __load_item(self,idx,adj_idx):
		"""
		Work horse function for reading an image and applying any of the supplied functions
		"""
		data = self.data[idx]

		try:
			a = EMData(data[0],data[1])
			if a is None: raise Exception
		except :
			for i in range(10):
				try:
					a=EMData(data[0],i)
					if a is None: raise Exception
				except: continue
				break
			a.to_zero()

		for func in data[2]: func(a)
		self.cache[adj_idx] = a
		return a

	def on_idle(self):
		"""
		call this to load unloaded images in the cache
		This needs to be rethought, maybe use a thread?
		"""
		for idx,i in enumerate(self.cache):
			if i is None:
				# only does one at a time
				self.__load_item(idx,idx+self.cache_start)
				return

	def is_3d(self): return False


class EMDataListCache(EMMXDataCache):
	"""
	This class became semi-redundant after the introduction of the EMLightWeightParticleCache, 
	however it is still used
	as the primary container for lists of the form [EMData,EMData,EMData,EMData,...].

	You can also initialize this object with a filename of an image matrix. 
	Then you can treat it as though it's a list of EMData objects. For example,

	data = EMDataListCache("particles.hdf")
	image1 = data[1] # just treat it like a list

	for i in data: i.write_image("test.hdf",-1) # iterable and enumerable

	"""
	LIST_MODE = 'list_mode'
	FILE_MODE = 'file_mode'
	def __init__(self, obj, cache_size=256, start_idx=0, soft_delete=False):
		EMMXDataCache.__init__(self)
		#DB = EMAN2db.EMAN2DB.open_db(".")
		self.xsize = -1
		self.ysize = -1
		self.keys = None
		self.current_set = None
		self.sets = {}
		self.set_init_flag = {} # sets stored on disk need an initialization flag, so action is only ever taken if the user chooses the set
		self.visible_sets = [] # stores the current sets, if there are more than one
		self.exclusions = []
		if isinstance(obj, list):
			# in list mode there is no real caching
			self.mode = EMDataListCache.LIST_MODE
			self.max_idx = len(obj)
			self.cache_size = self.max_idx
			self.images = obj
			self.start_idx = 0

		elif isinstance(obj, str):
			#print "file mode"
			self.mode = EMDataListCache.FILE_MODE
			if not os.path.exists(obj) and not db_check_dict(obj):
				print "error, the file you specified does not exist:",obj
				return
			self.file_name = obj
			self.max_idx = EMUtil.get_image_count(self.file_name)
			self.images = {}
			if self.max_idx < cache_size:
				self.cache_size = self.max_idx
			else:
				self.cache_size = cache_size
			self.start_idx = start_idx - self.cache_size/2
			if self.start_idx < 0: self.start_idx = 0

			self.__refresh_cache()
		else:
			print "the object used to construct the EMDataListCache is not a string (filename) or a list (of EMData objects). Can't proceed"
			return

#		self.__init_sets()

		self.current_iter = 0 # For iteration support
		self.soft_delete = soft_delete # toggle to prevent permanent Deletion of particles
		self.image_width = -1
		self.image_height = -1

	def __del__(self):
		pass

	def get_xsize(self):
		if self.xsize == -1:

			if self.mode == EMDataListCache.FILE_MODE:
				for i in self.images:
					try:
						if self.images[i] is not None:
							self.xsize = self.images[i].get_xsize()
							break
					except: pass

			elif self.mode == EMDataListCache.LIST_MODE:
				for i in self.images:
					try:
						self.xsize = i.get_xsize()
						break
					except: pass

		return self.xsize

	def get_ysize(self):
		if self.ysize == -1:

			if self.mode == EMDataListCache.FILE_MODE:
				for i in self.images:
					try:
						if self.images[i] is not None:
							self.ysize = self.images[i].get_ysize()
							break
					except: pass

			elif self.mode == EMDataListCache.LIST_MODE:
				for i in self.images:
					try:
						self.ysize = i.get_ysize()
						break
					except: pass
		return self.ysize

	def get_zsize(self): return 1

	def is_complex(self): return False

	def get_image_header(self,idx):
		if self.mode == EMDataListCache.FILE_MODE:
			if len(self.file_name) > 3 and self.file_name[:4] == "bdb:":
				db = db_open_dict(self.file_name)
				return db.get_header(idx)
			else:
				e = EMData()
				e.read_image(self.file_name,idx,True)
				return e.get_attr_dict()
		elif self.mode == EMDataListCache.LIST_MODE:
			return self.images[idx].get_attr_dict()

	def get_image_header_keys(self):
		if self.keys is None:
			if self.mode == EMDataListCache.FILE_MODE:
				for i in self.images:
					try:
						if self.images[i] is not None:
							self.keys = self.images[i].get_attr_dict().keys()
							break
					except: pass

			elif self.mode == EMDataListCache.LIST_MODE:
				for i in self.images:
					try:
						 self.keys = i.get_attr_dict().keys()
						 break
					except: pass

		return self.keys

	def on_idle(self):
		"""
		call this to load unloaded images in the cache
		"""
		for idx,i in enumerate(self.cache):
			if i is None:
				# only does one at a time
				self.__load_item(idx,idx+self.cache_start)
				return

	def delete_box(self,idx):
		"""
		@ must return a value = 1 indicates the box is permanently gone, 
		0 indicates the class is happy to do nothing
		and let the calling program display the deleted box differently
		"""
		if self.mode == EMDataListCache.LIST_MODE and not self.soft_delete:
			# we can actually delete the emdata object
			image = self.images.pop(idx)
			self.max_idx = len(self.images)
			self.cache_size = self.max_idx
			return 1
		elif self.mode == EMDataListCache.FILE_MODE or self.soft_delete:
			return 0

	def get_max_idx(self):
		""" Get the maximum image index  """
		return self.max_idx

	def get_num_images(self):
		""" Get the number of images currently cached """
		return len(self.images)

	def set_cache_size(self,cache_size,refresh=False):
		""" Set the cache size. May cause the cache to be refreshed, which could take a few moments """
		if self.mode != EMDataListCache.LIST_MODE:
			if cache_size > self.max_idx: self.cache_size = self.max_idx
			else: self.cache_size = cache_size
			self.start_idx = self.start_idx - self.cache_size/2
			if refresh: self.__refresh_cache()
		else:
			if self.cache_size != self.max_idx:
				print "error, in list mode the cache size is always equal to the max idx"
				return
	
	def set_start_idx(self,start_idx,refresh=True):
		""" Set the starting index of the cache, """
		self.start_idx = start_idx
		if refresh: self.__refresh_cache()

	def __refresh_cache(self):
		app = QtGui.QApplication.instance()
		app.setOverrideCursor(Qt.BusyCursor)

		try:
			cache = {}
			i = self.start_idx
			for i in range(self.start_idx,self.start_idx+self.cache_size,1):
				if i != 0:
					idx = i % self.max_idx
				else: idx = 0
				try:
					cache[idx] = self.images[idx]
				except:
					try:
						if self.mode ==  EMDataListCache.FILE_MODE:
							a = EMData()
							a.read_image(self.file_name,idx)
#							if idx in self.exclusions: a["excluded"] = True
							cache[idx] = a
							if self.current_set is not None:
								sets = []
								for set in self.current_set:

									if not hasattr(cache[idx],"mxset") and self.sets[set].count(idx) != 0:
										sets.append(set)
								if len(sets) != 0: cache[idx].mxset = sets
						else:
							print "data has been lost"
							raise
					except: print "couldn't access",idx,"the max idx was",self.max_idx,"i was",i,"start idx",self.start_idx,"cache size",self.cache_size,len(self.images)
				i += 1
			self.images = cache
		except:
			print "there was an error in cache regeneration. Suggest restarting"

		app.setOverrideCursor(Qt.ArrowCursor)

	def __getitem__(self,idx):

		i = 0
		if idx != 0: i = idx%self.max_idx
		try:
			return self.images[i]
		except:
			self.start_idx = i - self.cache_size/2
			if self.start_idx < 0: self.start_idx = 0
			#if self.start_idx < 0:
				#self.start_idx = self.start_idx % self.max_idx
			#elif self.start_idx+self.cache_size >= self.max_idx:
				#self.start_idx =  self.max_idx - self.cache_size/2 -1
			self.__refresh_cache()
			try:
				return self.images[i]
			except:
				print "error, couldn't get image",i,self.start_idx,self.max_idx,self.cache_size
				#for i in self.images:
					#print i,
				#print ''
	
	def __len__(self):
		return self.max_idx

	def __iter__(self):
		""" Iteration support """
		self.current_iter = 0
		return self

	def next(self):
		""" Iteration support """
		if self.current_iter >= self.max_idx:
			raise StopIteration
		else:
			self.current_iter += 1
			return self[self.current_iter-1]
	
	def on_idle(self):
		"""
		call this to load unloaded images in the cache, for example
		"""
		pass

	def is_3d(self): return False


class EM3DDataListCache(EMMXDataCache):
	"""
	A class that looks like a list to the outside world
	automated way of handling 3d images for the EMImageMXWidget

	"""
	def __init__(self,filename):
		EMMXDataCache.__init__(self)
		self.filename = filename
		self.nx, self.ny, self.nz = gimme_image_dimensions3D(filename)
		if self.nz == 1: raise RuntimeError("EM3DDataForMx class is only meant to be used with 3D images")
		self.keys = None
		self.header = None
		self.exclusions = []
		self.images = {}
		self.major_axis = "z"
		self.max_idx = self.nz

	def delete_box(self,idx):
		"""
		@ must return a value = 1 indicates the box is permanently gone, 
		0 indicates the class is happy to do nothing
		and let the calling program display the deleted box differently
		"""
		return 0

	def is_complex(self): return False

	def set_xyz(self,xyz):
		if xyz != self.major_axis:
			self.major_axis = xyz
			self.images = {}
			return True
		return False

	def get_xsize(self):
		return self.nx

	def get_ysize(self):
		return self.ny

	def get_zsize(self):
		return self.nz

	def get_image_header(self,idx):
		if self.header is None:
			image = self[self.nz/2]
			self.header = image.get_attr_dict()

		return self.header

	def get_image_header_keys(self):
		if self.keys is None:
			self.keys = self[0].get_attr_dict().keys()

		return self.keys

	def get_max_idx(self):
		""" Get the maximum image index  """
		return self.max_idx

	def get_num_images(self):
		""" Get the number of images currently cached """
		return self.max_idx

	def set_cache_size(self,cache_size,refresh=False):
		""" Set the cache size. May cause the cache to be refreshed, which could take a few moments """
		pass
#		if self.mode != EMDataListCache.LIST_MODE:
#			if cache_size > self.max_idx: self.cache_size = self.max_idx
#			else: self.cache_size = cache_size
#			self.start_idx = self.start_idx - self.cache_size/2
#			if refresh: self.__refresh_cache()
#		else:
#			if self.cache_size != self.max_idx:
#				print "error, in list mode the cache size is always equal to the max idx"
#				return
	
	def set_start_idx(self,start_idx,refresh=True):
		""" Set the starting index of the cache, """
		pass
#		self.start_idx = start_idx
#		if refresh: self.__refresh_cache()

	def __refresh_cache(self):
		pass

	def __getitem__(self,idx):
		if not self.images.has_key(idx):
			a = EMData()
			if self.major_axis == "z":
				r = Region(0,0,idx,self.nx,self.ny,1)
				a.read_image(self.filename,0,False,r)
			elif self.major_axis == "y":
				r = Region(0,idx,0,self.nx,1,self.nz)
				a.read_image(self.filename,0,False,r)
				a.set_size(self.nx,self.nz)
			elif self.major_axis == "x":
				r = Region(idx,0,0,1,self.ny,self.nz)
				a.read_image(self.filename,0,False,r)
				a.set_size(self.ny,self.nz)

			self.images[idx] = a

		return self.images[idx]

	def __len__(self):
		return self.max_idx

	def __iter__(self):
		""" Iteration support """
		self.current_iter = 0
		return self

	def next(self):
		""" Iteration support """
		if self.current_iter > self.max_idx:
			raise StopIteration
		else:
			self.current_iter += 1
			return self[self.current_iter-1]

	def on_idle(self):
		"""
		call this to load unloaded images in the cache, for example
		"""
		pass

	def is_3d(self): return True
