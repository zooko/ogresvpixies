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
__cvsid = '$Id: War.py,v 1.1 2002/02/09 22:46:13 zooko Exp $'

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
from WarPieces import *
import Game
import Images
from util import *

true = 1
false = 0

version = (0, 0, 0)
verstr = '.'.join(map(str, version))
name = "Fantastic Creatures vs. Fearsome Monsters"

class WarHex(HexBoard.Hex):
	def __init__(self, hb, hx, hy, bordercolor=Color.green, bgcolor=Color.black):
		HexBoard.Hex.__init__(self, hb, hx, hy, bordercolor, bgcolor)

class War(JFrame, MouseListener, KeyListener, Runnable):
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
		scale = 35
		self.hb = HexBoard.HexBoard(cxoffset=10, cyoffset=10+(self.boardheight-1)*scale*2*0.75, scale=scale)
		self.selectedcreature = None
		self.creatures = {} # k: color, v: list
		self.creatures[Color.red] = []
		self.creatures[Color.white] = []
		self.creatures[Color.blue] = []
		self.turnmans = {} # k: color, v: TurnMan
		self.turnmans[Color.red] = Game.TurnMan(self, self.creatures[Color.red], Color.red)
		self.turnmans[Color.white] = Game.TurnMan(self, self.creatures[Color.white], Color.white)
		self.turnmans[Color.blue] = Game.TurnMan(self, self.creatures[Color.blue], Color.blue)

		self.turnmans[Color.red].register_regular_eot_event(self.turnmans[Color.white].begin_turn)
		self.turnmans[Color.white].register_regular_eot_event(self.turnmans[Color.blue].begin_turn)
		self.turnmans[Color.blue].register_regular_eot_event(self.turnmans[Color.red].begin_turn)

		self.turnmans[Color.red].register_regular_bot_event(self.turnmans[Color.red].select_next_creature_or_end_turn)
		self.turnmans[Color.white].register_regular_bot_event(self.turnmans[Color.white].select_next_creature_or_end_turn)
		self.turnmans[Color.blue].register_regular_bot_event(self.turnmans[Color.blue].select_next_creature_or_end_turn)

		self.turnmans[Color.blue].register_regular_eot_event(self.generate_scroll)

		HSLOP=30
		VSLOP=60
		self.setContentPane(self.hb)
		self.setSize(int(HSLOP + ((self.boardwidth+0.5)*self.hb.w)), int(VSLOP + (self.boardheight*self.hb.h*0.75)))
		self.init_locations()

		self.setVisible(true)
		def finish_init(self=self):
			self.init_creatures()
			self.turnmans[Color.red].begin_turn()

			for mlmeth in dir(MouseListener):
				setattr(self.__class__, mlmeth, War._null)
			setattr(self.__class__, 'mousePressed', self._mousePressed)

			for klmeth in dir(KeyListener):
				setattr(self.__class__, klmeth, War._null)
			setattr(self.__class__, 'keyTyped', self._keyTyped)

			self.addMouseListener(self)
			self.addKeyListener(self)
		self.init_maze(finish_init)
	
	def _null(self, *args, **kwargs):
		pass

	def generate_scroll(self):
		hex = self.hb.get_empty_hex()
		if hex is not None:
			Scroll(self, hex)

	def init_locations(self):
		for hx in range(self.boardwidth):
			for hy in range(self.boardheight):
				WarHex(self.hb, hx, hy)

	def walk(self, current, next_func):
		current.unhighlight()
		adjhexes = rand_rotate(current.get_adjacent_hexes())
		# pick a random direction to walk
		for adjhex in adjhexes:
			if adjhex.contains_a(Wall):
				wouldclump = false
				oadjs = adjhex.get_ordered_adjacent_hexes()
				for i in range(len(oadjs)):
					run = (oadjs[i], oadjs[(i+1)%len(oadjs)], oadjs[(i+2)%len(oadjs)],)
					if not filter(lambda x: x is None or x.contains_a(Wall), run):
						wouldclump = true
						break
				if not wouldclump:
					adjhex.highlight()
					[x.destroy() for x in adjhex.get_all(Wall)]
					SwingUtilities.invokeLater(Runner(self.walk, args=(adjhex, next_func)))
					return
		SwingUtilities.invokeLater(Runner(next_func))

	def _init_maze_more(self, next_func):
		done = [0]
		def do_4_then_next_func(done=done, next_func=next_func):
			done[0] += 1
			if done[0] >= 4:
				SwingUtilities.invokeLater(Runner(next_func))

		cornerlocs = [(0,0,), (15,0,), (15,11,), (0,11,),]
		for i in range(len(cornerlocs)):
			starthex = self.hb.hexes[cornerlocs[i]]
			[x.destroy() for x in starthex.get_all(Wall)]
			self.walk(starthex, next_func=do_4_then_next_func)

	def init_maze(self, next_func):
		for hex in self.hb.hexes.values():
			Wall(self, hex)
		SwingUtilities.invokeLater(Runner(self._init_maze_more, args=(next_func,)))

		# Now if there are any big blocks of stone still, let's put hidden rooms in them
##		for hex in self.hb.hexes.values():
##			n/St
##xxxx
	def init_creatures(self):
		try:
			sumprice = 0
			import BlueArmy
			for (klass, args, kwargs,) in BlueArmy.army:
				kwargs['game'] = self
				kwargs['hex'] = self.hb.get_empty_hex(maxhx=self.boardwidth/3)
				kwargs['color'] = Color.blue
				creature = apply(klass, args, kwargs)
				print "blue army gains a %s for %s!" % (creature.__class__.__name__, creature.price(),)
				sumprice += creature.price()
			print "the price of the blue army is ", sumprice
			print
		except:
			# oh well.  no blue army.
			pass

		try:
			sumprice = 0
			import RedArmy
			for (klass, args, kwargs,) in RedArmy.army:
				kwargs['game'] = self
				kwargs['hex'] = self.hb.get_empty_hex(minhx=self.boardwidth*2/3)
				kwargs['color'] = Color.red
				creature = apply(klass, args, kwargs)
				print "red army gains a %s for %s!" % (creature.__class__.__name__, creature.price(),)
				sumprice += creature.price()
			print "the price of the red army is ", sumprice
			print
		except:
			# oh well.  no red army.
			pass

		try:
			sumprice = 0
			import WhiteArmy
			for (klass, args, kwargs,) in WhiteArmy.army:
				kwargs['game'] = self
				kwargs['hex'] = self.hb.get_empty_hex(maxhx=self.boardwidth/3)
				kwargs['color'] = Color.white
				creature = apply(klass, args, kwargs)
				print "white army gains a %s for %s!" % (creature.__class__.__name__, creature.price(),)
				sumprice += creature.price()
			print "the price of the white army is ", sumprice
			print
		except:
			# oh well.  no white army.
			pass

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

		# keystrokes when there is a current selected creature
		if self.selectedcreature is None:
			return
		self.selectedcreature.key_typed(e)

if __name__ == '__main__':
	ovp=War()
