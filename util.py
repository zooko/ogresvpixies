#!/usr/bin/env python

CVS_ID = '$Id: util.py,v 1.1 2002/01/25 16:36:01 zooko Exp $'

from types import *
import random
from UserDict import UserDict

class Trivial:
    """
    Occasionally it's nice to have this trivial class.
    """
    pass

class AttributeMap (UserDict):
	def __getattr__(self, name):
		return name == 'data' and self.__dict__['data'] or self.__dict__['data'].get(name)
	def __setattr__(self, name, value):
		if name == 'data':
			self.__dict__[name] = value
		else:
			self.__dict__['data'][name] = value

randgen = random.Random()

rand_norm = randgen.random

def rand_float(X):
	return randgen.random()*X

def rand_int(X):
	return int(rand_float(X))

def probable_apply(probability, func, args=(), kwargs=None):
	"""
	probable_apply(probability, func, args=(), kwargs=None) -> (called, result)

	There is a chance equal to probability that func will be called with args and kwargs.
	The return value is a 2-tuple; the first argument is a boolean indicating whether or
	not the function was called.  The second argument is the return value of the function,
	or None if not called.

	probability is a float between 0.0 and 1.0.
	"""
	assert is_type(probability, FloatType) and 0.0 <= probability <= 1.0, "Bad probability: %s" % `probability`

	kwargs = kwargs or {}
	if rand_norm() < probability:
		return (1, apply(func, args, kwargs))
	else:
		return (0, None)

def dX(X):
	return rand_int(X)+1

def d6():
	return dX(6)

def rand_rotate(list):
	i = rand_int(len(list))
	return list[i:] + list[:i]

def is_type(object, klass):
	"""
	is_type is functionally a superset of the built-in isinstance.

	If type(object) is klass, return a true value.
	Else, if type(object) is InstanceType and type(klass) is ClassType return isinstance(object, klass).
	Else, if type(klass) is a sequence, and is_type returns true for any element in klass, return true.
	Else, return a false value.

	Examples:
	is_type(42, IntegerType) -> true
	is_type(myhb, HexBoard) -> true
	is_type(None, HexBoard) -> false

	# Passing a sequence as klass:
	is_type([], (TupleType, ListType)) -> true
	is_type(None, (NoneType, MyClass)) -> true
	"""
	if type(object) is klass:
		return 1
	elif type(object) is InstanceType and type(klass) is ClassType:
		return isinstance(object, klass)
	elif type(klass) in (TupleType, ListType):
		return len(filter(lambda k, o=object : is_type(o, k),
						  klass)) > 0
	else:
		return 0

# A useful klass parameter for is_type:
SequenceTypes = (TupleType, ListType)

def null_func(*args, **kwargs):
	"""A null function, takes any kind of arguments and does nothing."""
	pass

def unpack_rect(r):
	"""
	Pragmatically the opposite of Rectangle(a, b, c, d).
	"""
	return r.x, r.y, r.width, r.height


