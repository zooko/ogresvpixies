import operator

from java.lang import *
from javax.swing import *

class TurnManager (Runnable):
	def __init__(self, creatures):
		self.creatures = creatures
		self.turnnumber = 0
		self.acts = []
		self.rbotevs = []
		self.reotevs = []
		pass

	def add_act(self, act, args=(), kwargs={}):
		#self.acts.append((act, args, kwargs,))
		apply(act, args, kwargs)

	def register_regular_bot_event(self, rbotev, args=(), kwargs={}, priority="whatever"):
		if priority == "first":
			self.rbotevs.insert(0, (rbotev, args, kwargs,))
		else:
			self.rbotevs.append((rbotev, args, kwargs,))

	def register_regular_eot_event(self, reotev, args=(), kwargs={}):
		self.reotevs.append((reotev, args, kwargs,))

	def resolve_turn(self):
		for (act, args, kwargs,) in self.acts:
			apply(act, args, kwargs)
		self.acts = []
		for (reotev, args, kwargs,) in self.reotevs:
			apply(reotev, args, kwargs)

	def begin_turn(self):
		self.turnnumber = self.turnnumber + 1
		print "and now for turn ", self.turnnumber
		for (rbotev, args, kwargs,) in self.rbotevs:
			apply(rbotev, args, kwargs)

	def go_if_ready(self):
		SwingUtilities.invokeLater(self)
		
	def _go_if_ready(self):
		"""
		If there are no more acts that need to be decided, then go ahead and resolve acts now.
		"""
		if reduce(operator.add, map(lambda c: c.actpleft, self.creatures), 0) <= 0:
			self.resolve_turn()
			self.begin_turn()

	# Runnable.run is our private _go_if_ready:
	run = _go_if_ready

