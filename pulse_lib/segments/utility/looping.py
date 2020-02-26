import numpy as np 
import copy

class loop_obj():
	"""object that initializes some standard fields that need to be there in a loop object"""
	def __init__(self):
		# little inspiration from qcodes parameter ...
		self.labels = list()
		self.units = list()
		self.axis = list()
		self.dtype = None
		self.setvals_set = False
		
	def add_data(self, data, axis = None, labels = None, units = None, setvals = None):
		'''
		add data to the loop object.
		data (array/np.ndarray) : n dimensional array with a regular shape (any allowed by numpy) of values you want to sweep
		axis (int/tuple<int>) : loop axis, if none is provided, a new loop axis is generated when the loop object is used in the pulse library.
		labels (str/tuple<str>) : name of the data that is swept. This will for example be used as an axis label
		units (str/tuple<str>) : unit of the sweep data
		setvals (array/np.ndarray) : if you want to display different things on the axis than the normal data point. When None, setvals is the same as the data varaible.
		'''
		self.data = np.asarray(data)
		self.dtype = self.data.dtype

		if axis is None:
			self.axis = [-1]*len(self.data.shape)
		elif type(axis) == int:
			self.axis = [axis]
		else:
			if len(axis) != len(self.data.shape):
				raise ValueError("Provided incorrect dimensions for the axis.")
			self.axis = axis
		
		if labels is None:
			self.labels = tuple()
		elif type(labels) == str:
			self.labels = (labels, )
		else:
			if len(labels) != len(self.data.shape):
				raise ValueError("Provided incorrect dimensions for the axis.")
			self.labels = labels

		if units is None:
			self.units = tuple()
		elif type(units) == str:
			self.units = (units, )
		else:
			if len(units) != len(self.data.shape):
				raise ValueError("Provided incorrect dimensions for the axis.")
			self.units = units

		if setvals is None:
			self.setvals = self.data
		else:
			setvals = np.asarray(setvals)
			if self.shape != setvals.shape:
				raise ValueError("setvals should have the same dimensions as the data dimensions.")
			self.setvals = setvals
			self.setvals_set = True

	def __len__(self):
		return len(self.data)

	@property
	def shape(self):
		return self.data.shape

	@property
	def ndim(self):
		return self.data.ndim

	def __getitem__(self, key):
		if self.ndim == 1:
			return self.data[key]
		else:
			partial = loop_obj()
			partial.labels =self.labels[1:] 
			partial.units = self.units[1:]
			partial.axis = self.axis[1:]
			partial.dtype = self.dtype
			partial.data = self.data[key]
			return partial

	def __add__(self, other):
		cpy = copy.copy(self)
		cpy.data += other
		return cpy
		
	def __mul__(self, other):
		cpy = copy.copy(self)
		cpy.data *= other
		return cpy

	def __sub__(self, other):
		cpy = copy.copy(self)
		cpy.data -= other
		return cpy
	def __truediv__(self, other):
		cpy = copy.copy(self)
		cpy.data += self.data/other
		return cpy

	def __copy__(self):
		cpy = loop_obj()
		cpy.labels = copy.copy(self.labels)
		cpy.units = copy.copy(self.units)
		cpy.axis = copy.copy(self.axis)
		cpy.dtype = copy.copy(self.dtype)

		if hasattr(self, 'data'):
			cpy.data= copy.copy(self.data)
		return cpy


class linspace(loop_obj):
	"""docstring for linspace"""
	def __init__(self, start, stop, n_steps = 50, name = None, unit = None, axis = -1, setvals = None):
		super().__init__()
		super().add_data(np.linspace(start, stop, n_steps), axis = axis, labels = name, units = unit, setvals= setvals)

class logspace(loop_obj):
	"""docstring for logspace"""
	def __init__(self, start, stop, n_steps = 50, name = None, unit = None, axis = -1, setvals = None):
		super().__init__()
		super().add_data(np.logspace(start, stop, n_steps), axis = axis, labels = name, units = unit, setvals= setvals)

class geomspace(loop_obj):
	"""docstring for geomspace"""
	def __init__(self, start, stop, n_steps = 50, name = None, unit = None, axis = -1, setvals = None):
		super().__init__()
		super().add_data(np.geomspace(start, stop, n_steps), axis = axis, labels = name, units = unit, setvals= setvals)
