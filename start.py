#!/usr/bin/env jython

CVS_ID = '$Id: start.py,v 1.1 2002/01/25 16:36:01 zooko Exp $'

import sys
sys.path.append('.')
sys.path.append('') # not sure which of these two puts the cwd on the path...
import OvP
print OvP.version
o = OvP.OvP()





