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
__cvsid = '$Id: OvP.py,v 1.1 2002/01/25 16:36:01 zooko Exp $'

import path_fix
version = (0, 0, 2,)
verstr = '.'.join(map(str, version))

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

NUM_STARTING_OGRES=2
NUM_STARTING_PIXIES=2
NUM_STARTING_TREES=4

class OvPHex(HexBoard.Hex):
	def __init__(self, hb, hx, hy, bordercolor=Color.GREEN, bgcolor=Color.BLACK):
		HexBoard.Hex.__init__(self, hb, hx, hy, bordercolor, bgcolor)

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
		JFrame.__init__(self, 'Ogres vs. Gardening Pixies [Version: %s]' % verstr)
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
		self.turnmanager.register_regular_eot_event(self.grow_a_tree)
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

	def _is_potential_clump(self, hex):
		"""
		@return true if, among the adjacent hexes to `hex', two of them which are adjacent to each other both contain trees
		"""
		adjswtrees = filter(lambda x: x.contains_a(Tree), hex.get_adjacent_hexes())
		for a1 in adjswtrees:
			for a2 in adjswtrees:
				if (a1 is not a2) and (a1.is_adjacent(a2)):
					return true
		return false

	def grow_a_tree(self):
		for emptyhex in rand_rotate(filter(HexBoard.Hex.is_empty, self.hb.hexes.values())):
			for adjhex in emptyhex.get_adjacent_hexes():
				if adjhex.contains_a(Tree):
					Tree(self, emptyhex)
					# Create Stones to prevent straight-runs.
					opphex = adjhex.get_opposite(emptyhex)
					if opphex is not None:
						if opphex.is_empty():
							Stone(self, opphex)
						# for longer runs of stones:
						# nexthex = emptyhex.get_opposite(opphex)
						# if (nexthex is not None) and nexthex.is_empty():
						# 	Stone(self, nexthex)
						# for coriolis stones:
						# predhex = opphex.get_circle_predecessor(emptyhex)
						# if (predhex is not None) and predhex.is_empty():
						# 	Stone(self, predhex)
					return
		# If there were no appropriate spots.  No trees grow!

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
			hex = self.hb.get_empty_hex(minhx=self.boardwidth/3)
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
