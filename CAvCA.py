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
__cvsid = '$Id: CAvCA.py,v 1.1 2002/02/09 22:46:13 zooko Exp $'

import path_fix

# standard Java modules
import java
from java.lang import *
from java.awt import *
from java.awt.event import *
from java.awt.geom import *
from javax.swing import *
from javax.swing.text import *

# standard Python modules
import random
import math
import operator
import time
import traceback

# OvP modules
import HexBoard
from CAvCAPieces import *
import Game
from util import *

true = 1
false = 0

version = (0, 2, 1)
verstr = '.'.join(map(str, version))
name = "Cellular Automata vs. Cellular Automata"

NUM_STARTING_REDS=32
NUM_STARTING_BLUES=32

class CAvCAHex(HexBoard.Hex):
	def __init__(self, hb, hx, hy, bordercolor=Color.green, bgcolor=Color.black):
		HexBoard.Hex.__init__(self, hb, hx, hy, bordercolor, bgcolor)
		self._nextnumneighbors = {} # key: color, value: number of neighbors (default 0)

class CreatureMan:
	def __init__(self, turnman):
		self.turnman = turnman
		self.creatures = [] # "cells" that can move and have a lifespan

class CellMan:
	def __init__(self, game, color):
		self.game = game
		self.color = color
		self.cells = []

	def __repr__(self):
		if self.color is Color.red:
			return "red %s <%x>" % (self.__class__.__name__, id(self),)
		elif self.color is Color.blue:
			return "blue %s <%x>" % (self.__class__.__name__, id(self),)
		else:
			return "%s %s <%x>" % (self.color, self.__class__.__name__, id(self),)

	def evolve(self):
		# print "%s.evolve()" % self
		d = {} # k: hex, v: neighbs
		for cell in self.cells:
			d.setdefault(cell.hex, 0)
			for adjhex in cell.hex.get_adjacent_hexes():
				d[adjhex] = d.get(adjhex, 0) + 1

		for (hex, neighbs,) in d.items():
			if (neighbs < 1) or (neighbs >= 3):
				for item in hex.items:
					if isinstance(item, Cell) and (item.color is self.color):
						item.destroy()
			elif (neighbs == 2) and hex.is_empty():
				Cell(self, self.game.creaturemans[self.color], hex, self.color)

		for cell in self.cells[:]:
			cell.get_older()

