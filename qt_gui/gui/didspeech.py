import speech_recognition as sr
import sys, os, math, time, argparse
import PyQt5.QtWidgets as qt
import PyQt5.QtCore as qtc
import PyQt5.QtGui as qtg

from os import path
from pydub import AudioSegment
from threading import Thread
from qt_gui.utils import misc
from qt_gui.utils.misc import print_d, time_2_ms, ms_2_time, is_video
from qt_gui.multithread.chunk import Chunk
from qt_gui.multithread.parsing import Parsing
from qt_gui.multithread.prints import PrintPartial, PrintLoading
from qt_gui.multithread.multithread import SystemJob, ShowDialog

import moviepy.editor

sys.path.append("..")
sys.path.append(".")

THREADS = 4

class Start(qtc.QThread):
	""" Handle threads which execute parsing in order to let app reactive.
		The main job is to start threads in order to
		begin parsing and wait for the finish.
		In the end, emit a singal and send the output, 
		so the extracted text
	"""
	is_finish = qtc.pyqtSignal(str)	# signal to notify end of jobs

	def __init__(self, didspeech, threads, loading_thread=None):
		""" Init

		Parameters:
			didspeech (Didspeech): the app, used for __init__ of QThread
			threads (list): list of Threads from multithread.Parsing
			loading_thread (QThread): Thread that print a loading string while computing 
		"""
		qtc.QThread.__init__(self, didspeech)
		self._didspeech = didspeech
		self._threads = threads
		self._loading_thread = loading_thread
		self.exiting = False
		self._text = ""
	
	def __del__(self):
		self.exiting = True
		self.wait()
	
	def run(self):
		""" Start threads and wait for them.
			When they finished, emit a signal with the output text.
		"""
		start_time = time.time()
		
		# print a blinking "loading..." string in text box
		if self._loading_thread:
			print_d("Starting loading thread...")
			self._loading_thread.start()
		# start parsing thread
		print_d("Starting threads...")
		for t in self._threads:
			t.start()
		print_d("Waiting for finish...")

		finish = False
		"""		
		while not finish:
		print("Wait...")
		finish = True
		"""
		for t in self._threads:
			t.wait()

		# at the end, save the result in text
		text = Parsing.text
		for t in text:
			if t:
				self._text += t+"\n"
		Parsing.text = []

		# stop loading thread
		if self._loading_thread:
			self._loading_thread.exit()
		# stop parsing thread
		self.is_finish.emit(self._text)
		Didspeech.elapsed_time = time.time() - start_time
		print_d("Run time: "+str(Didspeech.elapsed_time))
		pass

