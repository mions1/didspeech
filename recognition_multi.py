import speech_recognition as sr
import sys, os, math, time
from tkinter import filedialog
from tkinter import *
from tkinter import scrolledtext, messagebox
from tkinter.ttk import *
from os import path
from pydub import AudioSegment
from threading import Thread

class Chunk():
	def __init__(self, chunk, filename, start="00:00:00", end="00:00:00"):
		self._chunk = chunk
		self._filename = filename
		self._start = start
		self._end = end

	def toString(self):
		print("File: "+str(self._filename)+" Start: "+str(self._start)+" End: "+str(self._end))

class Parsing(Thread):
	file = None

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
				self._text += self._r.recognize_google(listen, language="it-IT")
			except Exception as e:
				print(e)

		print_d("Thread #"+self._name+" finished")
		pass

	def toString(self):
		print("File: "+str(self._chunks))

TRACE = 1
THREADS = 4

def print_d(text, level=1):
	""" Enable trace to print tracing. Higher levels means more details
	"""
	if TRACE == level:
		print(str(text))

""" Allow user to select a directory

Parameters:
	label (StringVar): Label to set with folder path
"""
def browse(label):
	print_d("Selecting file...")
	filename = filedialog.askopenfilename()
	if filename == () or filename == '':
		filename = "No file selected..."
	#label.set(filename[filename.rfind("/")+1:])
	print_d("Selected file: "+str(filename))
	label.set(filename)

def tb_replace(tb, text, replace=True):
	""" Replace (or append) text in a textbox
	"""
	if replace:
		tb.delete("1.0", END)
	tb.insert(INSERT, text)
	tb.update()

def check_time_format(time):
    if len(time) != 8:
        return False
    h = time[0:2]
    m = time[3:5]
    s = time[6:]
    if h.isdigit() and m.isdigit and s.isdigit and time[2]==":" and time[5]==":":
        return True

def time_2_ms(start, end):
	""" It converts start and end from "hh:mm:ss" in ms
	"""
	if not check_time_format(start):
		start = "00:00:00"
		print_d("Start format wrong, repalce with "+start)
	if not check_time_format(end):
		end = "00:00:00"
		print_d("End format wrong, repalce with "+end)

	h_start = start[0:2]
	m_start = start[3:5]
	s_start = start[6:]

	h_end = end[0:2]
	m_end = end[3:5]
	s_end = end[6:]

	s = int(h_start)*(60*60*1000) + int(m_start)*(60*1000) + int(s_start)*(1000)
	e = int(h_end)*(60*60*1000) + int(m_end)*(60*1000) + int(s_end)*(1000)

	print_d("Start at: "+str(start)+" ("+str(s)+" ms)"+"\nEnd at: "+str(end)+" ("+str(e)+" ms)")

	return s, e


def start_parse(file, start, end, out=None, chunk_size=50000):  
	""" Main function, start parsing process
	"""
	
	start_time = time.time()
	global THREADS
	print_d("Starting parse...")
	
	if "..." in file[-4:]:
		print_d("no file selected, exit!")
		messagebox.showwarning("Warning", "Please, specified an audio file")   
		return
	
	if ".wav" not in file[-5:]:
		print_d("no wav, exit!")
		messagebox.showwarning("Warning", "Please, audio file must be in a .wav format")   
		return

	ms_start, ms_end = time_2_ms(start, end)
	print_d("Loading audio file...")
	audio = AudioSegment.from_wav(file)
	if ms_start == 0:
		start = "00:00:00"
	if ms_end == 0:
		end = "00:00:00"
		ms_end = len(audio)
	print_d("File: "+file+"\nStart: "+start+" ("+str(ms_start)+") \nEnd: "+end+" ("+str(ms_end)+" ms)")
	text = ""
	file_list = []
	chunks = []
	threads = []
	i = ms_start
	j = 1
	while i < ms_end:

		chunk = audio[ms_start:ms_start+chunk_size]
		chunk_file = file+"_chunk_"+str(j)+".wav"
		chunks.append(Chunk(chunk, chunk_file, ms_start, ms_start+chunk_size))
		file_list.append(chunk_file)

		ms_start += chunk_size
		i = ms_start
		j += 1

	if len(chunks) < THREADS:
		THREADS = 1
	s = math.floor(len(chunks)/THREADS)
	j = 0
	n_thread = 0
	for i in range(THREADS):
		threads.append(Parsing(chunks[j:j+s], n_thread))
		j = j+s
		n_thread += 1
	if s != math.ceil(len(chunks)/THREADS):
		for c in chunks[j:]:
			threads[-1]._chunks.append(c)
	


	print_d("Starting threads...")
	for t in threads:
		t.start()
	print_d("Waiting for finish...")

	for t in threads:
		t.join()

	text = ""
	for t in threads:
		text += t._text

	finish_parse(text, file_list, out)
	elapsed_time = time.time() - start_time
	print_d("Tempo esecuzione: "+str(elapsed_time))

