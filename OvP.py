#!/usr/bin/env jython

# copyright 2002 the Brothers Wilcox
# <mailto:zooko@zooko.com>
# 
# This file is part of OvP.
# 
# OvP is open source software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
# 
# OvP is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License
# along with OvP; if not, write to zooko.com:
# <a mailto:zooko@zooko.com>
# 
# See the file COPYING or visit http://www.gnu.org/ for details.

# CVS:
__cvsid = '$Id: OvP.py,v 1.4 2002/01/30 14:27:40 zooko Exp $'

import path_fix

# standard Java modules
import java
from java.lang import *
from java.awt import *
from java.awt.event import *
from java.awt.geom import *
from javax.swing import *
from javax.swing.text import *

from java.awt.image import ImageObserver # debug

# standard Python modules
import math
import operator
import time
import traceback

# OvP modules
import HexBoard
from GamePieces import *
import Game
import Images
from util import *

true = 1
false = 0

version = (1, 2, 0)
verstr = '.'.join(map(str, version))
name = "Ogres vs. Cellular Automata"

NUM_STARTING_OGRES=2
NUM_STARTING_PIXIES=3
NUM_STARTING_TREES=32

class OvPHex(HexBoard.Hex):
	def __init__(self, hb, hx, hy, bordercolor=Color.green, bgcolor=Color.black):
		HexBoard.Hex.__init__(self, hb, hx, hy, bordercolor, bgcolor)
		self._nextnumneighbors = 0

	def is_center_of_broken_pixie_ring(hex):
		return (hex.is_empty() or hex.contains_only(Stone)) and \
			   (len(hex.get_adjacent_hexes()) == 6) and \
			   (((HexBoard.all_contain_a(hex.get_east_trio(), Tree)) and \
				 (HexBoard.all_are_empty(hex.get_west_trio()))) or \
				((HexBoard.all_contain_a(hex.get_west_trio(), Tree)) and \
				 (HexBoard.all_are_empty(hex.get_east_trio()))))

	def is_center_of_pixie_ring(hex):
		return (hex.is_empty() or hex.contains_only(Stone)) and \
			   (len(hex.get_adjacent_hexes()) == 6) and \
			   HexBoard.all_contain_a(hex.get_adjacent_hexes(), Tree)

class OvP(JFrame, MouseListener, KeyListener, Runnable):
	def __init__(self, boardwidth=16, boardheight=12, randseed=None):
		JFrame.__init__(self, name + " v" + verstr)
		if randseed == None:
			randseed = int(time.time())
		print "randseed: ", randseed
		self.randseed = randseed
		self.boardwidth=boardwidth
		self.boardheight=boardheight
		SwingUtilities.invokeLater(self)

	def run(self):
		randgen.seed(self.randseed)
		self.hb = HexBoard.HexBoard(cxoffset=10, cyoffset=10+(self.boardheight-1)*30*2*0.75, scale=30)
		self.selecteditem = None
		self.creatures = [] # all extant creatures, living and dead
		self.turnmanager = Game.TurnManager(self.creatures)
		self.turnmanager.register_regular_eot_event(self.grow_trees)
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
			setattr(self.__class__, mlmeth, OvP._null)
		setattr(self.__class__, 'mousePressed', self._mousePressed)

		for klmeth in dir(KeyListener):
			setattr(self.__class__, klmeth, OvP._null)
		setattr(self.__class__, 'keyTyped', self._keyTyped)

		self.addMouseListener(self)
		self.addKeyListener(self)
		
	def _null(self, *args, **kwargs):
		pass

	def grow_trees(self):
		for hex in self.hb.hexes.values():
			if filter(lambda x: isinstance(x, Tree) or (isinstance(x, Pixie) and not x.is_dead()), hex.items):
				for adjhex in hex.get_adjacent_hexes():
					adjhex._nextnumneighbors += 1

		for hex in self.hb.hexes.values():
			if hex._nextnumneighbors == 3:
				if hex.is_empty():
					Tree(self, hex)

		for hex in self.hb.hexes.values():
			[x.get_older() for x in hex.get_all(Tree)]

			if hex._nextnumneighbors < 2:
				if hex.contains_a(Tree):
					[x.destroy() for x in hex.get_all(Tree)]
					if not hex.contains_a(Stone):
						Stone(self, hex)
			elif hex._nextnumneighbors >= 4:
				if hex.contains_a(Tree):
					[x.destroy() for x in hex.get_all(Tree)]
					if not hex.contains_a(Stone):
						Stone(self, hex)
			hex._nextnumneighbors = 0

	def init_locations(self):
		for hx in range(self.boardwidth):
			for hy in range(self.boardheight):
				OvPHex(self.hb, hx, hy)

	def init_creatures(self):
		for i in range(NUM_STARTING_OGRES):
			hex = self.hb.get_empty_hex(maxhx=self.boardwidth/3)
			if hex is not None:
				Ogre(self, hex)
		for i in range(NUM_STARTING_PIXIES):
			hex = self.hb.get_empty_hex(minhx=self.boardwidth*3/4)
			if hex is not None:
				Pixie(self, hex)
		for i in range(NUM_STARTING_TREES):
			hex = self.hb.get_empty_hex(minhx=self.boardwidth/3)
			if hex is not None:
				Tree(self, hex)

	def select_next_creature(self):
		"""
		Selects the next creature with action points.
		"""
		if (self.selecteditem is not None) and (isinstance(self.selecteditem, Creature)):
			i = self.creatures.index(self.selecteditem)
			self.selecteditem.unselect()
			cs = self.creatures[i+1:] + self.creatures[:i+1]
		else:
			cs = self.creatures

		for c in cs:
			if c.actpleft > 0:
				c.select()
				return

	def _mousePressed(self, e):
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

if __name__ == '__main__':
	ovp=OvP()
