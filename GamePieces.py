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
__cvsid = '$Id: GamePieces.py,v 1.2 2002/01/29 22:48:48 zooko Exp $'

import path_fix
version = (1, 1, 0)
verstr = '.'.join(map(str, version))
name = "Ogres vs. Cellular Automata"

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

class Flying:
	def __init__(self):
		# print "Flying.__init__(%s@%s)" % (self.__class__.__name__, id(self),)
		pass

class Item:
	def __init__(self, game, hex, treadable):
		"""
		@precondition `hex' must not be None.: hex is not None
		"""
		assert hex is not None, "precondition: `hex' must not be None."

		# print "Item.__init__(%s@%s)" % (self.__class__.__name__, id(self),)
		self.game = game
		self.hb = self.game.hb
		self.hex = hex
		self.treadable = treadable
		self.hex.items.append(self)
		self.hex.repaint()

	def mouse_pressed(self):
		return false

	def is_treadable(self, treader=None):
		"""
		@param who is doing the treading, or `None' if default
		"""
		# print "Item.is_treadable(%s)" % self
		if self.treadable == "all":
			return true
		elif self.treadable == "none":
			return false
		elif self.treadable == "flying only":
			return isinstance(treader, Flying)

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

	def __init__(self, game, hex, treadable, color=Color.black, image=None):
		"""
		@precondition `hex' must not be None.: hex is not None
		"""
		assert hex is not None, "precondition: `hex' must not be None."

		# print "Graphical.__init__(%s@%s)" % (self.__class__.__name__, id(self),)
		self.image = image or self.IMAGEDEFAULT or Images.getImageCache().get(self.__class__.__name__)
		self.color = color
		Item.__init__(self, game, hex, treadable)
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

class Active(Graphical):
	def __init__(self, game, hex, color=Color.black):
		# print "Active.__init__(%s@%s)" % (self.__class__.__name__, id(self),)
		pass

	def is_selected(self):
		return self.game.selecteditem is self

	def paint(self, g):
		mg = g.create()
		if self.is_selected():
			mg.setColor(Color.yellow)
			mg.draw(self.hb.hexinnerpoly)

	def mouse_pressed(self):
		"""
		Active items are selectable as actors.  (Unless dead.)
		XXX NOTE: it would be better, instead of managing boolean state `self.dead' and switching on it in various places, to make the object stop being a subclass of Active and become a subclass of Dead instead.

		@return `true' if the event was consumed
		"""
		if not Item.mouse_pressed(self):
			if not self.is_dead():
				# Select this item.
				self.select()
				return true
		return false

	def select(self):
		assert self.actpleft > 0, "self: %s, self.actpleft: %s, traceback.extract_stack(): %s" % (self, self.actpleft, traceback.extract_stack(),)
		self.game.selecteditem = self
		self.hex.repaint()

	def unselect(self):
		# print "%s.unselect(): st: %s" % (self, traceback.extract_stack(),)
		assert self.game.selecteditem is self
		self.game.selecteditem = None
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

