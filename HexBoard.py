CVS_ID = '$Id: HexBoard.py,v 1.3 2002/02/09 22:46:13 zooko Exp $'

import java
from java.awt import *
from java.awt.event import *
from java.awt.geom import *
from javax.swing import *
from javax.swing.text import *

import math
from types import *

from util import *

true = 1
false = 0

LINEWIDTH=2 # ???

# Hex instance sequence functions:
def all_contain_a(hs, klass):
	return len(filter(None, [(h is None) or h.contains_a(klass) for h in hs])) == len(hs)

def any_contain_a(hs, klass):
	return len(filter(None, [(h is None) or h.contains_a(klass) for h in hs])) != 0

def all_contain_only(hs, klass):
	return len(filter(None, [(h is None) or h.contains_only(klass) for h in hs])) == len(hs)

def all_are_empty(hs):
	return len(filter(None, [(h is None) or h.is_empty() for h in hs])) == len(hs)

# Coordinate functions:
def nw_of(coord):
	return (coord[0] - 1 + coord[1]%2, coord[1] + 1,)

def ne_of(coord):
	return (coord[0] + coord[1]%2, coord[1] + 1,)

def e_of(coord):
	return (coord[0] + 1, coord[1],)

def w_of(coord):
	return (coord[0] - 1, coord[1],)

def se_of(coord):
	return (coord[0] + coord[1]%2, coord[1] - 1,)

def sw_of(coord):
	return (coord[0] - 1 + coord[1]%2, coord[1] - 1,)

# Coordinate-based path related functions:
def distance(a, b):
	"""Returns the distance, in hexes, between two hex arguments."""
	path = shortest_path(a, b, hopsleft=30)
	assert path[-1] is not None, "ACK!  Bad distance, %s, between %s and %s; path: %s" % (`len(path)`, `a`, `b`, `path`)
	return len(path)

def shortest_path(src, dst, hopsleft=None):
	"""
	shortest_path(src, dst, hopsleft=None) -> path

	Returns a sequence of hex coordinates.

	src and dst are tuples of hex coordinates.
	hopsleft is None or a positive integer; if an integer the path stops after that many hops.

	The return value is a sequence of hex coordinate tuples.  If the maximum
	number of hops was reached, the last element of path is None, else it is dst.
	"""
	# This first implementation is a slow, recursive approach.

	if hopsleft is not None:
		hopsleft -= 1
		if hopsleft == 0:
			return (None,) # signify the path was too long.
		
	dx = (src[0] - dst[0])
	dy = (src[1] - dst[1])

	#print "shortest_path: %r hopsleft %s -> %s | dx: % 4s | dy: % 4s" % (hopsleft, repr(src), repr(dst), dx, dy),

	if dst == src:
		#print 'Finished.'
		return ()
	elif dx == 0:
		#print "Same column, which way?", src[1] % 2
		if dy < 0:
			if src[1] % 2 == 1:
				#print 'NW'
				return (nw_of(src),) + shortest_path(nw_of(src), dst, hopsleft)
			else:
				#print 'NE'
				return (ne_of(src),) + shortest_path(ne_of(src), dst, hopsleft)
		else:
			if src[1] % 2 == 1:
				#print 'SW'
				return (sw_of(src),) + shortest_path(sw_of(src), dst, hopsleft)
			else:
				#print 'SE'
				return (se_of(src),) + shortest_path(se_of(src), dst, hopsleft)
	elif abs(dx) <= abs(dy):
		if dx < 0 and dy < 0:
			#print 'NE'
			return (ne_of(src),) + shortest_path(ne_of(src), dst, hopsleft)
		elif dx < 0 and dy > 0:
			#print 'SE'
			return (se_of(src),) + shortest_path(se_of(src), dst, hopsleft)
		elif dx > 0 and dy < 0:
			#print 'NW'
			return (nw_of(src),) + shortest_path(nw_of(src), dst, hopsleft)
		else: #elif dx > 0 and dy > 0:
			#print 'SW'
			return (sw_of(src),) + shortest_path(sw_of(src), dst, hopsleft)
	else:
		if dx < 0:
			#print 'E'
			return (e_of(src),) + shortest_path(e_of(src), dst, hopsleft)
		else:
			#print 'W'
			return (w_of(src),) + shortest_path(w_of(src), dst, hopsleft)

