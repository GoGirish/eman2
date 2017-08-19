class EMMXDataCache:
	"""
	Base class for EMMXDataCaches
	"""
	def __init__(self):
		self.excluded_list = []  # a list of excluded idxs, used when saving the data to disk
