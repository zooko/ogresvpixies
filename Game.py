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
__cvsid = '$Id: Game.py,v 1.2 2002/02/09 22:46:13 zooko Exp $'

import operator

from java.lang import *
from javax.swing import *
from java.awt import *

true = 1
false = 0

class TurnMan:
	def __init__(self, game, creatures, color):
		self.game = game
		self.creatures = creatures
		self.color = color
		self.turnnumber = 0
		self.rbotevs = []
		self.reotevs = []
		self.waitingforconfirm = false # this is `true' if we are waiting for the user to press the `t' key before beginning the next turn

	def __repr__(self):
		if self.color is Color.red:
			return "red %s <%x>" % (self.__class__.__name__, id(self),)
		elif self.color is Color.blue:
			return "blue %s <%x>" % (self.__class__.__name__, id(self),)
		else:
			return "%s %s <%x>" % (self.color, self.__class__.__name__, id(self),)

	def register_regular_bot_event(self, rbotev, args=(), kwargs={}, priority="whatever"):
		if priority == "first":
			self.rbotevs.insert(0, (rbotev, args, kwargs,))
		else:
			self.rbotevs.append((rbotev, args, kwargs,))

	def register_regular_eot_event(self, reotev, args=(), kwargs={}):
		self.reotevs.append((reotev, args, kwargs,))

	def begin_turn(self):
		self.turnnumber += 1
		# print "%s.begin_turn(): %s" % (self, self.turnnumber,),
		for (rbotev, args, kwargs,) in self.rbotevs:
			apply(rbotev, args, kwargs)

	def end_turn(self):
		for (reotev, args, kwargs,) in self.reotevs:
			apply(reotev, args, kwargs)
		# print "end_turn(): (waiting for `t' key)"
		# self.waitingforconfirm = true

	def _really_end_turn(self):
		self.waitingforconfirm = false
		for (reotev, args, kwargs,) in self.reotevs:
			apply(reotev, args, kwargs)

	def select_next_creature_or_end_turn(self):
		"""
		Selects the next creature with action points.  If there are no more creatures, it does end-of-turn.
		"""
		if self.game.selectedcreature is not None:
			i = self.creatures.index(self.game.selectedcreature)
			self.game.selectedcreature.unselect()
			cs = self.creatures[i+1:] + self.creatures[:i+1]
		else:
			cs = self.creatures

		for c in cs:
			if c.actpleft > 0:
				c.select()
				return

		# No more creatures have action points.  Next turn!
		self.end_turn()

