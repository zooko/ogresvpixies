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
__cvsid = '$Id: WarPieces.py,v 1.1 2002/02/09 22:46:13 zooko Exp $'

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

class Flying:
	def __init__(self):
		# print "Flying.__init__(%s@%s)" % (self.__class__.__name__, id(self),)
		pass

class Big:
	def __init__(self):
		# print "Big.__init__(%s@%s)" % (self.__class__.__name__, id(self),)
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
		return "%s at %s" % (self.__class__.__name__, self.hex,)

	def repaint(self):
		self.hex.repaint()

	def paint(self, g):
		mg = g.create()
		str = self.__class__.__name__
		if isinstance(self, Attackable) and self.is_dead():
			str = "dead " + str
		(font, ox, oy,) = self.hb.find_fitting_font_bottom_half(str, mg)
		mg.setColor(Color.white)
		mg.setFont(font)
		mg.drawString(str, ox, oy)

	def destroy(self):
		self.hex.items.remove(self)
		self.repaint()

class OurImageObserver(ImageObserver):
	def __init__(self, hb):
		# print "OurImageObserver.__init__(%s@%s)" % (self.__class__.__name__, id(self),)
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
		self.imageobserver = OurImageObserver(self.hb)

	def paint(self, g):
		mg = g.create()
		if self.image is not None:
			#print "[Debug:] Graphical.paint(self=%r, g); self.image = %r" % (self, self.image)
			dx, dy, dw, dh = unpack_rect(self.hex.boundingrect)
			sx, sy, sw, sh = 0, 0, self.image.getWidth(self.imageobserver), self.image.getHeight(self.imageobserver)
			pad = self.IMAGEPADDING
			mg.drawImage(self.image,
						pad, pad, dw-pad, dh-pad,
						sx, sy, sx+sw, sy+sh,
						Color(0, 0, 0, 0), # An alpha of 0; does not seem to work.
						self.imageobserver)
		else:
			Item.paint(self, g)

class Active(Graphical):
	def __init__(self):
		# print "Active.__init__(%s@%s)" % (self.__class__.__name__, id(self),)
		pass

	def is_selected(self):
		return self.game.selectedcreature is self

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
			if not (isinstance(self, Attackable) and self.is_dead()):
				# Select this item.
				self.select()
				return true
		return false

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

DEFAULT_NUM_SPLATTERS=8
class Attackable(Graphical):
	IMAGEDEAD = None
	
	def __init__(self, hp, defensep, numsplatters=DEFAULT_NUM_SPLATTERS, bloodcolor=Color.red, deadimage=None):
		# print "Attackable.__init__(%s@%s)" % (self.__class__.__name__, id(self),)
		self.defensep = defensep
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
			return Item.__repr__(self)

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

	def handle_attack(self, attackval, damage, attacker):
		defenseroll = d6() + d6() + d6()
		defenseval = defenseroll + self.defensep
		print "%2s + %2s = %2s" % (defenseroll, self.defensep, defenseval,),
		if attackval > defenseval:
			# hit!
			self.take_damage(damage)
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

class Wall(Attackable):
	def __init__(self, game, hex, treadable="none", color=Color.gray):
		"""
		@precondition `hex' must not be None.: hex is not None
		"""
		assert hex is not None, "precondition: `hex' must not be None."

		# print "Wall.__init__(%s@%s)" % (self.__class__.__name__, id(self),)
		Attackable.__init__(self, hp=3, defensep=-2, numsplatters=0, bloodcolor=Color.lightGray)
		Graphical.__init__(self, game, hex, treadable, color=color)

	def paint(self, g):
		#Graphical.paint(self, g)
		#Attackable.paint(self, g)
		mg = g.create()
		mg.setColor(self.color)
		d=self.hb.s/2
		mg.fill(self.hb.hexpoly)
		mg.setColor(self.bloodcolor)
		for (x, y, d,) in self.splatters:
			mg.fillOval(x, y, d, d)

	def handle_attack(self, attackval, damage, attacker):
		if not (isinstance(attacker, Big) or isinstance(attacker, Dwarf)):
			print "I'm sorry, this wall can only be harmed by Big creatures or Dwarfs."
			damage = 0
		Attackable.handle_attack(self, attackval, damage, attacker)

	def take_damage(self, amount):
		if amount == 0:
			# print "%s.take_damage(%s): Nyah nyah nyah nyah NYAH nyah!" % (self, amount,)
			print
			return
		print "%s.take_damage(%s): Ouch!" % (self, amount,)
		self.hp = self.hp - amount
		x = int(self.IMAGEPADDING + rand_float(self.hb.w - self.IMAGEPADDING*2))
		y = int(self.IMAGEPADDING + rand_float(self.hb.h - self.IMAGEPADDING*2))
		r = int(1 + rand_float(rand_float(self.hb.s*0.4)))
		self.splatters.append((x, y, r,))
		if len(self.splatters) > self.highhp:
			self.splatters = self.splatters[:-self.highhp]
		self.hex.repaint()
		if self.hp <= 0:
			self.die()

	def die(self):
		Attackable.die(self)
		# remove entirely
		self.hex.items.remove(self)
		self.hex.repaint()

