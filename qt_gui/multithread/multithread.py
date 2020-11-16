import time, sys, os, speech_recognition as sr
from threading import Thread

from pyparsing import Optional

from qt_gui.utils.misc import print_d, get_audio
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *

class GetAudio(QThread):

	audio_loaded_signal = pyqtSignal()
	audio_loaded_return_signal = pyqtSignal(object)

	def __init__(self, context, file):
		QThread.__init__(self, context)
		self._context = context
		self._file = file

	def run(self):
		self._audio = get_audio(self._file)
		self.audio_loaded_signal.emit()
		self.audio_loaded_return_signal.emit(self._audio)



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