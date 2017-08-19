from libpyEMData2 import EMData
from libpyUtils2 import EMUtil

from EMAN2 import get_header


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
