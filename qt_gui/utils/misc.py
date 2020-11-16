import argparse
from pydub import AudioSegment

TRACE = 2
THREADS = 4

def print_d(text, level=1, end="\n"):
	""" Enable trace to print tracing. Higher levels means more details
	"""
	if level <= TRACE:
		print(str(text), end=end)

def get_params():
	global TRACE

	parser = argparse.ArgumentParser(description="didspeech allow you to transcrive your audio file",
				epilog="For every suggestion, please contact <simone.mione1@gmail.com>")
	parser.add_argument("-f", "--file", help="Audio file to parse, mandatory")
	parser.add_argument("-o", "--output", help="Output file for saving data. Default: 'save.txt'", default='save.txt')
	parser.add_argument("-s", "--start", help="Start point. Default: '00:00:00'", default='00:00:00')
	parser.add_argument("-e", "--end", help="Start point. Default: end of file", default='00:00:00')
	#parser.add_argument("-ms", "--ms_start", help="Start point in ms. Default: 0", default='0')
	#parser.add_argument("-me", "--ms_end", help="Start point in ms. Default: end of file", default='')
	parser.add_argument("-t", "--tracing", help="Print tracing (level). Default: 1", default=1)
	parser.add_argument("--chunk_size", help="Set chunk_size in ms. Audio file will be sampling in chunk of chunk_size lenght. Default: 50000", default=50000)
	parser.add_argument("-T", "--threads", help="Set threads number for multi_threading. Default: 4", default=4)
	parser.add_argument("-d", "--debug", help="Set default value. File: 'demo.wav' start: '00:00:00' end: '00:10:00'", action='store_true', default=False)
	parser.add_argument("--nogui", help="Start without gui", action='store_true', default=False)
	args = parser.parse_args()

	if args.nogui and args.file is None:
		parser.error("--nogui requires --file.")

	file = args.file
	output = args.output
	start = args.start
	end = args.end
	#ms_start = args.ms_start
	#ms_end = args.ms_end
	trace = int(args.tracing)
	TRACE = trace
	chunk_size = args.chunk_size
	threads = args.threads
	nogui = args.nogui
	debug = args.debug

	return {"file": file, 
			"output": output, 
			"start": start, 
			"end": end,
			#"ms_start": ms_start,
			#"ms_end": ms_end,
			"trace": trace,
			"chunk_size": chunk_size,
			"threads": threads, 
			"nogui": nogui, 
			"debug": debug}

def time_2_ms(start, end):
	""" It converts start and end from "hh:mm:ss" in ms
	"""
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

def ms_2_time(ms):

	ss = int(ms/1000)%60
	if ss < 10:
		ss = "0"+str(ss)
	mm = int((ms/(60*1000)) % 60)
	if mm < 10:
		mm = "0"+str(mm)
	hh = int(ms/(60*60*1000)%24)
	if hh < 10:
		hh = "0"+str(hh)

	return str(hh)+":"+str(mm)+":"+str(ss)

def is_video(file):
	extensions = ["mp4",
				"avi",
				"mvk",
				]
	ext = file[file.rfind(".")+1:]
	if ext in extensions:
		return True
	else:
		return False

def get_audio(*file):
	file = file[0]
	audio_type = file[file.rindex(".")+1:]
	print_d("Loading audio...", 0)
	audio = AudioSegment.from_file(file, audio_type)
	print_d("Audio loaded!", 0)
	return audio