class Creature(Attackable, Active):
	def __init__(self, turnman, hex, hp, actpoints, attackp, defensep, damagep=1, numsplatters=DEFAULT_NUM_SPLATTERS, color=Color.black, bloodcolor=Color.red, deadimage=None):
		"""
		@param hex the hex the creature inhabits
		@param hp starting hit points
		@param actpoints action points (per turn)
		"""
		# print "Creature.__init__(%s@%s)" % (self.__class__.__name__, id(self),)
		self.turnman = turnman
		self.actp = actpoints
		self.attackp = attackp
		self.damagep = damagep
		self.actpleft = 0 # invalid value
		turnman.game.creatures[color].append(self)
		turnman.register_regular_bot_event(self.handle_new_turn, priority="first")
		Active.__init__(self)
		Attackable.__init__(self, hp=hp, defensep=defensep, numsplatters=numsplatters, bloodcolor=bloodcolor, deadimage=deadimage)
		Graphical.__init__(self, turnman.game, hex, treadable="none", color=color)

	def __repr__(self):
		if self.is_dead():
			return "dead " + Item.__repr__(self)
		else:
			return Item.__repr__(self)

	def price(self):
		return (self.attackp + 3) * self.actp + self.hp + (self.defensep + 3)

	def paint(self, g):
		Graphical.paint(self, g)
		Attackable.paint(self, g)
		Active.paint(self, g)

	def is_foe(self, item):
		return isinstance(item, Creature) and (item.color is not self.color)

	def handle_new_turn(self):
		# print "%s.handle_new_turn()" % self
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
		self.turnman.select_next_creature_or_end_turn()

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
			self.act_and_be_done_if_done(self.move, kwargs={'hex': hex})
			return

		# Else, if you can attack an item, attack the first one it (top items first):
		for idx in range(len(hex.items)-1, -1, -1):
			item = hex.items[idx]
			if isinstance(item, Attackable):
				# WHAH?  Won't let me MOVE there, EH?  We'll see about that!
				# print "attacking %s" % item
				self.act_and_be_done_if_done(self.attack, kwargs={'defender': item})
				return

		assert self.actpleft > 0, "self: %s, self.actpleft: %s, traceback.extract_stack(): %s" % (self, self.actpleft, traceback.extract_stack(),)

		# Else, you can't do anything to that hex.
		self.handle_cant_act()

	def act_and_be_done_if_done(self, act, args=(), kwargs={}):
		assert self.actpleft > 0, "self: %s, self.actpleft: %s, traceback.extract_stack(): %s" % (self, self.actpleft, traceback.extract_stack(),)
		self.actpleft -= 1
		assert self.actpleft >= 0, "self: %s, self.actpleft: %s, traceback.extract_stack(): %s" % (self, self.actpleft, traceback.extract_stack(),)
		apply(act, args, kwargs)
		assert self.actpleft >= 0, "self: %s, self.actpleft: %s, traceback.extract_stack(): %s" % (self, self.actpleft, traceback.extract_stack(),)
		self.be_done_if_done()

	def act(self, act, args=(), kwargs={}):
		assert self.actpleft > 0, "self: %s, self.actpleft: %s, traceback.extract_stack(): %s" % (self, self.actpleft, traceback.extract_stack(),)
		self.actpleft -= 1
		assert self.actpleft >= 0, "self: %s, self.actpleft: %s, traceback.extract_stack(): %s" % (self, self.actpleft, traceback.extract_stack(),)
		apply(act, args, kwargs)
		assert self.actpleft >= 0, "self: %s, self.actpleft: %s, traceback.extract_stack(): %s" % (self, self.actpleft, traceback.extract_stack(),)

	def be_done_if_done(self):
		assert self.actpleft >= 0, "self: %s, self.actpleft: %s, traceback.extract_stack(): %s" % (self, self.actpleft, traceback.extract_stack(),)
		if self.actpleft <= 0:
			self.turnman.select_next_creature_or_end_turn()

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
		roll = d6() + d6() + d6()
		attackval = roll + self.attackp
		print "attack: %2s + %2s = %2s " % (roll, self.attackp, attackval,),
		defender.handle_attack(attackval, self.damagep, self)

	def key_typed(self, e):
		c = e.getKeyChar()
		if c == 'w':
			self.user_act(self.hex.get_nw())
		elif c == 'e':
			self.user_act(self.hex.get_ne())
		elif c == 'a':
			self.user_act(self.hex.get_w())
		elif c == 'd':
			self.user_act(self.hex.get_e())
		elif c == 'z':
			self.user_act(self.hex.get_sw())
		elif c == 'x':
			self.user_act(self.hex.get_se())
		elif c == 's':
			self.user_act(self.hex)
		elif c == 'u':
			self.unselect()
		elif c == 'n':
			self.turnman.select_next_creature_or_end_turn()
		elif c == ' ':
			self.pass()

