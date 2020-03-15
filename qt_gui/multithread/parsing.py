import time, sys, os, speech_recognition as sr
from threading import Thread
from qt_gui.utils.misc import print_d
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *

sys.path.append("../../")

class Parsing(QThread):
	""" 
	"""

	file = None
	text = []

	def __init__(self, parent=None, chunks=[], name=""):
		QThread.__init__(self, parent)
		self._r = sr.Recognizer()
		self._parent = parent
		self._chunks = chunks
		self._done = 0
		self._text = ""
		self._name = str(name)
		self.exiting = False

	def __del__(self):
		print_d(str(self)+" __del__")
		self.exiting = True
		self.wait()

	def run(self):
		print_d("Thread #"+self._name+" starting...")
		for c in self._chunks:
			if self.exiting:
				return
			print_d("Thread #"+self._name+" start "+str(c))
			c._chunk.export(c._filename, format="wav")
			wav = sr.AudioFile(c._filename)

			with wav as source:
				self._r.pause_threshold = 3.0
				listen = self._r.listen(source)
			
			try:
				print_d("Thread #"+self._name+" recongizing...")
				text_tmp = self._r.recognize_google(listen, language="it-IT")
				print_d("Thread #"+self._name+" recongized!")
				self._text += "\n"+text_tmp
				c._done = True
				Parsing.text[c._number] = text_tmp
				c._text = text_tmp
				self._done += 1
				self._parent.done += 1
				print_d("Thread #"+self._name+" finishes a chunk")
			except Exception as e:
				print(e)

		print_d("Thread #"+self._name+" finished")
		pass

	def __str__(self):
		return("File: "+str(self._chunks))