def finish_parse(text, file_list, filename="save.txt", gui=True):
	print_d("Finish!")
	with open(filename, "w+") as f:
		print_d("Writing response on file "+filename+"...")
		f.write(text)
	
	for f in file_list:
		print_d("Deleting file "+str(f)+"...")
		os.remove(f)
	
	if gui:
		messagebox.showinfo("Info", "Finish. Result saved on "+filename)    
		

if "--nogui" in sys.argv:
	if "--debug" in sys.argv:
		file = "demo.wav"
		start = "00:00:00"
		end = "00:02:00"
	else:
		file = sys.argv[1]
		start = sys.argv[2] #00:00:00
		end = sys.argv[3]   #00:02:00
		
	start_parse(file, start, end)
	
	exit()    


#---------------- Create Windows ----------------------------------------------
window = Tk()
window.title("Didspeech - Transcribe")
window.geometry("700x400") # setting up window size
window.resizable(0, 0) # don't allow resizing in the x or y direction

#---------------- Button to choose file audio ---------------------------------
f_select_file = Frame(window)   # setting up frame in which put "select file" button
f_select_file.place(relx=0.5, rely=0.0, relheight=0.25, relwidth=0.50)
t_selected_file = StringVar(master=f_select_file, value="select file audio to parse...")
b_select_file = Button(f_select_file, textvariable=t_selected_file,
				command=lambda: [browse(t_selected_file)])
Label(f_select_file, text="Input audio file: ").pack()   
b_select_file.pack()

tb_out = scrolledtext.ScrolledText()

#---------------- Text input for "start" and "end" audio ----------------------
Label(window, 
	text="Start at (hh:mm:ss)").grid(row=0)
Label(window, 
		text="End at (hh:mm:ss)").grid(row=1)

e_start = Entry(window)
e_end = Entry(window)

e_start.grid(row=0, column=1)
e_end.grid(row=1, column=1)

#--------------- "start" and "quit" buttons -----------------------------------
b_start = Button(window, text='Start', command=lambda: Thread(target=start_parse, args=(t_selected_file.get(), e_start.get(), e_end.get(), tb_out)).start()).grid(row=3, column=0, sticky=W, pady=4)
b_quit = Button(window, text='Force quit', command=lambda: exit()).grid(row=3, column=1, sticky=W, pady=4)

#--------------- Textbox output -----------------------------------------------
f_out = Frame(window)
f_out.place(relx=0.0, rely=0.3)

tb_out = scrolledtext.ScrolledText(f_out, undo=True, height=15)
tb_out.pack(expand=True, fill='both')

tb_out.insert(INSERT, "1. Select an audio file\n2. Set range to parse (left blank if the whole file)\n3. Press Start button\nIn this box you will see log and result")

#--------------- Start --------------------------------------------------------
window.mainloop()