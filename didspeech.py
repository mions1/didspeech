import speech_recognition as sr
import sys, os, math, time, argparse
import tkinter as tk
from tkinter import scrolledtext, messagebox, filedialog
from tkinter.ttk import *
from os import path
from pydub import AudioSegment
from threading import Thread
from gui.mainwindow import MainWindow
from gui.frame import SelectFileFrame, OptionsFrame, OutputFrame
from utils import misc
from utils.misc import print_d, tb_replace, browse, time_2_ms, check_time_format
from multithread.multithread import *

# Global var
THREADS = 4	# threads number

def start_parse(file, start, end, out=None, chunk_size=50000):  
	""" Main function, start parsing process

	Parameters:
		file (str): audio file to parse
		start (str): starting point in format 'hh:mm:ss'
		end (str): ending point in format 'hh:mm:ss'
		out (ScrolledText): text box to showing log and result
		chunk_size (int): audio lenght of chunk, in ms
	"""
	global THREADS

	# if debug is on, set default values FIXME: It must be set in main
	if "--debug" in sys.argv:
		file = "demo.wav"
		start = "00:00:00"
		end = "00:06:00"

	start_time = time.time()
	print_d("Starting parse...")
	
	# if no file selected, return
	if "..." in file[-4:]:
		print_d("no file selected, exit!")
		messagebox.showwarning("Warning", "Please, specified an audio file")   
		return
	
	# if audio file is no a .wav FIXME: It must support more audio type
	if ".wav" not in file[-5:]:
		print_d("no wav, exit!")
		messagebox.showwarning("Warning", "Please, audio file must be in a .wav format")   
		return

	# get start and end point from hh:mm:ss in ms
	ms_start, ms_end = time_2_ms(start, end)
	print_d("Loading audio file...")

	# load audio file
	audio = AudioSegment.from_wav(file)
	if ms_start == 0:
		start = "00:00:00"
	if ms_end == 0:
		end = "00:00:00"
		# set ms_end at len of audio if end was set to 0
		ms_end = len(audio)
	print_d("File: "+file+"\nStart: "+start+" ("+str(ms_start)+") \nEnd: "+end+" ("+str(ms_end)+" ms)")
	file_list = []	# in it, store list of chunk file saved
	chunks = []		# in it, store all chunks (see class Chunk)
	threads = []	# in it, store threads which execute chunk (see class Parsing)

	# split audio file in chunks according to chunk_size, from ms_start to ms_end
	i = ms_start
	j = 1
	while i < ms_end:
		chunk = audio[ms_start:ms_start+chunk_size]	# split audio file in a chunk of chunk_size size
		chunk_file = file+"_chunk_"+str(j)+".wav"	# name of file (ex. demo.wav_chunk_1.wav)
		chunks.append(Chunk(j-1, chunk, chunk_file, ms_start, ms_start+chunk_size))	# store the Chunk instance into list
		file_list.append(chunk_file)	# append file to file_list (it will be use to eliminate these tmp files)

		# update var for while loop
		ms_start += chunk_size
		i = ms_start
		j += 1

	chunks_num = len(chunks)	# number of chunks created
	Parsing.text = [False]*(chunks_num-1)	# used to print partial result in log text box
	print_d("#Chunks: "+str(chunks_num))

	# if there are more chunks than threads, set threads number to chunks number
	if chunks_num < THREADS:
		THREADS = chunks_num

	# distribuite in equal part chunks to threds. If even, the last thread will have more chunks
	s = math.floor(chunks_num/THREADS)
	j = 0
	n_thread = 0
	for i in range(THREADS):
		threads.append(Parsing(chunks[j:j+s], n_thread))
		j = j+s
		n_thread += 1
	if s != math.ceil(chunks_num/THREADS):
		for c in chunks[j:]:
			threads[-1]._chunks.append(c)
	
	# start parsing
	print_d("Starting threads...")
	for t in threads:
		t.start()
	print_d("Waiting for finish...")

	# start thread that print partial result in order. See class PrintPartial for more information
	if out:
		print_partial = PrintPartial(out, chunks)
		print_partial.start()

	for t in threads:
		t.join()

	# at the end, save the result in text
	text = ""
	for t in threads:
		text += t._text+"\n"

	finish_parse(text, file_list, "save.txt", out)
	elapsed_time = time.time() - start_time
	print_d("Tempo esecuzione: "+str(elapsed_time))

