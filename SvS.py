#!/usr/bin/env jython

CVS_ID = '$Id: SvS.py,v 1.1 2002/01/25 16:36:01 zooko Exp $'
import path_fix
version = (1, 0)
verstr = '.'.join(map(str, version))

import java
from java.lang import *
from java.awt import *
from java.awt.event import *
from java.awt.geom import *
from javax.swing import *
from javax.swing.text import *

from java.awt.image import ImageObserver # debug

import math
import operator
import time
import traceback

import GamePieces
import Game
import HexBoard
import Images
from util import *

true = 1
false = 0

class SvS(JFrame, MouseListener, KeyListener, Runnable):
	def __init__(self, boardwidth=16, boardheight=12, randseed=None):
		JFrame.__init__(self, 'Oneiromancer\'s Conundrum  [Version: %s]' % verstr)
		if randseed == None:
			randseed = int(time.time())
		print "randseed: ", randseed
		self.randseed = randseed
		self.boardwidth=boardwidth
		self.boardheight=boardheight

		# Where Wizards start:
		self.homecoords = (
			(0, self.boardheight-1,),
			(self.boardwidth-1, 0,),
			)

		SwingUtilities.invokeLater(self)

	def run(self):
		randgen.seed(self.randseed)
		self.hb = HexBoard.HexBoard(cxoffset=10, cyoffset=10+(self.boardheight-1)*30*2*0.75, scale=30)
		self.selecteditem = None
		self.creatures = [] # all extant creatures, living and dead
		self.turnmanager = Game.TurnManager(self.creatures)
		#self.turnmanager.register_regular_eot_event(self.grow_a_tree)
		self.turnmanager.register_regular_bot_event(self.select_next_creature)

		HSLOP=30
		VSLOP=60
		self.setContentPane(self.hb)
		self.setSize(int(HSLOP + ((self.boardwidth+0.5)*self.hb.w)), int(VSLOP + (self.boardheight*self.hb.h*0.75)))
		self.init_locations()

		self.setVisible(true)
		self.init_creatures()
		self.turnmanager.begin_turn()

		for mlmeth in dir(MouseListener):
			setattr(self.__class__, mlmeth, null_func)
		setattr(self.__class__, 'mousePressed', self._mousePressed)

		for klmeth in dir(KeyListener):
			setattr(self.__class__, klmeth, null_func)
		setattr(self.__class__, 'keyTyped', self._keyTyped)

		self.addMouseListener(self)
		self.addKeyListener(self)
		
	def init_locations(self):
		for hx in range(self.boardwidth):
			for hy in range(self.boardheight):
				q = HexBoard.Hex(self.hb, hx, hy)
				if (hx, hy) in self.homecoords:
					# Don't place a Stone in a home hex.
					continue

				if min(map(lambda homecoord, thiscoord=(hx, hy) : HexBoard.distance(homecoord, thiscoord),
						   self.homecoords)) < 4:
					# If we're close to a Wizard's home hex, there are few rocks.
					probability = 0.2
				else:
					# Everywhere else, there are many rocks:
					probability = 0.8

				# Create a Stone with a certain probability:
				probable_apply(probability, GamePieces.Stone, (self, q))

	def init_creatures(self):
		for homecoord in self.homecoords:
			Wizard(self, self.hb.get(homecoord))

	def select_next_creature(self):
		"""
		Selects the next creature with action points.
		"""
		if (self.selecteditem is not None) and (isinstance(self.selecteditem, GamePieces.Creature)):
			i = self.creatures.index(self.selecteditem)
			self.selecteditem.unselect()
			cs = self.creatures[i+1:] + self.creatures[:i+1]
		else:
			cs = self.creatures

		for c in cs:
			if c.actpleft > 0:
				c.select()
				return

	def _DEBUG_shortest_path_mousePressed(self, e):
		pt = e.getPoint()
		hbpt = self.hb.getLocation()
		rppt = self.getRootPane().getLocation()
		pt.translate(hbpt.x - rppt.x, hbpt.y - rppt.y)
		hex = self.hb.pick_hex(pt)
		if self.selecteditem is None:
			print "Selecting hex:", hex
			self.selecteditem = hex
			self.hb.unhighlight_all()
			hex.highlight()
		else:
			# Highlight the path:
			coords = HexBoard.shortest_path((self.selecteditem.hx, self.selecteditem.hy,),
											(hex.hx, hex.hy,),
											30
											)
			print "[Debug:]", coords
			if coords[-1] is None:
				coords = coords[:-1]
			[self.hb.get(coord).highlight() for coord in coords]
			self.selecteditem = None
		self.repaint()
	
	def _REAL_mousePressed(self, e):
		pt = e.getPoint()
		hbpt = self.hb.getLocation()
		rppt = self.getRootPane().getLocation()
		pt.translate(hbpt.x - rppt.x, hbpt.y - rppt.y)
		hex = self.hb.pick_hex(pt)
		if SwingUtilities.isRightMouseButton(e):
			if self.selecteditem is not None:
				# cancel of current selection by right-click
				self.selecteditem.unselect()
		else:
			if self.selecteditem is not None:
				# act-request
				self.selecteditem.user_act(hex)
			else:
				if (hex is not None) and (not hex.is_empty()):
					# mousepress
					hex.items[-1].mouse_pressed()

	_mousePressed = _REAL_mousePressed

	def _keyTyped(self, e):
		c = e.getKeyChar()
		# keystrokes when there is or is not a current selected item
		if c == 'n':
			self.select_next_creature()

		# keystrokes when there is a current selected item
		if self.selecteditem is None:
			return
		if c == 'w':
			self.selecteditem.user_act(self.selecteditem.hex.get_nw())
		elif c == 'e':
			self.selecteditem.user_act(self.selecteditem.hex.get_ne())
		elif c == 'a':
			self.selecteditem.user_act(self.selecteditem.hex.get_w())
		elif c == 'd':
			self.selecteditem.user_act(self.selecteditem.hex.get_e())
		elif c == 'z':
			self.selecteditem.user_act(self.selecteditem.hex.get_sw())
		elif c == 'x':
			self.selecteditem.user_act(self.selecteditem.hex.get_se())
		elif c == 's':
			self.selecteditem.user_act(self.selecteditem.hex)
		elif c == ' ':
			self.selecteditem.pass()
		elif c == 'u':
			self.selecteditem.unselect()

class Wizard(GamePieces.Creature):
	def __init__(self, game, hex):
		GamePieces.Creature.__init__(self, game, hex, 20, 3, 1, 1)

