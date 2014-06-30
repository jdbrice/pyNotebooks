#!/usr/bin/env python 

import asyncore
import pyinotify
import os, string
from subprocess import call

wm = pyinotify.WatchManager()
mask = pyinotify.ALL_EVENTS

# the directory to watch for changes
watchDir = "/home/daniel/pyNotebooks/notebooks/";

# the directory to mirror with the html notebooks
hostDir = "/home/daniel/pyNotebooks/html/"


# Add any directories here that you want to excludde from the notebook hosting location
excludeList = [ '^' + watchDir + '.git', '^' + watchDir + 'private' ]
privateDirs =[]
for path in excludeList :
	parts = str.split( path, '/' )
	if  len( parts ) >= 1 :
		privateDirs.append( parts[-1] )

print "Private directories : ", privateDirs

exclude = pyinotify.ExcludeFilter(excludeList)


def convertNotebook( path ):
	#print "convertNotebook "

	rpath = path[ len(watchDir): ]
	parts = str.split( rpath, '/' )
	cDir = rpath[ :-len(parts[-1]) ]

	try:
		os.chdir( hostDir + cDir )

		call( ['ipython', 'nbconvert', path])

		os.chdir( hostDir )		
	except:
		print "could not convert notebook : ", path 

	print "-------------------------------------------------------------------"
	print " Created public version of : ", rpath
	print "-------------------------------------------------------------------"

	

def isNotebookFile( rpath ):
	#print "isNotebookFile "
	
	sfile = os.path.splitext( rpath )
	if  sfile[-1] == '.ipynb' and "Untitled" not in rpath:
		return True
	else :
		return False

def isHiddenFile( rpath ):
	#print "isHiddenFile "

	if '/' in rpath :
		
		parts = str.split( rpath, '/' )
		if parts[ -1 ][0] is '.' :
			return True
		else :
			return False
	else :
		
		if len( rpath ) >= 1 and rpath[0] is '.' :
			return True
		else :
			return False

def mirrorDir( rpath ):
	#print "mirrorDir "
	if os.path.exists( hostDir + rpath ) or rpath in privateDirs:
		return
	else :
		print ' Creating : ', rpath
		call( [ 'mkdir', rpath ] )

	for (dirpath, dirs, filenames) in os.walk( watchDir + rpath ):
		while len(dirs) > 0:  
			dirs.pop()
		for f in filenames :
			#print watchDir + rpath + "/" + f
			if isNotebookFile( rpath + "/" + f ) is True :
				convertNotebook( watchDir + rpath + "/" + f )

class EventHandler(pyinotify.ProcessEvent):
    def process_IN_CREATE(self, event):
        print "Creating:", event.pathname

    def process_IN_DELETE(self, event):
        print "Removing:", event.pathname
        
    
    def process_IN_CLOSE_WRITE( self, event ):
    	# get the substring after root watch dir
        rpath = event.pathname[ len(watchDir): ]
    	if not isHiddenFile( rpath ) and isNotebookFile(rpath) :
    		convertNotebook( event.pathname )
    		

    def process_default(self, event):
        # default if no function handler specified
        
        # get the substring after root watch dir
        rpath = event.pathname[ len(watchDir): ]
        
        #print 'default: ', event.maskname, ' path: ', rpath , ' mirror dir: ', (hostDir + rpath)
        
        if not isHiddenFile( rpath ) :
        	if event.dir :
        		mirrorDir( rpath )

notifier = pyinotify.AsyncNotifier(wm, EventHandler())
wdd = wm.add_watch(watchDir, mask, rec=True, exclude_filter=exclude, auto_add=True)

try :
	asyncore.loop()
except:
	print '\nExiting'