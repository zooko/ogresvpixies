Index: GamePieces.py
===================================================================
RCS file: /cvsroot/OvP/GamePieces.py,v
retrieving revision 1.4
diff -u -d -r1.4 GamePieces.py
--- GamePieces.py	25 Jan 2002 15:27:33 -0000	1.4
+++ GamePieces.py	25 Jan 2002 15:57:43 -0000
@@ -238,6 +238,8 @@
 		y = int(self.IMAGEPADDING + rand_float(self.hb.h - self.IMAGEPADDING*2))
 		r = int(1 + rand_float(self.hb.s*0.4))
 		self.splatters.append((x, y, r,))
+		if len(self.splatters) > self.highhp:
+			self.splatters = self.splatters[:-self.highhp]
 		self.hex.repaint()
 		if self.hp == 0:
 			self.die()
@@ -398,9 +400,11 @@
 			self.unselect()
 			self.game.select_next_creature()
 		self.game.turnmanager.go_if_ready() # If there are no more acts that need to be decided, then go ahead and resolve acts now.
-
+		
 	def move(self, hex):
-		# exit the old hex, move onto the top of the stack of the new one, step on objects, repaint
+		"""
+		exit the old hex, move onto the top of the stack of the new one, check for ZoC, repaint
+		"""
 		self.hex.items.remove(self)
 		hex.items.append(self)
 		self.repaint() # repaint the old
@@ -450,12 +454,12 @@
 		# print "Tree.__init__(%s@%s)" % (self.__class__.__name__, id(self),)
 		Graphical.__init__(self, ovp, hex, treadable=treadable, color=color)
 		for adjhex in hex.get_adjacent_hexes():
-			# Now check if this new tree just formed a Broken Pixie Ring.  If so, create a 2-Pixie there.
+			# Now check if this new tree just formed a Broken Pixie Ring.  If so, create a 3-Pixie there.
 			if adjhex.is_center_of_broken_pixie_ring():
-				# WHOO!  A BROKEN PIXIE RING!  Remove any Stones and create a 2-Pixie in the center of the Fairie Ring.
+				# WHOO!  A BROKEN PIXIE RING!  Remove any Stones and create a 3-Pixie in the center of the Fairie Ring.
 				[x.destroy() for x in adjhex.get_all(Tree)]
 				[x.destroy() for x in adjhex.get_all(Stone)]
-				Pixie(ovp, adjhex, hp=2)
+				Pixie(ovp, adjhex, hp=3)
 
 			# Now check if this new tree just formed a Pixie Ring.  If so, create a Pixie there.
 			if adjhex.is_center_of_pixie_ring():
@@ -475,9 +479,36 @@
 class Pixie(Creature, Flying):
 	def __init__(self, ovp, hex, color=Color.WHITE, hp=1, bloodcolor=Color(0.7, 1.0, 0.3)):
 		# print "Pixie.__init__(%s@%s)" % (self.__class__.__name__, id(self),)
+		self.carrieditems = []
 		Creature.__init__(self, ovp, hex, hp=hp, actpoints=3, attack=1, defense=1, color=color, bloodcolor=bloodcolor)
 		Flying.__init__(self)
 
+	def garden(self):
+		"""
+		If there are any underlying trees, destroy them.
+		If there is some non-Tree (and non-Creature!) underlying item, pick it up.
+		If there is no underlying item, and you are carrying an item, drop it.
+		"""
+		[x.destroy() for x in self.hex.get_all(Tree)]
+		items = self.hex.items[:] # copy the list
+		items.reverse() # reverse it
+		for item in items:
+			if not isinstance(item, Tree) and not isinstance(item, Creature):
+				self.carrieditems.append(item)
+				self.hex.items.remove(item)
+				# While being carried, the item has no `self.hex'!
+				item.hex = None
+				self.repaint()
+				self.hex.repaint()
+				return
+
+		if len(self.carrieditems) > 0:
+			item = self.carrieditems.pop(0)
+			self.hex.items.append(item)
+			item.hex = self.hex
+			self.repaint()
+			self.hex.repaint()
+
 	def user_act(self, hex):
 		"""
 		The user has selected you, and then selected `hex'.  Try to do something to it!
@@ -487,10 +518,9 @@
 		if hex is None:
 			return
 
-		# If it is ourself, then destroy any underlying trees or rocks (do gardening).
+		# If it is ourself, then do gardening.
 		if hex is self.hex:
-			[x.destroy() for x in hex.get_all(Tree)]
-			[x.destroy() for x in hex.get_all(Stone)]
+			self.garden()
 		else:
 			Creature.user_act(self, hex)
 
Index: OvP.py
===================================================================
RCS file: /cvsroot/OvP/OvP.py,v
retrieving revision 1.6
diff -u -d -r1.6 OvP.py
--- OvP.py	25 Jan 2002 15:27:33 -0000	1.6
+++ OvP.py	25 Jan 2002 16:14:11 -0000
@@ -57,7 +57,7 @@
 
 NUM_STARTING_OGRES=2
 NUM_STARTING_PIXIES=2
-NUM_STARTING_TREES=3
+NUM_STARTING_TREES=4
 
 class OvPHex(HexBoard.Hex):
 	def __init__(self, hb, hx, hy, bordercolor=Color.GREEN, bgcolor=Color.BLACK):
@@ -141,9 +141,14 @@
 					if opphex is not None:
 						if opphex.is_empty():
 							Stone(self, opphex)
-						predhex = opphex.get_circle_predecessor(emptyhex)
-						if (predhex is not None) and predhex.is_empty():
-							Stone(self, predhex)
+						# for longer runs of stones:
+						# nexthex = emptyhex.get_opposite(opphex)
+						# if (nexthex is not None) and nexthex.is_empty():
+						# 	Stone(self, nexthex)
+						# for coriolis stones:
+						# predhex = opphex.get_circle_predecessor(emptyhex)
+						# if (predhex is not None) and predhex.is_empty():
+						# 	Stone(self, predhex)
 					return
 		# If there were no appropriate spots.  No trees grow!
 
@@ -154,15 +159,15 @@
 
 	def init_creatures(self):
 		for i in range(NUM_STARTING_OGRES):
-			hex = self.hb.get_empty_hex(maxhx=self.boardwidth/2)
+			hex = self.hb.get_empty_hex(maxhx=self.boardwidth/3)
 			if hex is not None:
 				Ogre(self, hex)
 		for i in range(NUM_STARTING_PIXIES):
-			hex = self.hb.get_empty_hex(minhx=self.boardwidth/3+2)
+			hex = self.hb.get_empty_hex(minhx=self.boardwidth/3)
 			if hex is not None:
 				Pixie(self, hex)
 		for i in range(NUM_STARTING_TREES):
-			hex = self.hb.get_empty_hex(minhx=self.boardwidth*1/3)
+			hex = self.hb.get_empty_hex(minhx=self.boardwidth/3)
 			if hex is not None:
 				Tree(self, hex)
 