class Hex:
	def __init__(self, hb, hx, hy, bordercolor=Color.green, bgcolor=Color.black, hicolor=Color.pink):
		self.bordercolor = bordercolor
		self.bgcolor = bgcolor
		self.hicolor = hicolor
		self.items = [] # a list of items (the first item is drawn first, so higher-indexed items might overwrite it)
		self.hb = hb
		self.hx = hx
		self.hy = hy
		self.hb.hexes[(hx, hy,)] = self
		self.cx = int(self.hb.cxoffset + ((hx + ((hy % 2)*0.5)) * self.hb.w))
		self.cy = int(self.hb.cyoffset - (hy*0.75*self.hb.h))
		self.highlightflag = 0

		self.hexonboardpoly = Polygon(self.hb.hexpoly.xpoints, self.hb.hexpoly.ypoints, self.hb.hexpoly.npoints)
		self.hexonboardpoly.translate(self.cx, self.cy)
		self.boundingrect = Rectangle(self.cx, self.cy, self.hb.wplusline, self.hb.hplusline)

	def __repr__(self):
		return "hex(%d, %d)" % (self.hx, self.hy,)

	def highlight(self):
		"""Sets the highlight flag of this hex."""
		self.highlightflag = 1
		self.repaint()

	def unhighlight(self):
		"""Clears the highlight flag of this hex."""
		self.highlightflag = 0
		self.repaint()

	def is_highlighted(self):
		return self.highlightflag
		
	def contains(self, pt):
		"""
		graphics...
		"""
		return self.hexonboardpoly.contains(pt)

	def contains_a(self, klass):
		return len(self.get_all(klass)) > 0
	
	def contains_only(self, klass):
		return len(filter(lambda x, klass=klass: not isinstance(x, klass), self.items)) == 0

	def is_empty(self):
		return len(self.items) == 0

	def get_all(self, klass):
		return filter(lambda x, klass=klass: isinstance(x, klass), self.items)

	def intersects(self, rect):
		return self.hexonboardpoly.intersects(rect)

	def is_adjacent(self, otherhex):
		return ((abs(otherhex.hx-self.hx)==1) and (otherhex.hy==self.hy)) or ((abs(otherhex.hy-self.hy)==1) and (((otherhex.hx==self.hx)) or (otherhex.hx-self.hx==((self.hy % 2)*2-1))))

	def is_adjacent_to_a(self, klass):
		return self.count_adjacent(klass) > 0

	def count_adjacent(self, klass):
		sum = 0
		for adj in self.get_adjacent_hexes():
			if adj.contains_a(klass):
				sum += 1
		return sum

	def get_adjacent_hexes(self):
		"""
		excludes Nones
		"""
		res = []
		for (dx, dy,) in ( (-1, 0), (1, 0), (0, 1), (0, -1), (((self.hy % 2)*2-1), 1), (((self.hy % 2)*2-1), -1) ,):
			if self.hb.hexes.has_key((self.hx+dx, self.hy+dy,)):
				res.append(self.hb.hexes[(self.hx+dx, self.hy+dy,)])
		return res

	def get_ordered_adjacent_hexes(self):
		"""
		includes Nones
		"""
		return (self.get_nw(), self.get_ne(), self.get_e(), self.get_se(), self.get_sw(), self.get_w(),)

	def get_east_trio(self):
		return self.get_ordered_adjacent_hexes()[::2]

	def get_west_trio(self):
		return self.get_ordered_adjacent_hexes()[1::2]

	def get_circle_successor(self, middlehex):
		"""
		@returns the hex that is the next hex from `self' in the circle that surrounds `middlehex' (in a clockwise direction)

		@precondition `middlehex' must be adjacent to this hex
		"""
		assert self.is_adjacent(middlehex)
		if middlehex.get_nw() is self:
			return middlehex.get_ne()
		if middlehex.get_ne() is self:
			return middlehex.get_e()
		if middlehex.get_e() is self:
			return middlehex.get_se()
		if middlehex.get_se() is self:
			return middlehex.get_sw()
		if middlehex.get_sw() is self:
			return middlehex.get_w()
		if middlehex.get_w() is self:
			return middlehex.get_nw()
		
	def get_circle_predecessor(self, middlehex):
		"""
		@returns the hex that is the next hex from `self' in the circle that surrounds `middlehex' (in a counter-clockwise direction)

		@precondition `middlehex' must be adjacent to this hex
		"""
		assert self.is_adjacent(middlehex)
		if middlehex.get_nw() is self:
			return middlehex.get_w()
		if middlehex.get_ne() is self:
			return middlehex.get_nw()
		if middlehex.get_e() is self:
			return middlehex.get_ne()
		if middlehex.get_se() is self:
			return middlehex.get_e()
		if middlehex.get_sw() is self:
			return middlehex.get_se()
		if middlehex.get_w() is self:
			return middlehex.get_sw()

	def get_opposite(self, middlehex):
		"""
		@returns the hex that lies directly across `middlehex' from this hex, or None if none

		@precondition `middlehex' must be adjacent to this hex
		"""
		assert self.is_adjacent(middlehex)
		if middlehex.get_nw() is self:
			return middlehex.get_se()
		if middlehex.get_ne() is self:
			return middlehex.get_sw()
		if middlehex.get_e() is self:
			return middlehex.get_w()
		if middlehex.get_se() is self:
			return middlehex.get_nw()
		if middlehex.get_sw() is self:
			return middlehex.get_ne()
		if middlehex.get_w() is self:
			return middlehex.get_e()

	def get_nw(self):
		return self.hb.hexes.get(nw_of((self.hx, self.hy,)))

	def get_ne(self):
		return self.hb.hexes.get(ne_of((self.hx, self.hy,)))

	def get_e(self):
		return self.hb.hexes.get(e_of((self.hx, self.hy,)))

	def get_w(self):
		return self.hb.hexes.get(w_of((self.hx, self.hy,)))

	def get_se(self):
		return self.hb.hexes.get(se_of((self.hx, self.hy,)))

	def get_sw(self):
		return self.hb.hexes.get(sw_of((self.hx, self.hy,)))

	def paint(self, g):
		g.setColor(self.is_highlighted() and self.hicolor or self.bgcolor)
		g.fill(self.hb.hexpoly)
		g.setColor(self.bordercolor)
		g.draw(self.hb.hexpoly)
		for i in self.items:
			try:
				i.paint(g)
			except:
				print "i: %s" % i
				raise

	def repaint(self):
		# Tell the HexBoard to repaint only this hex's bounding rectangle:
		self.hb.repaint(self.boundingrect)

		# The short-circuit way: just repaint that hex.  We do this by adding the hex coords to our "hexrepaintqueue" and then signalling ourselves that this is a "hexrepaint" call by asking to repaint a rectangle that is a crummy little corner of the board.
		# self.hb.hexrepaintqueue.append((hxloc, hyloc,))
		# self.hb.repaint(self.signalrect)
		# Hrm.  Whoops -- that signalling mechanism doesn't work because only the signalrect is included in the clipping.  Hrm....  Okay after reading lots of docs about this, it looks like "incremental painting" as its called, just isn't possible in Swing (without digging in too deep under the Swing abstraction).  Bummer.
		
