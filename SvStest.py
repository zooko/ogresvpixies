#!/usr/bin/env jython

CVS_ID = '$Id: SvStest.py,v 1.1 2002/01/25 16:36:01 zooko Exp $'

import path_fix # hack for nathan's box

import HexBoard
import Game
import GamePieces
import Images
import util
import SvS
import GUITools

os = []

class Command:
	def __init__(self, func, args=(), **kw):
		self.func = func
		self.args = args
		self.kw = kw
	def __call__(self):
		return apply(self.func, self.args, self.kw)
	def __repr__(self):
		print 'Running command:', self.func, self.args, self.kw
		self()
		print 'Finished command:', self.func, self.args, self.kw
		return ''

def _b_func(randseed):
	reload(util)
	reload(Images)
	reload(Game)
	reload(GamePieces)
	reload(HexBoard)
	reload(SvS)
	reload(GUITools)
	os.append(SvS.SvS(randseed=randseed))

def _d_func():
	os[0].dispose()
	del os[0]

def _r_func(randseed):
	try:
		d()
	except:
		pass
	b(randseed=randseed)

randseed = None

b = Command(_b_func, randseed=randseed)
d = Command(_d_func)
r = Command(_r_func, randseed=randseed)

if __name__ == '__main__':
	import code

	scope = {}
	names = []
	for name, thing in globals().items():
		if isinstance(thing, Command):
			names.append(name)

	names.sort()
	banner = 'Commands: ' + ', '.join(names)

	del name, thing, names
	scope.update(globals())

	code.interact(local=scope, banner=banner)
