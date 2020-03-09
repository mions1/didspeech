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

class PrintLoading(QThread):
	print_loading = pyqtSignal(str,bool)

	def __init__(self, parent, fixed_text="Loading", changing_text=[".","..","..."]):
		QThread.__init__(self, parent)
		self._parent = parent
		self._fixed_text = fixed_text
		self._changing_text = changing_text
		self._last_printed = fixed_text
		self.exiting = False

	def __del__(self):
		self.exiting = True
		self.wait()

	def run(self):
		i = 0
		tb_text = self._fixed_text
		while not self.exiting:
			self.print_loading.emit(tb_text,True)
			time.sleep(0.8)	 
			tb_text = self._parent.tb_get_text()
			new_print = str(self._fixed_text)+str(self._changing_text[i])
			tb_text = tb_text.replace(self._last_printed, new_print)
			self._last_printed = new_print

			i = (i+1)%len(self._changing_text)

class Chunk():
	def __init__(self, number, chunk, filename, start="00:00:00", end="00:00:00"):
		self._number = number
		self._chunk = chunk
		self._filename = filename
		self._start = start
		self._end = end
		self._done = False
		self._text = ""

	def __str__(self):
		return ("File: "+str(self._filename)+" Start: "+str(self._start)+" End: "+str(self._end))

class PrintPartial(QThread):
	print_partial = pyqtSignal(str)

	def __init__(self, parent, chunks):
		QThread.__init__(self, parent)
		self._parent = parent	# parent is a Didspeech instance
		self._chunks = chunks
		self.exiting = False

	def __del__(self):
		self.exiting = True
		self.wait()

	def run(self):
		print_d("Starting print partial...")
		all_done = False
		j = 0
		while not all_done and not self.exiting:
			print_d("Sleep 8s...")
			time.sleep(8)
			print_d("Awake")
			i = j
			all_done = True
			for t in Parsing.text[i:]:
				all_done = False
				if t == False:
					print_d(str(i)+": not yet")
					break
				if i == 0:
					t = "---------- PARTIAL RESULT -----------\n"+t
				print_d(str(i+1)+": to print")
				self.print_partial.emit("\n"+t)
				#self._didspeech.tb_insert("\n"+t, False)
				i += 1
				j = i
		print_d("All done, die")

class Parsing(QThread):
	""" 
	"""

	file = None
	text = []

	def __init__(self, parent=None, chunks=[], name=""):
		QThread.__init__(self, parent)
		self._r = sr.Recognizer()
		self._chunks = chunks
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
			print(c)
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
				print_d("Thread #"+self._name+" finish a chunk")
			except Exception as e:
				print(e)

		print_d("Thread #"+self._name+" finished")
		pass

	def __str__(self):
		return("File: "+str(self._chunks))