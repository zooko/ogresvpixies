#! /usr/bin/env jython
"""
ChatPanel provides a chat GUI for OvP.
"""

import java
from java.awt import *
from java.awt.event import *
from javax.swing import *
from javax.swing.text import *

# from Toolkit import *

class ChatPanel (JPanel, ActionListener):
	def __init__(self, columns=60, rows=10, author='NoName'):
		JPanel.__init__(self)
		self.author = author
		
		self.setLayout(BorderLayout())
		
		self._text = JTextArea(columns=columns, rows=rows)
		self._text.setEditable(0)
		self._text.setFocusable(0)
		self.add(self._text, BorderLayout.NORTH)

		self._input = JTextField(columns)
		self._input.addActionListener(self)
		self._input.requestFocusInWindow()
		self.add(self._input, BorderLayout.SOUTH)

	def appendMessage(self, text, author=None):
		if author:
			text = '%s: %s' % (author or 'anonymous', text)
		self._text.append(text + '\n')

	# Event handlers:
	def actionPerformed(self, e):
		s=e.getSource()
		if s is self._input:
			input = s.getText()
			s.setText('')
			self.appendMessage(text=input, author=self.author)
		else:
			raise Exception('Unknown action source: %s' % `s`)


if __name__ == '__main__':
	f=JFrame()
	f.getContentPane().add(ChatPanel())
	f.pack()
	f.setVisible(1)
	
