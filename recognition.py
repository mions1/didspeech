import speech_recognition as sr
import sys, os, time
from tkinter import filedialog
from tkinter import *
from tkinter import scrolledtext, messagebox
from tkinter.ttk import *
from os import path
from pydub import AudioSegment

TRACE = 1

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
    if tb == None:
        return
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

def start_parse(file, start="00:00:00", end="00:00:00", out=None, chunk_size=50000):  
    """ Main function, start parsing process
    """
    
    start_time = time.time()
    print_d("Starting parse...")
    
    if "..." in file[-4:]:
        print_d("no file selected, exit!")
        messagebox.showwarning("Warning", "Please, specified an audio file")   
        return
    
    if ".wav" not in file[-5:]:
        print_d("no wav, exit!")
        messagebox.showwarning("Warning", "Please, audio file must be in a .wav format")   
        return

    print_d("File: "+file+"\nStart: "+start+"\nEnd: "+end)
    
    tb_replace(out, "I'm creating a new audio file cutting at requested range...\n")
    ms_start, ms_end = time_2_ms(start, end)
    print_d("Loading audio file...")
    audio = AudioSegment.from_wav(file)
    if ms_end == 0:
        ms_end = len(audio)
    text = ""
    file_list = []
    r = sr.Recognizer()
    i = ms_start
    j = 1
    while i < ms_end:
        print_d("Cutting and creating audio file #"+str(j)+" ("+str(ms_start)+" ms:"+str(ms_start+chunk_size)+" ms)...") 
        chunk = audio[ms_start:ms_start+chunk_size]
        chunk_file = file+"_chunk_"+str(j)+".wav"
        file_list.append(chunk_file)
        chunk.export(chunk_file, format="wav")

        wav = sr.AudioFile(chunk_file) # formati riconosciuti: .aiff .flac .wav

        with wav as source:
            print_d("Computing result #"+str(j)+"...")
            if j==1:
                tb_replace(out, "I'm computing result, please wait, it can take several minutes according to audio length, please don't touch anything until you read 'Finish'...\n", False)
            r.pause_threshold = 3.0 
            listen = r.listen(source)
        try:
            text += r.recognize_google(listen, language="it-IT")
            if out:
                if j==1:
                    tb_replace(out, "------------------------\nResult:\n----------------\n", False)
                tb_replace(out, text, False)
            print("Google response: \n"+str(text))
        except Exception as e:
            if out:
                tb_replace(out, "Sorry, there was an problem, please send this log to awesome Simone\n"+str(e), False)
            print(e)
        
        ms_start += chunk_size
        i = ms_start
        j += 1

    elapsed_time = time.time() - start_time
    print("Tempo: "+str(elapsed_time))
    finish_parse(text, file_list)
    tb_replace(out, "\n--------------------------------FINISH-------------------------\n", False)

def finish_parse(text, file_list, filename="save.txt"):
    print_d("Finish!")
    with open(filename, "w+") as f:
        print_d("Writing response on file "+filename+"...")
        f.write(text)
    
    for f in file_list:
        print_d("Deleting file "+str(f)+"...")
        os.remove(f)
    
    messagebox.showinfo("Info", "Finish. Result saved on "+filename)    
        

if "--nogui" in sys.argv:
    if "--debug" in sys.argv:
        file = "demo.wav"
        start = "00:00:00"
        end = "00:02:00"
    else:
        file = sys.argv[1]
        start = sys.argv[2] #00:00:40
        end = sys.argv[3]   #00:01:15
        
    start_parse(file, start, end)
    
    exit()    

#---------------- Create Windows ----------------------------------------------
window = Tk()
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
b_start = Button(window, text='Start', command=lambda: start_parse(t_selected_file.get(), e_start.get(), e_end.get(), tb_out)).grid(row=3, column=0, sticky=W, pady=4)
b_quit = Button(window, text='Quit', command=window.quit).grid(row=3, column=1, sticky=W, pady=4)

#--------------- Textbox output -----------------------------------------------
f_out = Frame(window)
f_out.place(relx=0.0, rely=0.3)

tb_out = scrolledtext.ScrolledText(f_out, undo=True, height=15)
tb_out.pack(expand=True, fill='both')

tb_out.insert(INSERT, "1. Select an audio file\n2. Set range to parse (left blank if the whole file)\n3. Press Start button\nIn this box you will see log and result")

#--------------- Start --------------------------------------------------------
window.mainloop()