class Didspeech(qt.QApplication):
	""" Handle application.
		Create layouts and widgets, connect buttons and
		handle their functions.
	"""

	SUPPORTED_FILE = ["wav",
					"ogg",
					"flv",
					"wma",
					"aac",
					"mp3",

					"mp4",
					"avi",
					]

	elapsed_time = 0
	done = 0
	chunks_num = 0

	def __init__(self, file="Select file...", chunk_size=50000, output_file="save.txt", options=[]):
		""" Main class, application

		Parameters:
			chunk_size (int): length of every chunk (so, a piece of audio)
		"""
		super().__init__(options)
		self._file = file
		self._start = ""
		self._end = ""
		self._chunk_size = chunk_size
		self._output_file = output_file

	def init(self):
		self.load_resources()
		#-------------- Frame select file -----------------------------------------
		self._f_select_file = qt.QGridLayout()

		self._l_select_file = qt.QLabel("Input file:")
		self.set_style(self._l_select_file, "labels", "all_input")
		self._b_select_file = qt.QPushButton(self._file)
		self.set_style(self._b_select_file, "buttons", "b_select_file")

		self._l_select_output_file = qt.QLabel("Output file: ")
		self.set_style(self._l_select_output_file, "labels", "all_input")
		self._b_select_output_file = qt.QPushButton(self._output_file)
		self.set_style(self._b_select_file, "buttons", "b_select_file")

		self._f_select_file.addWidget(self._l_select_file, 0,0)
		self._f_select_file.addWidget(self._b_select_file, 1,0)

		self._f_select_file.addWidget(self._l_select_output_file, 0,1)
		self._f_select_file.addWidget(self._b_select_output_file, 1,1)

		l_title = qt.QLabel()
		pixmap = qtg.QPixmap(path.join("resources","images","title.png"))
		l_title.setPixmap(pixmap)
		self.set_style(l_title, "labels", "title")
		self._f_select_file.addWidget(l_title, 2,0,2,2)
		self._f_select_file.addWidget(self.get_QHline(), 3,0,3,2)

		#f_select_file.setLayout(f_select_file)
		self._b_select_file.clicked.connect(lambda a: self.set_file())	
		self._b_select_output_file.clicked.connect(lambda a: self.set_output_file())
		self.set_style(self._b_select_output_file, "buttons", "b_select_output_file")		

		#-------------- Frame options ---------------------------------------------
		self._f_options = qt.QGridLayout()

		self._l_start = qt.QLabel("Start (hh:mm:ss)")
		self.set_style(self._l_start, "labels", "l_start")
		self._e_start = qt.QLineEdit()
		self._e_start.setMaxLength(8)
		self._e_start.setInputMask("99:99:99")
		self._e_start.setText("00:00:00")

		self._l_end = qt.QLabel("End (hh:mm:ss)")
		self.set_style(self._l_end, "labels", "l_end")
		self._e_end = qt.QLineEdit()
		self._e_end.setMaxLength(8)
		self._e_end.setInputMask("99:99:99")
		self._e_end.setText("00:00:00")

		self._b_start = qt.QPushButton("Start", enabled=False, default=True)
		self._b_quit = qt.QPushButton("Force quit")
		self.set_style(self._b_start, "buttons", "b_start")
		self.set_style(self._b_quit, "buttons", "b_end")

		self._b_start.clicked.connect(self.start_parse)
		self._b_quit.clicked.connect(self.exit)

		self._b_other_settings = qt.QPushButton("Other settings")
		self.set_style(self._b_other_settings, "buttons", "b_other_settings")

		self._f_options.addWidget(self._l_start, 0,0)
		self._f_options.addWidget(self._e_start, 0,1)
		self._f_options.addWidget(self._l_end, 1,0)
		self._f_options.addWidget(self._e_end, 1,1)

		self._f_options.addWidget(self._b_start, 2,0)
		self._f_options.addWidget(self._b_quit, 2,1)
		# FIXME make other settings
		#self._f_options.addWidget(self._b_other_settings, 3,0,3,3)

		#---------- Frame Output ----------------------------------------------
		self._f_output = qt.QVBoxLayout()

		self._tb_out = qt.QTextEdit()
		self._tb_out.setReadOnly(True)
		tmp_str = "1. Select an audio file\n"
		tmp_str += "2. Set range to parse (left blank if the whole file)\n"
		tmp_str += "3. Press Start button\n"
		tmp_str += "In this box you will see log and result. Result will be saved on output file too"
		self.tb_insert(tmp_str)
		self.set_style(self._tb_out, "textbox", "tb_out")

		self._f_output.addWidget(self._tb_out)

		#---------- <ADD HERE OTHER FRAMES AND WIDGETS TO CREATE> -------------
		
	def check_file(self, selected):

		# if no file selected, return
		if "Select file..." == selected:
			if "--debug" in sys.argv:
				self._file = "demo.wav"
			else:
				print_d("no file selected, exit!")
				self.message_dialog("Error", "Please, select a file first", icon=qt.QMessageBox.Critical)
				return False
		
		# if audio file is no a .wav FIXME: It must support more audio type
		if selected != "":
			ext = selected[selected.rfind(".")+1:]
			if ext not in Didspeech.SUPPORTED_FILE:
				print_d("file not supported yet, exit!")
				self.message_dialog("Error", "Please, audio file must be in a supported type"+str(Didspeech.SUPPORTED_FILE), icon=qt.QMessageBox.Critical)
				return False
		
		return ext

	def set_file(self):
		""" Browse into filesystem to choose an audio file

		Parameters:
			file_types (list): list of accepted exenstions
		"""

		all_supported = "All supported format ("
		file_types = []
		for file_type in Didspeech.SUPPORTED_FILE:
			file_types.append(str(file_type) + " files " + "(*." + str(file_type) + ")")
			all_supported += ("*." + file_type + " ")
		all_supported += ")"
		file_types.insert(0, all_supported)

		file_types_str = ""
		for file_type in file_types:
			file_types_str += file_type+(";;")
		dialog = qt.QWidget()
		dialog.setWindowTitle("Choose audio file")
		options = qt.QFileDialog.Options()
		options |= qt.QFileDialog.DontUseNativeDialog
		choose = qt.QFileDialog.getOpenFileName(dialog, "QFileDialog.getOpenFileName()", "", file_types_str, options=options)
		selected = choose[0]
		
		file_type = self.check_file(selected)
		if file_type:
			self._b_select_file.setText(choose[0][choose[0].rindex("/")+1:])
			self._file = choose[0]
			if is_video(self._file):
				print_d("Converting video...")
				video = moviepy.editor.VideoFileClip(self._file)
				audio = video.audio
				file_type = "wav"
				self._file = path.join("resources","output",path.basename(self._file)[:self._file.rfind(".")]+"."+file_type)
				audio.write_audiofile(self._file)
				print_d("Finish convertion!")
				self.tb_insert("Done!", False)
			
			self._audio = AudioSegment.from_file(self._file, file_type)
			print(ms_2_time(len(self._audio)))
			self._e_end.setText(ms_2_time(len(self._audio)))
			self._b_start.setEnabled(True)
			return choose[0]
	
	def set_output_file(self):
		""" Browse into filesystem

		Parameters:
			file_types (list): list of accepted exenstions
		"""
		file_types=["All files (*)"]

		file_types_str = ""
		for file_type in file_types:
			file_types_str += file_type+(";;")
		dialog = qt.QWidget()
		dialog.setWindowTitle("Save file on...")
		options = qt.QFileDialog.Options()
		options |= qt.QFileDialog.DontUseNativeDialog
		choose = qt.QFileDialog.getOpenFileName(dialog, "QFileDialog.getSaveFileName()", "", file_types_str, options=options)
		self._b_select_output_file.setText(choose[0][choose[0].rindex("/")+1:])
		self._output_file = choose[0]
		return choose[0]

	def message_dialog(self, title="Info", message="Info", more_text="", icon=qt.QMessageBox.NoIcon):
		msg = qt.QMessageBox()
		msg.setIcon(icon)
		msg.setText(message)
		msg.setInformativeText(more_text)
		msg.setWindowTitle(title)
		msg.exec_()

	def load_resources(self):
		print_d("Loading resources...")
		res = dict()
		for file in os.listdir(os.path.join("resources","style")):
			with open(os.path.join("resources","style",file), "r") as f:
				for line in f:
					if file not in res:
						res[file] = dict()
					element_name = line[:line.find(" ")]
					css = line[line.find("{")+1:]
					res[file][element_name] = css
		self._resources = res
		print_d(self._resources, 2)
		print_d("Finish loading resources!")

	def set_style(self, object, category, name=""):
		if not self._resources:
			self.load_resources()
		if category not in self._resources:
			return
		style = ""
		if "all" in self._resources[category]:
			style += str(self._resources[category]["all"])
		if name in self._resources[category]:
			style += str(self._resources[category][name])
		object.setStyleSheet(style)
		print_d(str(object)+" "+str(category)+" "+str(name)+" "+style)
		pass

	def get_audio(self):
		audio_type = self._file[self._file.rindex(".")+1:]
		return AudioSegment.from_file(self._file, audio_type)

	def start_parse(self):  
		""" Main function, start parsing process
		"""
		global THREADS

		print_d("Starting parse...")

		#---------- Now, if a file is select ---------------------------------------
		# get start and end point
		self._start = self._e_start.text()
		self._end = self._e_end.text()

		# convert start and end point from hh:mm:ss to ms
		ms_start, ms_end = time_2_ms(self._start, self._end)
		print_d("Loading audio file...")

		audio = self.get_audio()
		# if ms_start == 0 maybe self._start is unset, so adjust it
		if ms_start == 0:
			self._start = "00:00:00"
		# same for ms_end. Further, if ms_end == 0, set ms_end to audio length
		if ms_end == 0:
			self._end = "00:00:00"
			ms_end = len(audio)

		#---------- Setting up threads ----------------------------------------
		print_d("File: "+self._file+"\nStart: "+self._start+" ("+str(ms_start)+") \nEnd: "+self._end+" ("+str(ms_end)+" ms)")
		self.file_list = []	# in it, store list of chunk file saved
		chunks = []		# in it, store all chunks (see class Chunk)
		threads = []	# in it, store threads which execute chunk (see class Parsing)

		# split audio file in chunks according to chunk_size, from ms_start to ms_end
		i = ms_start
		j = 1
		print_d("Creating chunks...")
		while i < ms_end:
			print_d("Chunk #"+str(j), 2)
			# split audio
			if ms_start+self._chunk_size > ms_end:
				chunk = audio[ms_start:ms_end-1]
			else:
				chunk = audio[ms_start:ms_start+self._chunk_size]
			# create associated file (named like: filename_chunk_1.wav) and add it into a list (this files will be delete in the end)
			chunk_file = self._file+"_chunk_"+str(j)+".wav"
			self.file_list.append(chunk_file)
			# create Chunk istance and add it to a list
			chunks.append(Chunk(j-1, chunk, chunk_file, ms_start, ms_start+self._chunk_size))

			# update var for while loop
			ms_start += self._chunk_size
			i = ms_start
			j += 1

		time.sleep(8)
		chunks_num = len(chunks)	# number of chunks created
		Didspeech.chunks_num = chunks_num
		Parsing.text = [False]*(chunks_num)	# used to print partial result in log text box
		print_d("#Chunks: "+str(chunks_num))

		# if there are more chunks than threads, set threads number to chunks number
		if chunks_num < THREADS:
			THREADS = chunks_num

		# split in equal part chunks to threads. If odd, the last thread will have more chunks
		i = 0
		split_chunks = [ [] for i in range(THREADS) ]
		for c in chunks:
			split_chunks[i%THREADS].append(c)
			i += 1
		i = 0
		n_thread = 0
		for chunk in split_chunks:
			threads.append(Parsing(self, chunk, n_thread))
			n_thread += 1
		
		# start parsing
		# loading_thread is for print loading string
		loading_thread = PrintLoading(self, "Loading", [".","..","..."])
		started = Start(self, threads, loading_thread=loading_thread)
		started.start()
		started.is_finish[str].connect(self.finish_parse)
		loading_thread.print_loading[str,bool].connect(self.tb_insert)

		# disable button to avoid problems
		self._b_start.setEnabled(False)
		# start thread that print partial result in order. See class PrintPartial for more information
		if True:
			print_partial = PrintPartial(self, chunks)
			print_partial.start()
			print_partial.print_partial[str].connect(self.tb_insert)

	def finish_parse(self, text):
		""" Invoke at the end of parsing. It save the result on file and show it
			on log text box. Furthermore, delete created chunks file and show a pop up
			that inform for the finish.

		Parameters:
			text (str): result
			file_list (list): list of file to be delete (chunks)
			filename (str): file to save result
			gui (ScrolledText): text box to show result
		"""
		# re-enable button
		self._b_start.setEnabled(True)
		print_d("Finish!")

		# save result on file
		with open(self._output_file, "w+") as f:
			print_d("Writing response on file "+self._output_file+"...")
			text = text[0].upper() + text[1:].lower()
			print_d(text)
			f.write(text)

		# delete files
		for f in self.file_list:
			print_d("Deleting file "+str(f)+"...")
			os.remove(f)
		
		# show result in text box and show pop up
		self.tb_insert("------------ RESULT -----\n"+text, replace=True)
		self.message_dialog("Finish", "Parsing finished in "+str(  round(Didspeech.elapsed_time, 2) ), "Result saved on "+self._output_file, qt.QMessageBox.Information)

		(SystemJob(self, 'vlc "'+self._file+'"')).start()

	def tb_insert(self, text, replace=False):
		if replace:
			self._tb_out.setText(text)
		else:
			self._tb_out.append(text)

	def tb_get_text(self):
		return self._tb_out.toPlainText()

	def get_QHline(self):
		qhline = qt.QFrame()
		qhline.setFrameShape(qt.QFrame.HLine)
		qhline.setFrameShadow(qt.QFrame.Plain)
		return qhline

if __name__=='__main__':
	didspeech = Didspeech()
	didspeech.init()
	#didspeech.setStyle('Fusion')
	#palette = qt.QPalette()
	#palette.setColor(qt.QPalette.ButtonText, Qt.red)
	#didspeech.setPalette(palette)
	#didspeech.setStyleSheet("QPushButton { margin: 10ex; }") # like css
	window = qt.QMainWindow()
	main_frame = qt.QGridLayout()

	#-------------- Add all ---------------------------------------------------
	main_frame.addLayout(didspeech._f_select_file, 0,0,0,2)
	main_frame.addLayout(didspeech._f_options, 2,0,2,2)
	main_frame.addLayout(didspeech._f_output, 2,0,2,2)
	window.setLayout(main_frame)
	
	window.resize(700,1800)
	window.show()

	didspeech.exec_()