class Ogre(Creature, Big):
	"""
	An ogre is very tough and powerful and it eats corpses for extra hit points.

	hp: 3
	actpoints: 1
	attackp: 3
	defensep: 2
	"""
	def __init__(self, game, hex, color=Color.red):
		# print "Ogre.__init__(%s@%s)" % (self.__class__.__name__, id(self),)
		Creature.__init__(self, game.turnmans[color], hex, hp=3, actpoints=1, attackp=3, defensep=2, damagep=2, color=color, bloodcolor=Color.red)
		Big.__init__(self)

	def move(self, hex):
		Creature.move(self, hex)
		for i in self.hex.items:
			if isinstance(i, Tree) or (isinstance(i, Creature) and i.is_dead()):
				self.eat(i)

	def eat(self, item):
		print "OGRE EAT %s" % item
		item.destroy()
		self.hp += 1
		if self.hp > self.highhp:
			self.highhp = self.hp
		self.repaint()

class Tree(Graphical):
	def __init__(self, game, hex, treadable="all", color=Color.black):
		# print "Tree.__init__(%s@%s)" % (self.__class__.__name__, id(self),)
		Graphical.__init__(self, game, hex, treadable=treadable, color=color)
		self.age = 0
		for adjhex in hex.get_adjacent_hexes():
			# Destroy any adjacent Wall.
			[x.destroy() for x in adjhex.get_all(Wall)]

	def get_older(self):
		self.age += 1
		if (self.age > 8) and not self.hex.contains_a(Creature):
			Pixie(self.game, self.hex)
			self.destroy()
		self.repaint()

	def paint(self, g):
		Graphical.paint(self, g)
		mg = g.create()
		mg.setColor(Color.black)
		mg.draw(self.hb.treepoly)
		mg.setColor(Color.green)
		mg.fill(self.hb.treeinnerpoly)

		strage = str(self.age)
		# (font, ox, oy,) = self.hb.find_fitting_font_nw_vertex(strage, mg)
		(font, ox, oy,) = self.hb.find_fitting_font_bottom_half(strage, mg)
		mg.setColor(Color.gray)
		mg.setFont(font)
		mg.drawString(strage, ox, oy)

class KingTree(Tree):
	def __init__(self, game, hex, treadable="all", color=Color.black):
		Tree.__init__(self, game, hex, treadable=treadable, color=color)

class Pixie(Creature, Flying):
	"""
	A pixie is very fast.

	hp: 1
	actpoints: 3
	attackp: 0
	defensep: 0
	"""
	def __init__(self, game, hex, color=Color.white, hp=1, bloodcolor=Color(0.7, 1.0, 0.3)):
		# print "Pixie.__init__(%s@%s)" % (self.__class__.__name__, id(self),)
		self.carrieditems = []
		Creature.__init__(self, game.turnmans[color], hex, hp=hp, actpoints=3, attackp=0, defensep=0, color=color, bloodcolor=bloodcolor)
		Flying.__init__(self)

	def price(self):
		return 10

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

class Dwarf(Creature):
	"""
	A dwarf is tough and gets an extra defense point against Big attackers.  

	hp: 3
	actpoints: 1
	attackp: 2
	defensep: 1
	"""
	def __init__(self, game, hex, color=Color.blue):
		Creature.__init__(self, game.turnmans[color], hex, hp=3, actpoints=1, attackp=2, defensep=2, color=color, bloodcolor=Color.red)

	def handle_attack(self, attackval, damage, attacker):
		if isinstance(attacker, Big):
			self.defensep += 1
			Attackable.handle_attack(self, attackval, damage, attacker)
			self.defensep -= 1
		else:
			Attackable.handle_attack(self, attackval, damage, attacker)

