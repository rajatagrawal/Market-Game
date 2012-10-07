#!/usr/bin/env python

# Copyright (c) 2007 Carnegie Mellon University.
#
# You may modify and redistribute this file under the same terms as
# the CMU Sphinx system.  See
# http://cmusphinx.sourceforge.net/html/LICENSE for more information.
#
# Briefly, don't remove the copyright.  Otherwise, do what you like.

__author__ = "David Huggins-Daines <dhuggins@cs.cmu.edu>"

# System imports
import sys
import os
from socket import *      #import the socket library

# GTK+ and GStreamer
import pygtk
pygtk.require('2.0')
import gtk
try:
    import hildon
    wtype = hildon
    using_hildon = True
except:
    wtype = gtk
    using_hildon = False
import gobject
import pango
import pygst
pygst.require('0.10')
gobject.threads_init()
import gst

# Local imports
import sphinxbase
import pocketsphinx
#import latticeui

class LiveDemo(object):
    def __init__(self,
                 hmm=None,
                 lm='model/mobile.lm.DMP',
                 dict='model/mobile.dic',
                 latdir='lattice'):
        # Create toplevel window
        self.window = wtype.Window()
        #self.window.connect("delete-event", gtk.main_quit)
        # Handle full-screen key events
        if using_hildon:
            #self.window.connect('key-press-event', self.on_key_press)
            #self.window.connect('window-state-event', self.on_window_state_change)
            #self.window.fullscreen()
            #self.in_fullscreen = True
            audiosrc = 'dsppcmsrc'
        else:
            audiosrc = 'gconfaudiosrc'

        # Create ASR pipeline
        self.pipeline = gst.parse_launch(audiosrc + ' ! audioconvert ! audioresample '
                                         + '! vader name=vad dump-dir=audio '
                                         + '! queue name=queue '
                                         + '! pocketsphinx name=asr ! fakesink')
        asr = self.pipeline.get_by_name('asr')
        if hmm != None:
            asr.set_property('hmm', hmm)
        asr.set_property('lm', lm)
        asr.set_property('dict', dict)
        asr.set_property('latdir', latdir)
        asr.set_property('fwdflat', False)
        asr.set_property('bestpath', False)
        asr.set_property('configured', True)

        # Retrieve some internal objects
        self.ps = pocketsphinx.Decoder(boxed=asr.get_property('decoder'))
        self.lm = self.ps.get_lmset()

        # Connect some signal handlers to ASR signals (will use the bus to forward them)
        asr.connect('partial_result', self.asr_partial_result)
        asr.connect('result', self.asr_result)

        # Connect to the queue's flow control signals
        queue = self.pipeline.get_by_name('queue')
        queue.connect('overrun', self.queue_overrun)

        # Connect VADER signals
        vader = self.pipeline.get_by_name('vad');
        vader.set_property('auto_threshold', True)
        vader.connect('vader_start', self.vader_start)
        vader.connect('vader_stop', self.vader_stop)

        # Bus signals etc
        bus = self.pipeline.get_bus()
        bus.add_signal_watch()
    #    bus.connect('message::application', self.application_message)

        self.pipeline.set_state(gst.STATE_PLAYING)

        # Vbox to hold stuff
        #vbox = gtk.VBox()

        # A menu for loading lattices
        #if using_hildon:
        #    main_menu = gtk.Menu()
        #    self.window.set_menu(main_menu)
        #else:
        #    main_menu = gtk.MenuBar()
        #    vbox.pack_start(main_menu)

        # Current folder for word lattices
        #try:
        #    os.stat('test/lattice')
        #    self.lat_folder = 'test/lattice'
        #except:
        #    self.lat_folder = '.'

        #file_item = gtk.MenuItem("File")
        #file_menu = gtk.Menu()
        #file_item.set_submenu(file_menu)
        #open_item = gtk.MenuItem("Open Lattice...")
        #open_item.connect("activate", self.file_open_lattice)
        #file_menu.append(open_item)
        #file_menu.append(gtk.MenuItem())
        #quit_item = gtk.MenuItem("Quit")
        #quit_item.connect("activate", gtk.main_quit)
        #file_menu.append(quit_item)
        #main_menu.append(file_item)
        
        # Create an (empty) lattice model and view
        #self.model = latticeui.LatticeModel(lm=self.lm)
        #self.result = latticeui.LatticeView(self.model, probscale=0.75)
        #scroll = latticeui.KineticDragPort()
        #w, h = self.result.get_size_request()
        #scroll.set_size_request(600, h)
        #scroll.add(self.result)

        # And a push to talk button
        #vbox.pack_start(scroll)
        #self.button = gtk.ToggleButton("speak")
        #self.button.connect('clicked', self.button_clicked)
        #vbox.pack_start(self.button)
        #self.window.add(vbox)
        #self.window.show_all()

        # If we were passed a lattice on the command line, set it
        #if len(sys.argv) > 1:
        #   self.open_lattice(sys.argv[1])



	#Establish Socket Connection 
	HOST = ''    #we are the host
	PORT = 5000    #arbitrary port not currently in use
	ADDR = (HOST,PORT)    #we need a tuple for the address
	BUFSIZE = 4096    #reasonably sized buffer for data
 
	## now we create a new socket object (serv)
	## see the python docs for more information on the socket types/flags
	serv = socket(AF_INET,SOCK_STREAM)
 
	##bind our socket to the address
	serv.bind((ADDR))    #the double parens are to create a tuple with one element
	serv.listen(5)    #5 is the maximum number of queued connections we'll allow
	print 'listening...'
 
	self.conn,addr = serv.accept() #accept the connection
	print '...connected!'
	#keep looping, start the recognizer loop when you receive "start", pause when you receive "pause" and close connection if you receive "stop"
	while(1):
		self.data=self.conn.recv(BUFSIZE)
		if self.data.find('echo')!=-1:
			os.system(self.data)
	#	if self.data == "stop":
   	#		print  "Done!"
	#		self.conn.close()
	
    def open_lattice(self, latfile):
        self.lat_folder = os.path.dirname(latfile)
        self.dag = pocketsphinx.Lattice(self.ps, latfile)
        self.model.set_dag(self.dag)
        self.result.update_model()
        self.window.set_title(os.path.basename(latfile))

    def file_open_lattice(self, item):
        chooser = gtk.FileChooserDialog("Open Lattice...", None,
                                        gtk.FILE_CHOOSER_ACTION_OPEN,
                                        buttons=(gtk.STOCK_CANCEL,gtk.RESPONSE_CANCEL,
                                                 gtk.STOCK_OPEN,gtk.RESPONSE_OK))
        chooser.set_default_response(gtk.RESPONSE_OK)
        filt = gtk.FileFilter()
        filt.set_name("All files")
        filt.add_pattern("*")
        chooser.add_filter(filt)
        filt = gtk.FileFilter()
        filt.set_name("Word Lattices")
        filt.add_pattern("*.lat")
        filt.add_pattern("*.lat.gz")
        chooser.add_filter(filt)
        chooser.set_current_folder(self.lat_folder)
        
        response = chooser.run()
        if response == gtk.RESPONSE_OK:
            latfile = chooser.get_filename()
            chooser.destroy()
            self.open_lattice(latfile)
        else:
            chooser.destroy()

    def on_key_press(self, window, event):
        if event.keyval == gtk.keysyms.F6:
            if self.in_fullscreen:
                window.unfullscreen()
            else:
                window.fullscreen()

    #def on_window_state_change(self, window, event):
    #    if event.new_window_state & gtk.gdk.WINDOW_STATE_FULLSCREEN:
    #        self.in_fullscreen = True
    #    else:
    #        self.in_fullscreen = False

