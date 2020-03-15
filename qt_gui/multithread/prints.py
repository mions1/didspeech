import time, sys, os, speech_recognition as sr
from threading import Thread
from qt_gui.utils.misc import print_d
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from . import parsing

sys.path.append("../")
sys.path.append("../../")

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
		j = 0
		while self._parent.done < self._parent.chunks_num and not self.exiting:
			print_d("Sleep 8s...")
			time.sleep(8)
			print_d("Awake")
			i = j
			for t in parsing.Parsing.text[i:]:
				if t == False:
					print_d(str(i)+": not yet")
					break
				if i == 0:
					t = "---------- PARTIAL RESULT -----------\n"+t
				print_d(str(i+1)+": to print")
				self.print_partial.emit("\n"+t)	# refers to didispeech.start_parse
				#self._didspeech.tb_insert("\n"+t, False)
				i += 1
				j = i
		print_d("All done, die")

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
		percent = 0
		while not self.exiting and self._parent.done < self._parent.chunks_num:
			self.print_loading.emit(tb_text,True)
			time.sleep(0.8)
			print("DONE"+ str(self._parent.done))
			print(self._parent.chunks_num)
			if self._parent.chunks_num != 0:
				percent = round( (self._parent.done / self._parent.chunks_num)*100, 2)
			tb_text = self._parent.tb_get_text()
			new_print = str(percent)+"%\t" + self._fixed_text + str(self._changing_text[i])
			tb_text = tb_text.replace(self._last_printed, new_print)
			self._last_printed = new_print

			i = (i+1)%len(self._changing_text)