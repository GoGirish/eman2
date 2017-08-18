class ApplyTransform:
	def __init__(self,transform):
		self.transform = transform

	def __call__(self,emdata):
		emdata.transform(self.transform)


class ApplyAttribute:
	def __init__(self,attribute,value):
		self.attribute = attribute
		self.value = value

	def __call__(self,emdata):
		emdata.set_attr(self.attribute,self.value)


class ApplyProcessor:
	def __init__(self,processor="",processor_args={}):
		self.processor = processor
		self.processor_args = processor_args

	def __call__(self,data):
		data.process_inplace(self.processor,self.processor_args)
