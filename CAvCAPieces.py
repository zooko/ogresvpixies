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
__cvsid = '$Id: CAvCAPieces.py,v 1.1 2002/02/09 22:46:13 zooko Exp $'

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
import Game
import HexBoard
import Images
from util import *

true = 1
false = 0

class Item:
	def __init__(self, game, hex):
		"""
		@precondition `hex' must not be None.: hex is not None
		"""
		assert hex is not None, "precondition: `hex' must not be None."

		# print "Item.__init__(%s@%s)" % (self.__class__.__name__, id(self),)
		self.game = game
		self.hb = self.game.hb
		self.hex = hex
		self.hex.items.append(self)
		self.hex.repaint()

	def mouse_pressed(self):
		return false

	def __repr__(self):
		return "%s <%x> at %s" % (self.__class__.__name__, id(self), self.hex,)

	def repaint(self):
		self.hex.repaint()

	def destroy(self):
		self.hex.items.remove(self)
		self.repaint()

class OvPImageObserver(ImageObserver):
	def __init__(self, hb):
		# print "OvPImageObserver.__init__(%s@%s)" % (self.__class__.__name__, id(self),)
		self.hb = hb

	def imageUpdate(self, img, infoflags, x, y, width, height):
		result = self.hb.imageUpdate(img, infoflags, x, y, width, height)
		#print "[Debug:] imageUpdate(img=%r, infoflags=%r, x=%r, y=%r, width=%r, height=%r)\n-> %r" %\
		#	  (img, infoflags, x, y, width, height, result)
		return result

class Graphical (Item):
	IMAGEDEFAULT = None
	IMAGEPADDING = 10 # A hackish kludge until scaling works better.

	def __init__(self, game, hex, color=Color.black, image=None):
		"""
		@precondition `hex' must not be None.: hex is not None
		"""
		assert hex is not None, "precondition: `hex' must not be None."

		# print "Graphical.__init__(%s@%s)" % (self.__class__.__name__, id(self),)
		self.image = image or self.IMAGEDEFAULT or Images.getImageCache().get(self.__class__.__name__)
		self.color = color
		Item.__init__(self, game, hex)
		self.imageobserver = OvPImageObserver(self.hb)

	def paint(self, g):
		if self.image is not None:
			#print "[Debug:] Graphical.paint(self=%r, g); self.image = %r" % (self, self.image)
			dx, dy, dw, dh = unpack_rect(self.hex.boundingrect)
			sx, sy, sw, sh = 0, 0, self.image.getWidth(self.imageobserver), self.image.getHeight(self.imageobserver)
			pad = self.IMAGEPADDING
			g.drawImage(self.image,
						pad, pad, dw-pad, dh-pad,
						sx, sy, sx+sw, sy+sh,
						Color(0, 0, 0, 0), # An alpha of 0; does not seem to work.
						self.imageobserver)

class Cell(Graphical):
	def __init__(self, cellman, creatureman, hex, color):
		Graphical.__init__(self, cellman.game, hex, color=color)
		self.cellman = cellman
		self.creatureman = creatureman
		# print "self.creatureman: %s, traceback.extract_stack(): %s" % (self.creatureman, traceback.extract_stack(),)
		self.cellman.cells.append(self)
		self.age = 0

	def __repr__(self):
		return "%s %s <%x> at %s" % (self.color, self.__class__.__name__, id(self), self.hex,)

	def paint(self, g):
		mg = g.create()
		mg.setColor(self.color)
		mg.fill(self.hb.hexinnerpoly)

		strage = str(self.age)
		# (font, ox, oy,) = self.hb.find_fitting_font_nw_vertex(strage, mg)
		(font, ox, oy,) = self.hb.find_fitting_font_bottom_half(strage, mg)
		mg.setColor(Color.gray)
		mg.setFont(font)
		mg.drawString(strage, ox, oy)

	def get_older(self):
		self.age += 1
		if self.age > 99:
			ScoutCell(self.cellman, self.creatureman, self.hex, self.color)
			self.destroy()
		self.repaint()

	def destroy(self):
		assert self in self.hex.items
		Item.destroy(self)
		self.cellman.cells.remove(self)

class Active(Graphical):
	def __init__(self):
		# print "Active.__init__(%s@%s)" % (self.__class__.__name__, id(self),)
		pass

	def is_selected(self):
		return self.game.selectedcreature is self

	def paint(self, g):
		assert self in self.hex.items
		mg = g.create()
		if self.is_selected():
			mg.setColor(Color.yellow)
			mg.draw(self.hb.hexinnerpoly)

	def mouse_pressed(self):
		"""
		Active items are selectable as actors.

		@return `true' if the event was consumed
		"""
		# Select this item.
		self.select()
		return true

	def select(self):
		# print "%s.select()" % self
		assert self.actpleft > 0, "self: %s, self.actpleft: %s, traceback.extract_stack(): %s" % (self, self.actpleft, traceback.extract_stack(),)
		self.game.selectedcreature = self
		self.hex.repaint()

	def unselect(self):
		# print "%s.unselect(): st: %s" % (self, traceback.extract_stack(),)
		assert self.game.selectedcreature is self
		self.game.selectedcreature = None
		self.hex.repaint()

	def handle_cant_act(self):
		"""
		Ring the bell.
		"""
		print "I can't do that!"
		Toolkit.getDefaultToolkit().beep()

	def user_act(self, hex):
		"""
		The user has selected you, and then selected `hex'.  Try to do something to it!

		(The default behavior is to call `handle_cant_act()'.  Subclasses should override to implement acts.) 
		"""
		return self.handle_cant_act()

