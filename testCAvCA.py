#!/usr/bin/env jython

CVS_ID = '$Id: testCAvCA.py,v 1.1 2002/02/09 22:46:13 zooko Exp $'

import path_fix # hack for nathan's box

import util
import HexBoard
import Game
import CAvCAPieces
import CAvCA

os = []

class B:
	def __call__(self, randseed=None, os=os):
		reload(util)
		reload(HexBoard)
		reload(Game)
		reload(CAvCAPieces)
		reload(CAvCA)
		os.append(CAvCA.CAvCA(randseed=randseed))

	def __repr__(self, os=os, randseed=None):
		self.__call__(randseed=randseed)
		return ''

b=B()

class D:
	def __call__(self, os=os):
		os[0].dispose()
		del os[0]

	def __repr__(self, os=os):
		self.__call__()
		return ''

d=D()

class R:
	def __init__(self, randseed=None):
		self.randseed=randseed

	def __call__(self, randseed=None, os=os, b=b, d=d):
		if randseed is None:
			randseed = self.randseed
		try:
			d()
		except:
			pass
		b(randseed=randseed)

	def __repr__(self, randseed=None, os=os, b=b, d=d):
		self.__call__(randseed=randseed)
		return ''

randseed = None
r=R(randseed=randseed)

r()
