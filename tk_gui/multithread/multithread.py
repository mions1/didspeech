import time, sys, speech_recognition as sr
from threading import Thread
from tk_gui.utils.misc import print_d, tb_replace
sys.path.append("..")

class Chunk():
	def __init__(self, number, chunk, filename, start="00:00:00", end="00:00:00"):
		self._number = number
		self._chunk = chunk
		self._filename = filename
		self._start = start
		self._end = end
		self._done = False

	def __str__(self):
		return ("File: "+str(self._filename)+" Start: "+str(self._start)+" End: "+str(self._end))

class PrintPartial(Thread):

	def __init__(self, logger, chunks):
		Thread.__init__(self)
		self._logger = logger
		self._chunks = chunks

	def run(self):
		print_d("Starting print partial...")
		all_done = False
		j = 0
		while not all_done:
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
				tb_replace(self._logger, "\n"+t, False)
				i += 1
				j = i
		print_d("All done, die")

class Parsing(Thread):
	file = None
	text = []

	def __init__(self, chunks=[], name=""):
		Thread.__init__(self)
		self._r = sr.Recognizer()
		self._chunks = chunks
		self._text = ""
		self._name = str(name)
		pass

	def run(self):
		print_d("Thread #"+self._name+" starting...")
		for c in self._chunks:
			c._chunk.export(c._filename, format="wav")
			wav = sr.AudioFile(c._filename)

			with wav as source:
				self._r.pause_threshold = 3.0
				listen = self._r.listen(source)
			
			try:
				text_tmp = self._r.recognize_google(listen, language="it-IT")
				self._text += "\n"+text_tmp
				c._done = True
				Parsing.text[c._number] = text_tmp
			except Exception as e:
				print(e)

		print_d("Thread #"+self._name+" finished")
		pass

	def __str__(self):
		return("File: "+str(self._chunks))