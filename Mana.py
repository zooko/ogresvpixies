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
__cvsid = '$Id: Mana.py,v 1.1 2002/02/09 22:46:13 zooko Exp $'

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

class Mana:
	"""
	Mana crawls around and if it hits another Mana of any color they mutually annihilate.  But if two Mana of the same color are adjacent to one another then they spawn a whole bunch of new mana.
	"""
	def __init__(self, hex, color):
		self.hex = hex
		self.color = color

	def move(self):
		adjhexes = rand_rotate(self.hex.get_adjacent_hexes())
		for adjhex in adjhexes:
			n

			for item in adjhex.items:
				if isinstance(item, Mana) and (item.color is self.color):
					# spawn!
					k
			
		