class Skeleton(Creature):
	"""
	A skeleton is weak but fast.

	hp: 1
	actpoints: 2
	attackp: 1
	defensep: 1
	"""
	def __init__(self, game, hex, color=Color.blue):
		Creature.__init__(self, game.turnmans[color], hex, hp=1, actpoints=2, attackp=1, defensep=1, color=color, bloodcolor=Color.red)

class LightningAttack(Runnable):
	def __init__(self, hb, source, targethex, be_done_func=None):
		self.hb = hb
		self.source = source
		self.targethex = targethex
		self.be_done_func = be_done_func
		self.attacklets = 0
		# calculate shortest path from here to there
		self.path = HexBoard.shortest_path((source.hex.hx, source.hex.hy,), (targethex.hx, targethex.hy,), 8)
		self.go()

	def paint(self, g):
		pass

	def go(self):
		# schedule the first attacklet
		SwingUtilities.invokeLater(self)

	def attacklet(self):
		self.attacklets += 1
		for hc in self.path:
			hex = self.hb.hexes.get(hc)
			if hex is not None:
				hex.highlight()
				hex.repaint()
				for item in hex.items:
					if isinstance(item, Attackable) and not item.is_dead():
						item.handle_attack(15, 1, self)
						return

	def run(self):
		self.attacklet()
		if self.attacklets < 3:
			# schedule another attacklet
			SwingUtilities.invokeLater(self)
		else:
			# done.
			for hc in self.path:
				hex = self.hb.hexes.get(hc)
				if hex is not None:
					hex.unhighlight()
					hex.repaint()

			# call back to do whatever comes next
			# print "%s.%s()" % (self, self.be_done_func,)
			if self.be_done_func:
				self.be_done_func()

class Wizard(Creature):
	"""
	A wizard is weak, slow, and vulnerable, but he casts spells!

	hp: 1
	actpoints: 1
	attackp: -2
	defensep: -2
	"""
	def __init__(self, game, hex, color=Color.blue):
		Creature.__init__(self, game.turnmans[color], hex, hp=1, actpoints=1, attackp=-2, defensep=-2, color=color, bloodcolor=Color.red)
		self.waitingfortarget = false

	def price(self):
		return 35

	def cast_lightning_bolt(self):
		print "%s.cast_lightning_bolt()" % self
		self.waitingfortarget = true
		self.completionfunc = (self.complete_cast_lightning_bolt, (), {},)

	def complete_cast_lightning_bolt(self, hex):
		print "hex: %s, ZZZZzzzap!!!" % hex
		la = LightningAttack(self.hb, self, hex, self.be_done_if_done)

	def key_typed(self, e):
		c = e.getKeyChar()
		if c == 's':
			print "%s trying to cast lightning bolt!" % self
			for adjhex in self.hex.get_adjacent_hexes():
				for item in adjhex.items:
					if isinstance(item, Creature) and not item.is_dead() and item.is_foe(self):
						print "Can't cast -- adjacent to enemy!"
						return
			self.cast_lightning_bolt()
		else:
			Creature.key_typed(self, e)

	def user_act(self, hex):
		if hex is None:
			return

		# If it is ourself, then ignore this event.
		if hex is self.hex:
			return

		assert self.actpleft >= 0, "self: %s, self.actpleft: %s, traceback.extract_stack(): %s" % (self, self.actpleft, traceback.extract_stack(),)
		if self.actpleft <= 0:
			print "can't do any more acts this turn"
			return self.handle_cant_act()

		assert self.actpleft > 0, "self: %s, self.actpleft: %s, traceback.extract_stack(): %s" % (self, self.actpleft, traceback.extract_stack(),)

		if self.waitingfortarget:
			self.waitingfortarget = false
			kw = self.completionfunc[2]
			kw['hex'] = hex
			self.act(self.completionfunc[0], self.completionfunc[1], kw)
		else:
			Creature.user_act(self, hex)

class Scroll(Graphical):
	def __init__(self, game, hex, color=Color.white, image=None):
		Graphical.__init__(self, game, hex, treadable="any", color=color)

	def paint(self, g):
		mg = g.create()
		mg.setColor(self.color)
		mg.fill(self.hb.scrollpoly)