DEFAULT_NUM_SPLATTERS=8
class Attackable(Graphical):
	IMAGEDEAD = None
	
	def __init__(self, hp, defense, numsplatters=DEFAULT_NUM_SPLATTERS, bloodcolor=Color.red, deadimage=None):
		# print "Attackable.__init__(%s@%s)" % (self.__class__.__name__, id(self),)
		self.defensedice = defense
		self.hp = hp
		self.highhp = self.hp # the high water mark for hp
		self.numsplatters = numsplatters
		self.bloodcolor = bloodcolor
		self.deadimage = deadimage or self.IMAGEDEAD or Images.getImageCache().get('Dead' + self.__class__.__name__.lower())

		self.splatters = [] # a list of (x, y, r,) for blood spatters

	def __repr__(self):
		if self.is_dead():
			return "dead " + Item.__repr__(self)
		else:
			return Item.__repr__(self) + ", hp: %s" % self.hp

	def paint(self, g):
		mg = g.create()
		mg.setColor(self.bloodcolor)
		for (x, y, d,) in self.splatters:
			mg.fillOval(x, y, d, d)

		if not self.is_dead():
			if self.highhp > 1:
				strhp = str(self.hp)
				(font, ox, oy,) = self.hb.find_fitting_font_nw_vertex(strhp, mg)
				# (font, ox, oy,) = self.hb.find_fitting_font_bottom_half(strhp, mg)
				mg.setColor(Color.white)
				mg.setFont(font)
				mg.drawString(strhp, ox, oy)

	def handle_attack(self, attdice):
		defdice = []
		for i in range(self.defensedice):
			defdice.append(d6())
		defdice.sort()
		defdice.reverse()
		# print "%s.attack(%s): attdice: %s, defdice: %s" % (self, defender, attdice, defdice,)
		if attdice[0] > defdice[0]:
			# hit!
			self.take_damage(1)
		else:
			print "missed..."

	def take_damage(self, amount):
		print "%s.take_damage(%s): Ouch!" % (self, amount,)
		self.hp = self.hp - amount
		x = int(self.IMAGEPADDING + rand_float(self.hb.w - self.IMAGEPADDING*2))
		y = int(self.IMAGEPADDING + rand_float(self.hb.h - self.IMAGEPADDING*2))
		r = int(1 + rand_float(self.hb.s*0.4))
		self.splatters.append((x, y, r,))
		if len(self.splatters) > self.highhp:
			self.splatters = self.splatters[:-self.highhp]
		self.hex.repaint()
		if self.hp == 0:
			self.die()

	def is_dead(self):
		return self.hp <= 0

	def die(self):
		self.hp = 0
		self.actpleft = 0
		self.image = self.deadimage
		# move to the bottom of the stack
		self.hex.items.remove(self)
		self.hex.items.insert(0, self)
		# add blood spatters
		for i in range(rand_int(self.numsplatters)):
			xdir = rand_int(2)*2 - 1
			ydir = rand_int(2)*2 - 1
			xl = randgen.random()*randgen.random()*randgen.random()*randgen.random()*44
			yl = randgen.random()*randgen.random()*randgen.random()*randgen.random()*44
			r = randgen.random()*randgen.random()*randgen.random()*randgen.random()*64
			self.splatters.append((int((self.hb.w*0.5) + (xdir*xl)), int((self.hb.h*0.5) + (ydir*yl)), int(r),))

		self.hex.repaint()

	def is_treadable(self, treader=None):
		# print "Attackable.is_treadable(%s)" % self
		if self.is_dead():
			return true
		return Item.is_treadable(self, treader)

class Stone(Attackable):
	def __init__(self, game, hex, treadable="flying only", color=Color.gray):
		"""
		@precondition `hex' must not be None.: hex is not None
		"""
		assert hex is not None, "precondition: `hex' must not be None."

		# print "Stone.__init__(%s@%s)" % (self.__class__.__name__, id(self),)
		Attackable.__init__(self, hp=1, defense=1, numsplatters=0, bloodcolor=color)
		Graphical.__init__(self, game, hex, treadable, color=color)

	def paint(self, g):
		Graphical.paint(self, g)
		Attackable.paint(self, g)
		mg = g.create()
		mg.setColor(self.color)
		d=self.hb.s/2
		mg.fillOval(self.hb.w/2-d/2, self.hb.h/2-d/2, d, d)

	def die(self):
		Attackable.die(self)
		# remove entirely
		self.hex.items.remove(self)
		self.hex.repaint()
		