class HexBoard(JPanel):
	def __init__(self, cxoffset=10, cyoffset=10, scale=100):
		JPanel.__init__(self)
		self.setOpaque(true)
	
		self.cxoffset = cxoffset
		self.cyoffset = cyoffset
		self.s = scale
		self.w = int(self.s*math.sqrt(3))
		self.h = self.s*2
		self.wplusline = self.w+LINEWIDTH
		self.hplusline = self.h+LINEWIDTH

		self.hexpoly = Polygon()
		self.hexpoly.addPoint(self.w/2, 0)
		self.hexpoly.addPoint(self.w, self.h/4)
		self.hexpoly.addPoint(self.w, (self.h*3)/4)
		self.hexpoly.addPoint(self.w/2, self.h)
		self.hexpoly.addPoint(0, (self.h*3)/4)
		self.hexpoly.addPoint(0, self.h/4)

		self.hexinnerpoly = Polygon()
		hyp = self.s/8.0
		adj = hyp*math.sqrt(3)/2.0
		opp = hyp/2.0
		self.hexinnerpoly.addPoint(int(self.w/2), int(0+hyp))
		self.hexinnerpoly.addPoint(int(self.w-adj), int(self.h/4+opp))
		self.hexinnerpoly.addPoint(int(self.w-adj), int((self.h*3)/4-opp))
		self.hexinnerpoly.addPoint(int(self.w/2), int(self.h-hyp))
		self.hexinnerpoly.addPoint(int(0+adj), int((self.h*3)/4-opp))
		self.hexinnerpoly.addPoint(int(0+adj), int(self.h/4+opp))

		self.hextophalfpoly = Polygon()
		self.hextophalfpoly.addPoint(self.w/2, 0)
		self.hextophalfpoly.addPoint(self.w, self.h/4)
		self.hextophalfpoly.addPoint(self.w, self.h/2)
		self.hextophalfpoly.addPoint(0, self.h/2)
		self.hextophalfpoly.addPoint(0, self.h/4)

		self.hexbottomhalfpoly = Polygon()
		self.hexbottomhalfpoly.addPoint(self.w, self.h/2)
		self.hexbottomhalfpoly.addPoint(self.w, (self.h*3)/4)
		self.hexbottomhalfpoly.addPoint(self.w/2, self.h)
		self.hexbottomhalfpoly.addPoint(0, (self.h*3)/4)
		self.hexbottomhalfpoly.addPoint(0, self.h/2)

		self.treepoly = Polygon()
		TREEHEIGHT = int(self.h*0.4)
		TREEWIDTH = int(self.w*0.3)
		self.treepoly.addPoint(self.w/2, (self.h-TREEHEIGHT)/2)
		self.treepoly.addPoint((self.w+TREEWIDTH)/2, (self.h+TREEHEIGHT)/2)
		self.treepoly.addPoint((self.w-TREEWIDTH)/2, (self.h+TREEHEIGHT)/2)
		self.treeinnerpoly = Polygon()
		self.treeinnerpoly.addPoint(self.w/2, (self.h-TREEHEIGHT)/2+1)
		self.treeinnerpoly.addPoint((self.w+TREEWIDTH)/2-1, (self.h+TREEHEIGHT)/2-1)
		self.treeinnerpoly.addPoint((self.w-TREEWIDTH)/2+1, (self.h+TREEHEIGHT)/2-1)

		self.scrollpoly = Polygon()
		SCROLLHEIGHT = int(self.h*0.4)
		SCROLLWIDTH = int(self.w*0.3)
		self.scrollpoly.addPoint(self.w/2, (self.h-SCROLLHEIGHT)/2)
		self.scrollpoly.addPoint(self.w/2+self.s/4, (self.h-SCROLLHEIGHT)/2+self.s/8)
		self.scrollpoly.addPoint(self.w/2+self.s/4, (self.h-SCROLLHEIGHT)/2+SCROLLHEIGHT+self.s/8)
		self.scrollpoly.addPoint(self.w/2, (self.h-SCROLLHEIGHT)/2+SCROLLHEIGHT)

		self.hexes = {} # key: (hx, hy,), value = instance of Hex

	def get(self, hc):
		if is_type(hc, SequenceTypes) and len(hc) == 2:
			pass # no change needed.
		elif hasattr(hc, 'hex'):
			hc = hc.hex
		else:
			raise Exception("Unknown hex indicator: %s" % repr(hc))

		if is_type(hc, Hex):
			# This is kinda funny; for an example, see HexBoard.highlight_path().
			hc = (hc.hx, hc.hy)

		return self.hexes.get(hc)

	def get_many(self, sequence):
		return map(self.get, sequence)

	def pick_hex(self, pt):
		"""
		@return hex that the cartesian coordinate `pt' falls into, or None if none
		"""
		# XXX TODO: do this in a nice efficient manner.  :-)
		for hex in self.hexes.values():
			if hex.contains(pt):
				return hex
		return None

	def paintComponent(self, g):
		self.super__paintComponent(g)

		cliprect = g.getClipBounds()
		# print "HB.paintComponent() cliprect: ", cliprect
		# XXX TODO: pick hexes more efficiently.  (In case we need to have 1000x1000 hexes visible at once.  ;-))
		for hex in self.hexes.values():
			if hex.intersects(cliprect):
				# print "cliprect: %s, hex: %s" % (cliprect, hex,)
				# newg = g.create(hex.boundingrect) # Why isn't this supported by the Java API?  :-<
				newg = g.create(hex.boundingrect.x, hex.boundingrect.y, hex.boundingrect.width, hex.boundingrect.height)
				hex.paint(newg)

	def unhighlight_all(self):
		[hex.unhighlight() for hex in self.hexes.values()]

	def get_empty_hex(self, minhx=None, minhy=None, maxhx=None, maxhy=None):
		"""
		@return a randomly chosen empty hex or None if there are no more empty hexes
		"""
		for hex in rand_rotate(self.hexes.values()):
			if hex.is_empty() and ((minhx is None) or (hex.hx >= minhx)) and ((minhy is None) or (hex.hy >= minhy)) and ((maxhx is None) or (hex.hx <= maxhx)) and ((maxhy is None) or (maxhy <= hex.hy)):
				return hex
		return None

	def find_fitting_font_nw_vertex(self, stro, g):
		fontFits=false
		maxFontSize = 14
		minFontSize = 6
		currentFont = Font("SansSerif", Font.PLAIN, maxFontSize)
		currentMetrics = g.getFontMetrics(currentFont)
		size = currentFont.getSize()
		name = currentFont.getName()
		style = currentFont.getStyle()
		cw = currentMetrics.stringWidth(stro)
		ch = currentMetrics.getHeight()
		ox = 4
		oy = self.h * 0.5 - 1

		while not fontFits:
			# print ox, oy, cw, ch
			if self.hextophalfpoly.contains(ox, oy-ch, cw, ch):
				fontFits=true
			elif size <= minFontSize:
				print "warning, couldn't fit words..."
				fontFits=true
			else:
				currentFont = Font(name, style, size-1)
				currentMetrics = g.getFontMetrics(currentFont)
				size = currentFont.getSize()
				name = currentFont.getName()
				style = currentFont.getStyle()
				cw = currentMetrics.stringWidth(stro)
				ch = currentMetrics.getHeight()
				ox = 4
				oy = self.h * 0.5 - 1
		return (currentFont, ox, oy,)

	def find_fitting_font_top_half(self, stro, g):
		fontFits=false
		maxFontSize = 14
		minFontSize = 6
		currentFont = Font("SansSerif", Font.PLAIN, maxFontSize)
		currentMetrics = g.getFontMetrics(currentFont)
		size = currentFont.getSize()
		name = currentFont.getName()
		style = currentFont.getStyle()
		cw = currentMetrics.stringWidth(stro)
		ch = currentMetrics.getHeight()
		ox = (self.w - cw) * 0.5
		oy = self.h * 0.5 - 1

		while not fontFits:
			# print ox, oy, cw, ch
			if self.hextophalfpoly.contains(ox, oy-ch, cw, ch):
				fontFits=true
			elif size <= minFontSize:
				print "warning, couldn't fit words..."
				fontFits=true
			else:
				currentFont = Font(name, style, size-1)
				currentMetrics = g.getFontMetrics(currentFont)
				size = currentFont.getSize()
				name = currentFont.getName()
				style = currentFont.getStyle()
				cw = currentMetrics.stringWidth(stro)
				ch = currentMetrics.getHeight()
				ox = (self.w - cw) * 0.5
				oy = self.h * 0.5 - 1
		return (currentFont, ox, oy,)

	def find_fitting_font_bottom_half(self, stro, g):
		fontFits=false
		maxFontSize = 14
		minFontSize = 6
		currentFont = Font("SansSerif", Font.PLAIN, maxFontSize)
		currentMetrics = g.getFontMetrics(currentFont)
		size = currentFont.getSize()
		name = currentFont.getName()
		style = currentFont.getStyle()
		cw = currentMetrics.stringWidth(stro)
		ch = currentMetrics.getHeight()
		ox = (self.w - cw) * 0.5
		oy = self.h * 0.5 + ch

		while not fontFits:
			if self.hexbottomhalfpoly.contains(ox, oy-ch, cw, ch):
				fontFits=true
			elif size <= minFontSize:
				fontFits=true
			else:
				currentFont = Font(name, style, size-1)
				currentMetrics = g.getFontMetrics(currentFont)
				size = currentFont.getSize()
				name = currentFont.getName()
				style = currentFont.getStyle()
				cw = currentMetrics.stringWidth(stro)
				ch = currentMetrics.getHeight()
				ox = (self.w - cw) * 0.5
				oy = self.h * 0.5 + ch
		return (currentFont, ox, oy,)