def finish_parse(text, file_list, filename="save.txt", gui=True):
	""" Invoke at the end of parsing. It save the result on file and show it
		on log text box. Furthermore, delete created chunks file and show a pop up
		that inform for the finish.

	Parameters:
		text (str): result
		file_list (list): list of file to be delete (chunks)
		filename (str): file to save result
		gui (ScrolledText): text box to show result
	"""
	print_d("Finish!")

	# save result on file
	with open(filename, "w+") as f:
		print_d("Writing response on file "+filename+"...")
		f.write(text)

	# delete files
	for f in file_list:
		print_d("Deleting file "+str(f)+"...")
		os.remove(f)
	
	# show result in text box and show pop up
	if gui:
		tb_replace(gui, "------------ RESULT -----"+text)
		messagebox.showinfo("Info", "Finish. Result saved on "+filename)

#------------------ MAIN ------------------------------------------------------
if __name__ == "__main__":

	#-------------- Get and handle params -------------------------------------
	args = misc.handle_params()
	THREADS = args["threads"]
	misc.TRACE = args["trace"]

	print_d("Args: "+str(args))

	# if debug is on, set default values
	if args["debug"]:
		file = "demo.wav"
		start = "00:00:00"
		end = "00:06:00"
	# if nogui is on, start without gui
	if args["nogui"]:
		if args["debug"] in sys.argv:	
			start_parse(file, start, end)
		# if debug is off, get params values
		else:
			file = args["file"]
			start = args["start"] #00:00:00
			end = args["end"]  #00:02:00
			start_parse(file, start, end)
		exit()    

	#------------------ Create Windows --------------------------------------------
	window = MainWindow()
	window.create_window()

	#------------------ Frame select file -----------------------------------------
	# frame top left
	f_select_file = SelectFileFrame(master=window, x=0.0, y=0.0, h=0.25, w=0.4) 

	# string to put in select file button, it will become the file name
	t_selected_file = tk.StringVar(master=f_select_file, value="select file audio to parse...")

	# select file button
	b_select_file = tk.Button(f_select_file, name="b_select_file", textvariable=t_selected_file,
				command=lambda: [browse(t_selected_file)])

	# label above select file button
	l_above_select_button = tk.Label(f_select_file, text="Input audio file: ")

	l_above_select_button.pack()
	b_select_file.pack()

	#------------------ Frame options ---------------------------------------------
	# frame top right
	f_options = OptionsFrame(master=window, x=0.5, y=0.0, h=0.25, w=0.4)

	# labels beside the text box
	l_start = tk.Label(f_options, text="Start at (hh:mm:ss)")
	l_start.grid(row=0)
	l_end = tk.Label(f_options, text="End at (hh:mm:ss)")
	l_end.grid(row=1)

	# text box where write start and end point
	e_start = tk.Entry(f_options)
	e_start.insert(0, "00:00:00")
	e_end = tk.Entry(f_options)
	e_end.insert(0, "00:00:00")
	e_start.grid(row=0, column=1)
	e_end.grid(row=1, column=1)

	tb_out = scrolledtext.ScrolledText()	# text box of the output

	# buttons to start and quit program
	b_start = tk.Button(f_options, text='Start', name="b_start",
			command=lambda: Thread(target=start_parse, args=(t_selected_file.get(), e_start.get(), e_end.get(), tb_out)).start())
	b_start.grid(row=3, column=0, sticky=tk.W, pady=4)
	b_quit = tk.Button(f_options, text='Force quit', name="b_quit", command=lambda: exit())
	b_quit.grid(row=3, column=1, sticky=tk.W, pady=4)

	#------------------ Frame output ----------------------------------------------
	f_out = OutputFrame(master=window, x=0.1, y=0.3, h=0.6, w=0.8)

	# output text box 
	tb_out = scrolledtext.ScrolledText(f_out, undo=True, height=15)
	tb_out.pack(expand=True, fill='both')

	# setting up output box
	tmp_str = "1. Select an audio file\n"
	tmp_str += "2. Set range to parse (left blank if the whole file)\n"
	tmp_str += "3. Press Start button\n"
	tmp_str += "In this box you will see log and result"
	tb_out.insert(tk.INSERT, tmp_str)

	#------------------ Start window ----------------------------------------------
	window.mainloop()