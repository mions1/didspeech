import argparse, tkinter as tk
from tkinter import filedialog

TRACE = 1

def print_d(text, level=1):
	""" Enable trace to print tracing. Higher levels means more details
	"""
	if TRACE == level:
		print(str(text))

def handle_params():
	parser = argparse.ArgumentParser(description="didspeech allow you to transcrive your audio file",
				epilog="For every suggestion, please contact <simone.mione1@gmail.com>")
	parser.add_argument("-f", "--file", help="Audio file to parse, mandatory")
	parser.add_argument("-o", "--output", help="Output file for saving data. Default: 'save.txt'", default='save.txt')
	parser.add_argument("-s", "--start", help="Start point. Default: '00:00:00'", default='00:00:00')
	parser.add_argument("-e", "--end", help="Start point. Default: end of file", default='')
	parser.add_argument("-t", "--tracing", help="Print tracing (level). Default: 1", default=1)
	parser.add_argument("--chunk_size", help="Set chunk_size in ms. Audio file will be sampling in chunk of chunk_size lenght. Default: 50000", default=50000)
	parser.add_argument("-T", "--threads", help="Set threads number for multi_threading. Default: 4", default=4)
	parser.add_argument("-d", "--debug", help="Set default value. File: 'demo.wav' start: '00:00:00' end: '00:10:00'", action='store_true', default=False)
	parser.add_argument("--nogui", help="Start without gui", action='store_true', default=False)
	args = parser.parse_args()

	file = args.file
	output = args.output
	start = args.start
	end = args.end
	trace = args.tracing
	chunk_size = args.chunk_size
	threads = args.threads
	nogui = args.nogui
	debug = args.debug

	return {"file": file, 
			"output": output, 
			"start": start, 
			"end": end, 
			"trace": trace,
			"chunk_size": chunk_size,
			"threads": threads, 
			"nogui": nogui, 
			"debug": debug}

def browse(label):
	""" Allow user to select a directory

	Parameters:
		label (StringVar): Label to set with folder path
	"""
	print_d("Selecting file...")
	filename = filedialog.askopenfilename()
	if filename == () or filename == '':
		filename = "No file selected..."
	#label.set(filename[filename.rfind("/")+1:])
	print_d("Selected file: "+str(filename))
	label.set(filename)

def browse_kivy():
	pass

def tb_replace(tb, text, replace=True):
	""" Replace (or append) text in a textbox
	"""
	if replace:
		tb.delete("1.0", tk.END)
	tb.insert(tk.INSERT, text)
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