#! /usr/bin/env jython
"""
Code for managing images.
"""

import path_fix # hack for nathan's box

import os
import sys

from java.awt import  *
from javax.swing import * # Just for main routine.


from util import AttributeMap

path = './images'

imageCache = None # The global reference.

def getImageCache():
	global imageCache

	if imageCache is not None:
		return imageCache

	#l = lambda message : log(message, name='ImageCache')
	l = lambda message : sys.stdout.write('ImageCache: %s\n' % message)

	l('Loading images from %r:' % path)

	imageCache = AttributeMap()
	for ipath in os.listdir(path):
		name, ext = os.path.splitext(ipath)
		if ext.lower() == '.jpeg':
			name = name.capitalize()
			fullpath = os.path.join(path, ipath)
			l('Loading %s from %r' % (name, ipath))
			img = Toolkit.getDefaultToolkit().getImage(fullpath)
			imageCache[name] = img
	return imageCache

def test_ImageCache(log):
	log('Starting test.')
	ic = getImageCache()
	log('Images: %s' % (', '.join(dir(ic))))
	ic2 = getImageCache()
	assert ic is ic2, "Duplicate image caches: %r vs %r" % (ic, ic2)
	log('Done testing.')

#testHook(globals())

if __name__ == '__main__':
	ic = getImageCache()
	class F (JFrame):
		def paint(self, g):
			dloc = self.getLocation()
			dsize = self.getSize()
			sw = ic.Ogre.getWidth(self)
			sh = ic.Ogre.getHeight(self)
			print "debug: destination rectangle:", dloc, dsize
			g.drawImage(ic.Ogre,
						dloc.x, dloc.y, dsize.width, dsize.height,
						0, 0, sw, sh,
						Color(0,0,0,0),
						self)
	f=F("Ogre Image")
	f.setSize(100, 100)
	f.setVisible(1)
	