#    def button_clicked(self, button):
#        if button.get_active():
#            button.set_label("Pause")
#            self.pipeline.set_state(gst.STATE_PLAYING)
#        else:
            # FIXME: Signal an end of utterance somehow
#            self.pipeline.set_state(gst.STATE_PAUSED)

    def application_message(self, bus, msg):
	print 'application message ....'
        msgtype = msg.structure.get_name()
        if msgtype == 'partial_result':
            self.model.set_hyp([latticeui.LatticeWord(w, 0.0, 0.0)
                                for w in msg.structure['hyp'].split()])
            self.result.update_model()
        elif msgtype == 'result':
            # Get the lattice
            self.model.set_dag(self.dag)
            self.result.update_model()
            self.window.set_title(msg.structure['uttid'])
        elif msgtype == 'vader_stop':
            self.pipeline.set_state(gst.STATE_PAUSED)
            self.button.set_label("Speak")
            self.button.set_active(False)

    def queue_overrun(self, queue):
        """
        Handle queue overruns.
        """
        # We should tell pocketsphinx to stop searching, but for now
        # we'll just expand the queue.
        nbuf = queue.get_property('current-level-buffers')
        nbytes = queue.get_property('current-level-bytes')
        nnsec = queue.get_property('current-level-time')
        maxbuf = queue.get_property('max-size-buffers')
        maxbytes = queue.get_property('max-size-bytes')
        maxnsec = queue.get_property('max-size-time')
	print "queue overrun max (%d,%d,%d) cur (%d,%d,%d)" \
		% (maxbuf,maxbytes,maxnsec,nbuf,nbytes,nnsec)
        if nbuf >= maxbuf:
            queue.set_property('max-size-buffers', maxbuf * 2)
        if nbytes >= maxbytes:
            queue.set_property('max-size-bytes', maxbytes * 2)
	# In practice, this is the only one that will happen
        if nnsec >= maxnsec:
            queue.set_property('max-size-time', maxnsec * 2)

    def vader_start(self, vader, ts):
        """
        Forward VADER start signals on the bus to the main thread.
        """
        struct = gst.Structure('vader_start')
        # Ignore the timestamp for now because gst-python is buggy
        vader.post_message(gst.message_new_application(vader, struct))

    def vader_stop(self, vader, ts):
        """
        Forward VADER stop signals on the bus to the main thread.
        """
        struct = gst.Structure('vader_stop')
        # Ignore the timestamp for now because gst-python is buggy
        vader.post_message(gst.message_new_application(vader, struct))

    def asr_partial_result(self, asr, text, uttid):
        """
        Forward partial result signals on the bus to the main thread.
        """
	#print text
	#send the hypothesis on the socket connection
	#self.conn.send(text)
        struct = gst.Structure('partial_result')
        struct.set_value('hyp', text)
        struct.set_value('uttid', uttid)
        asr.post_message(gst.message_new_application(asr, struct))

    def asr_result(self, asr, text, uttid):
        """
        Forward result signals on the bus to the main thread.
        """
	print text
	#send the hypothesis on the socket connection
	self.conn.send(text)
        struct = gst.Structure('result')
        struct.set_value('hyp', text)
        struct.set_value('uttid', uttid)
        #self.dag = pocketsphinx.Lattice(boxed=asr.get_property('lattice'))
        asr.post_message(gst.message_new_application(asr, struct))

d = LiveDemo()
gtk.main()