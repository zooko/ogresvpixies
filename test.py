#!/usr/bin/env jython

CVS_ID = '$Id: test.py,v 1.1 2002/01/25 16:36:01 zooko Exp $'

import path_fix # hack for nathan's box

import HexBoard
import GamePieces
import OvP
import Game
import Images
import util

os = []

class B:
	def __call__(self, randseed=None, os=os):
		reload(HexBoard)
		reload(GamePieces)
		reload(OvP)
		reload(Game)
		reload(Images)
		reload(util)
		os.append(OvP.OvP(randseed=randseed))

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