class Creature(Active):
	def __init__(self, creatureman, hp, actpoints):
		"""
		@param creatureman the creatureman for this creature
		@param hex the hex the creature inhabits
		@param actpoints action points (per turn)
		"""
		Active.__init__(self)
		# print "Creature.__init__(%s@%s)" % (self.__class__.__name__, id(self),)
		self.creatureman = creatureman
		self.actp = actpoints
		self.actpleft = 0 # invalid value
		creatureman.creatures.append(self)
		creatureman.turnman.register_regular_bot_event(self.handle_new_turn, priority="first")

	def __repr__(self):
		return Item.__repr__(self) + ", actpleft: %s" % self.actpleft

	def paint(self, g):
		Graphical.paint(self, g)
		Active.paint(self, g)

	def is_foe(self, item):
		return isinstance(item, Creature) and (item.__class__ is not self.__class__)

	def handle_new_turn(self):
		self.actpleft = self.actp
		assert self.actpleft > 0, "self: %s, self.actpleft: %s, traceback.extract_stack(): %s" % (self, self.actpleft, traceback.extract_stack(),)

	def pass(self):
		"""
		Throw away your remaining action points.

		@precondition you must be selected
		"""
		assert self.is_selected()
		self.actpleft = 0
		self.unselect()
		self.creatureman.turnman.select_next_creature_or_end_turn()

	def user_act(self, hex):
		"""
		The user has selected you, and then selected `hex'.  Try to do something to it!
		"""
		if hex is None:
			return

		# If it is ourself, then ignore this mousepress.
		if hex is self.hex:
			return

		if not hex.is_adjacent(self.hex):
			# path algorithm for creatures with > 1 actp
			# print "can't leap that far! self: %s, hex: %s, st: %s" % (self, hex, traceback.extract_stack(),)
			print "can't leap that far!"
			return self.handle_cant_act()

		assert self.actpleft >= 0, "self: %s, self.actpleft: %s, traceback.extract_stack(): %s" % (self, self.actpleft, traceback.extract_stack(),)
		if self.actpleft <= 0:
			print "can't do any more acts this turn"
			return self.handle_cant_act()

		assert self.actpleft > 0, "self: %s, self.actpleft: %s, traceback.extract_stack(): %s" % (self, self.actpleft, traceback.extract_stack(),)

		if hex.is_empty():
			self.act(self.move, kwargs={'hex': hex})
			return

		assert self.actpleft > 0, "self: %s, self.actpleft: %s, traceback.extract_stack(): %s" % (self, self.actpleft, traceback.extract_stack(),)

		# Else, you can't do anything to that hex.
		assert self in self.hex.items
		self.handle_cant_act()
		assert self in self.hex.items

	def act(self, act, args=(), kwargs={}):
		assert self in self.hex.items
		assert self.actpleft > 0, "self: %s, self.actpleft: %s, traceback.extract_stack(): %s" % (self, self.actpleft, traceback.extract_stack(),)
		self.actpleft -= 1
		assert self.actpleft >= 0, "self: %s, self.actpleft: %s, traceback.extract_stack(): %s" % (self, self.actpleft, traceback.extract_stack(),)
		apply(act, args, kwargs)
		assert self.actpleft >= 0, "self: %s, self.actpleft: %s, traceback.extract_stack(): %s" % (self, self.actpleft, traceback.extract_stack(),)
		if self.actpleft <= 0:
			self.creatureman.turnman.select_next_creature_or_end_turn()
		assert self in self.hex.items

	def move(self, hex):
		"""
		exit the old hex, move onto the top of the stack of the new one, repaint
		"""
		assert self in self.hex.items
		self.hex.items.remove(self)
		hex.items.append(self)
		self.repaint() # repaint the old
		self.hex = hex

		self.repaint() # repaint the new

	def destroy(self):
		self.creatureman.creatures.remove(self)

class ScoutCell(Cell, Creature):
	def __init__(self, cellman, creatureman, hex, color):
		Cell.__init__(self, cellman, creatureman.turnman, hex, color)
		Creature.__init__(self, creatureman, hp=1, actpoints=1)

	def paint(self, g):
		assert self in self.hex.items
		mg = g.create()
		mg.setColor(self.color)
		mg.fill(self.hb.hexinnerpoly)

		strage = str(self.age)
		# (font, ox, oy,) = self.hb.find_fitting_font_nw_vertex(strage, mg)
		(font, ox, oy,) = self.hb.find_fitting_font_bottom_half(strage, mg)
		mg.setColor(Color.white)
		mg.setFont(font)
		mg.drawString(strage, ox, oy)

		Creature.paint(self, mg)

	def get_older(self):
		assert self in self.hex.items
		self.age += 1
		if self.age >= 1:
			Cell(self.cellman, self.creatureman, self.hex, self.color)
			self.destroy()
		self.repaint()

	def destroy(self):
		assert self in self.hex.items
		Cell.destroy(self)
		Creature.destroy(self)