class CAvCA(JFrame, MouseListener, KeyListener, Runnable):
	def __init__(self, boardwidth=32, boardheight=32, randseed=None):
		JFrame.__init__(self, name + " v" + verstr)
		if randseed == None:
			randseed = int(time.time())
		print "randseed: ", randseed
		self.selectedcreature = None
		self.randseed = randseed
		self.boardwidth = boardwidth
		self.boardheight = boardheight
		SwingUtilities.invokeLater(self)

	def run(self):
		randgen.seed(self.randseed)
		scale = 12
		self.hb = HexBoard.HexBoard(cxoffset=10, cyoffset=10+(self.boardheight-1)*scale*2*0.75, scale=scale)
		self.cellmans = {} # key: color, value: CellMan instance
		self.cellmans[Color.red] = CellMan(self, Color.red)
		self.cellmans[Color.blue] = CellMan(self, Color.blue)

		self.creaturemans = {} # key: color, value: CreatureMan instance
		self.creaturemans[Color.red] = CreatureMan(None)
		self.creaturemans[Color.blue] = CreatureMan(None)

		self.turnmans = {} # key: color, value: TurnMan instance
		self.turnmans[Color.red] = Game.TurnMan(self, self.creaturemans[Color.red], Color.red)
		self.turnmans[Color.blue] = Game.TurnMan(self, self.creaturemans[Color.blue], Color.blue)
		self.turnmans[Color.red].register_regular_eot_event(self.cellmans[Color.red].evolve)
		self.turnmans[Color.blue].register_regular_eot_event(self.cellmans[Color.blue].evolve)
		self.turnmans[Color.red].register_regular_eot_event(self.turnmans[Color.blue].begin_turn)
		self.turnmans[Color.blue].register_regular_eot_event(self.turnmans[Color.red].begin_turn)

		self.turnmans[Color.red].register_regular_bot_event(self.turnmans[Color.red].select_next_creature_or_end_turn)
		self.turnmans[Color.blue].register_regular_bot_event(self.turnmans[Color.blue].select_next_creature_or_end_turn)

		self.creaturemans[Color.red].turnman = self.turnmans[Color.red]
		self.creaturemans[Color.blue].turnman = self.turnmans[Color.blue]

		HSLOP=30
		VSLOP=60
		self.setContentPane(self.hb)
		self.setSize(int(HSLOP + ((self.boardwidth+0.5)*self.hb.w)), int(VSLOP + (self.boardheight*self.hb.h*0.75)))
		self.init_locations()

		self.setVisible(true)
		self.init_creatures()
		self.turnmans[Color.red].begin_turn()

		for mlmeth in dir(MouseListener):
			setattr(self.__class__, mlmeth, CAvCA._null)
		setattr(self.__class__, 'mousePressed', self._mousePressed)

		for klmeth in dir(KeyListener):
			setattr(self.__class__, klmeth, CAvCA._null)
		setattr(self.__class__, 'keyTyped', self._keyTyped)

		self.addMouseListener(self)
		self.addKeyListener(self)

	def _null(self, *args, **kwargs):
		pass

	def init_locations(self):
		for hx in range(self.boardwidth):
			for hy in range(self.boardheight):
				CAvCAHex(self.hb, hx, hy)

	def init_creatures(self):
		prev = None
		for i in range(NUM_STARTING_REDS):
			if (prev is not None):
				adj = random.choice(prev.get_adjacent_hexes())
				if adj.is_empty():
					Cell(self.cellmans[Color.red], self.creaturemans[Color.red], adj, color=Color.red)
					prev = adj
					continue

			hex = self.hb.get_empty_hex()
			if hex is not None:
				Cell(self.cellmans[Color.red], self.creaturemans[Color.red], hex, color=Color.red)
				prev = hex

		prev = None
		for i in range(NUM_STARTING_BLUES):
			if (prev is not None):
				adj = random.choice(prev.get_adjacent_hexes())
				if adj.is_empty():
					Cell(self.cellmans[Color.blue], self.creaturemans[Color.blue], adj, color=Color.blue)
					prev = adj
					continue

			hex = self.hb.get_empty_hex()
			if hex is not None:
				Cell(self.cellmans[Color.blue], self.creaturemans[Color.blue], hex, color=Color.blue)
				prev = hex

	def _mousePressed(self, e):
		pt = e.getPoint()
		hbpt = self.hb.getLocation()
		rppt = self.getRootPane().getLocation()
		pt.translate(hbpt.x - rppt.x, hbpt.y - rppt.y)
		hex = self.hb.pick_hex(pt)
		if SwingUtilities.isRightMouseButton(e):
			if self.selectedcreature is not None:
				# cancel of current selection by right-click
				self.selectedcreature.unselect()
		else:
			if self.selectedcreature is not None:
				# act-request
				self.selectedcreature.user_act(hex)
			else:
				if (hex is not None) and (not hex.is_empty()):
					# mousepress
					hex.items[-1].mouse_pressed()

	def _keyTyped(self, e):
		c = e.getKeyChar()
		if c == 't':
			# if any turn mans are waiting for confirm, then this is the confirm
			for tm in self.turnmans.values():
				if tm.waitingforconfirm:
					tm._really_end_turn()
					return

		# keystrokes when there is a current selected item
		if self.selectedcreature is None:
			return
		if c == 'w':
			self.selectedcreature.user_act(self.selectedcreature.hex.get_nw())
		elif c == 'e':
			self.selectedcreature.user_act(self.selectedcreature.hex.get_ne())
		elif c == 'a':
			self.selectedcreature.user_act(self.selectedcreature.hex.get_w())
		elif c == 'd':
			self.selectedcreature.user_act(self.selectedcreature.hex.get_e())
		elif c == 'z':
			self.selectedcreature.user_act(self.selectedcreature.hex.get_sw())
		elif c == 'x':
			self.selectedcreature.user_act(self.selectedcreature.hex.get_se())
		elif c == 's':
			self.selectedcreature.user_act(self.selectedcreature.hex)
		elif c == 'u':
			self.selectedcreature.unselect()
		if c == 'n':
			self.selectedcreature.creatureman.turnman.select_next_creature_or_end_turn()
		elif c == ' ':
			self.selectedcreature.pass()

if __name__ == '__main__':
	ovp=CAvCA()
