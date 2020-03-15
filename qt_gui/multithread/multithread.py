import time, sys, os, speech_recognition as sr
from threading import Thread
from qt_gui.utils.misc import print_d
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *

sys.path.append("../../")

class SystemJob(QThread):
	
	def __init__(self, parent, command="exit"):
		QThread.__init__(self, parent)
		self._parent = parent
		self._command = command
		self.exiting = False
	
	def __del__(self):
		self.exiting = True
		self.wait()

	def run(self):
		print_d("Starting command: "+self._command)
		os.system(self._command)

class ShowDialog(QThread):

	def __init__(self, parent, title="Title", message="Message", more_text="More", icon=QMessageBox.NoIcon):
		QThread.__init__(self, parent)
		self._parent = parent
		self._title = title
		self._message = message
		self._more_text = more_text
		self._icon = icon
		self.exiting = False
	
	def __del__(self):
		self.exiting = True
		self.wait()

	def run(self):
		msg = QMessageBox()
		msg.setIcon(self._icon)
		msg.setText(self._message)
		msg.setInformativeText(self._more_text)
		msg.setWindowTitle(self._title)
		msg.exec_()