class Creature(Attackable, Active):
	def __init__(self, game, hex, hp, actpoints, attack, defense, numsplatters=DEFAULT_NUM_SPLATTERS, color=Color.black, bloodcolor=Color.red, deadimage=None):
		"""
		@param game the Ogres vs Pixies game
		@param hex the hex the creature inhabits
		@param hp starting hit points
		@param actpoints action points (per turn)
		"""
		# print "Creature.__init__(%s@%s)" % (self.__class__.__name__, id(self),)
		self.actp = actpoints
		self.attackdice = attack
		self.actpleft = 0 # invalid value
		game.creatures.append(self)
		game.turnmanager.register_regular_bot_event(self.handle_new_turn, priority="first")
		Active.__init__(self, game, hex, color=color)
		Attackable.__init__(self, hp=hp, defense=defense, numsplatters=numsplatters, bloodcolor=bloodcolor, deadimage=deadimage)
		Graphical.__init__(self, game, hex, treadable="none", color=color)

	def __repr__(self):
		if self.is_dead():
			return "dead " + Item.__repr__(self)
		else:
			return Item.__repr__(self) + ", actpleft: %s" % self.actpleft

	def paint(self, g):
		Graphical.paint(self, g)
		Attackable.paint(self, g)
		Active.paint(self, g)

	def is_foe(self, item):
		return isinstance(item, Creature) and (item.__class__ is not self.__class__)

	def handle_new_turn(self):
		if not self.is_dead():
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
		self.game.select_next_creature()
		self.game.turnmanager.go_if_ready() # If there are no more acts that need to be decided, then go ahead and resolve acts now.

	def user_act(self, hex):
		"""
		The user has selected you, and then selected `hex'.  Try to do something to it!

		(Try to move onto it, if that fails try to attack it.)
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

		# If all items are treadable, move there:
		blocked = false
		for item in hex.items:
			if not item.is_treadable(self):
				# print "blocked by %s" % item
				blocked = true
		if not blocked:
			self.schedule_act(self.move, kwargs={'hex': hex})
			return

		# Else, if you can attack an item, attack the first one it (top items first):
		for idx in range(len(hex.items)-1, -1, -1):
			item = hex.items[idx]
			if isinstance(item, Attackable):
				# WHAH?  Won't let me MOVE there, EH?  We'll see about that!
				# print "attacking %s" % item
				self.schedule_act(self.attack, kwargs={'defender': item})
				return

		assert self.actpleft > 0, "self: %s, self.actpleft: %s, traceback.extract_stack(): %s" % (self, self.actpleft, traceback.extract_stack(),)

		# Else, you can't do anything to that hex.
		self.handle_cant_act()

	def schedule_act(self, act, args=(), kwargs={}):
		assert self.actpleft > 0, "self: %s, self.actpleft: %s, traceback.extract_stack(): %s" % (self, self.actpleft, traceback.extract_stack(),)
		self.actpleft -= 1
		assert self.actpleft >= 0, "self: %s, self.actpleft: %s, traceback.extract_stack(): %s" % (self, self.actpleft, traceback.extract_stack(),)
		self.game.turnmanager.add_act(act, args, kwargs)
		assert self.actpleft >= 0, "self: %s, self.actpleft: %s, traceback.extract_stack(): %s" % (self, self.actpleft, traceback.extract_stack(),)
		if self.actpleft <= 0:
			self.unselect()
			self.game.select_next_creature()
		self.game.turnmanager.go_if_ready() # If there are no more acts that need to be decided, then go ahead and resolve acts now.
		
	def move(self, hex):
		"""
		exit the old hex, move onto the top of the stack of the new one, check for ZoC, repaint
		"""
		self.hex.items.remove(self)
		hex.items.append(self)
		self.repaint() # repaint the old
		self.hex = hex

		# The Zone of Control rule:  when you move onto a hex that is adjacent to a live enemy, your actpleft is set to 0.
		for adj in hex.get_adjacent_hexes():
			for i in adj.items:
				if self.is_foe(i) and not i.is_dead():
					self.actpleft = 0

		self.repaint() # repaint the new

	def attack(self, defender):
		attdice = []
		for i in range(self.attackdice):
			attdice.append(d6())
		attdice.sort()
		attdice.reverse()
		defender.handle_attack(attdice)

class Ogre(Creature):
	def __init__(self, game, hex, bloodcolor=Color.red):
		# print "Ogre.__init__(%s@%s)" % (self.__class__.__name__, id(self),)
		Creature.__init__(self, game, hex, hp=3, actpoints=1, attack=3, defense=2, bloodcolor=bloodcolor)

	def move(self, hex):
		Creature.move(self, hex)
		for i in self.hex.items:
			if isinstance(i, Tree) or (isinstance(i, Creature) and i.is_dead()):
				self.eat(i)

	def eat(self, item):
		item.destroy()
		self.hp += 1
		if self.hp > self.highhp:
			self.highhp = self.hp

		# If an ogre eats a tree, then all trees adjacent to that tree immediately die of fright.
		if isinstance(item, Tree):
			for adjhex in item.hex.get_adjacent_hexes():
				[x.destroy() for x in adjhex.get_all(Tree)]
		self.repaint()

class Tree(Graphical):
	def __init__(self, ovp, hex, treadable="all", color=Color.black):
		# print "Tree.__init__(%s@%s)" % (self.__class__.__name__, id(self),)
		Graphical.__init__(self, ovp, hex, treadable=treadable, color=color)
		for adjhex in hex.get_adjacent_hexes():
			# Now check if this new tree just formed a Broken Pixie Ring.  If so, create a 3-Pixie there.
			if adjhex.is_center_of_broken_pixie_ring():
				# WHOO!  A BROKEN PIXIE RING!  Remove any Stones and create a 3-Pixie in the center of the Fairie Ring.
				[x.destroy() for x in adjhex.get_all(Tree)]
				[x.destroy() for x in adjhex.get_all(Stone)]
				Pixie(ovp, adjhex, hp=3)

			# Now check if this new tree just formed a Pixie Ring.  If so, create a Pixie there.
			if adjhex.is_center_of_pixie_ring():
				# WHOO!  A PIXIE RING!  Remove any Stones and create a Pixie in the center of the Fairie Ring.
				[x.destroy() for x in adjhex.get_all(Tree)]
				[x.destroy() for x in adjhex.get_all(Stone)]
				Pixie(ovp, adjhex)

	def paint(self, g):
		Graphical.paint(self, g)
		mg = g.create()
		mg.setColor(Color.black)
		mg.draw(self.hb.treepoly)
		mg.setColor(Color.green)
		mg.fill(self.hb.treeinnerpoly)

class Pixie(Creature, Flying):
	def __init__(self, ovp, hex, color=Color.white, hp=1, bloodcolor=Color(0.7, 1.0, 0.3)):
		# print "Pixie.__init__(%s@%s)" % (self.__class__.__name__, id(self),)
		self.carrieditems = []
		Creature.__init__(self, ovp, hex, hp=hp, actpoints=3, attack=1, defense=1, color=color, bloodcolor=bloodcolor)
		Flying.__init__(self)

	def garden(self):
		"""
		If there are any underlying trees, destroy them.
		If there is some non-Tree (and non-Creature!) underlying item, pick it up.
		If there is no underlying item, and you are carrying an item, drop it.
		"""
		[x.destroy() for x in self.hex.get_all(Tree)]
		items = self.hex.items[:] # copy the list
		items.reverse() # reverse it
		for item in items:
			if not isinstance(item, Tree) and not isinstance(item, Creature):
				self.carrieditems.append(item)
				self.hex.items.remove(item)
				# While being carried, the item has no `self.hex'!
				item.hex = None
				self.repaint()
				self.hex.repaint()
				return

		if len(self.carrieditems) > 0:
			item = self.carrieditems.pop(0)
			self.hex.items.append(item)
			item.hex = self.hex
			self.repaint()
			self.hex.repaint()

##	def user_act(self, hex):
##		"""
##		The user has selected you, and then selected `hex'.  Try to do something to it!
##		"""
##		if hex is None:
##			return

##		# If it is ourself, then do gardening.
##		if hex is self.hex:
##			self.garden()
##		else:
##			Creature.user_act(self, hex)

