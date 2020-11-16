import speech_recognition as sr
import os, time, sys

from threading import Thread
from qt_gui.utils.misc import print_d
from qt_gui.utils import misc
from qt_gui.core.chunk import Chunk


class Didi:

    # TOADD: supported formats
    SUPPORTED_FILE = ["wav",
                      "ogg",
                      "flv",
                      "wma",
                      "aac",
                      "mp3",

                      "mp4",
                      "avi",
                      "m4a",
                      ]
    NO_FILE_SELECTED = 0
    NO_ALLOWED_EXTENSION = 1
    OK_FILE_SELECTED = 2

    def __init__(self, context, audio, ms_start=0, ms_end=0, output="save.txt", qt=None):
        self.context = context
        self.qt = qt
        self.audio = audio
        self.ms_start = ms_start
        self.ms_end = ms_end if ms_end > ms_start else len(audio)
        self.output = output
        self.chunks = []
        self.file_list = []
        self.threads = []

        self.chunk_listener = _Listener()
        self.thread_listener = _Listener()
        self.all_listener = _Listener()

    def addChunkListener(self, object):
        self.chunk_listener.addReader(_Listener.CHUNK_FINISH, object)

    def addThreadListener(self, object):
        self.thread_listener.addReader(_Listener.THREAD_FINISH, object)

    def addAllListener(self, object):
        self.all_listener.addReader(_Listener.ALL_FINISH, object)

    def create_chunks(self, prefix="tmp", chunk_size=50000):

        print_d("Creating chunks...", 0)
        i = self.ms_start
        j = 1
        tmp_size = round((self.ms_end - self.ms_start) / chunk_size)
        while i < self.ms_end:
            print_d("Chunk #" + str(j), 2)
            # split audio
            if self.ms_start + chunk_size > self.ms_end:
                chunk = self.audio[self.ms_start:self.ms_end - 1]
            else:
                chunk = self.audio[self.ms_start:self.ms_start + chunk_size]
            # create associated file (named like: filename_chunk_1.wav) and add it into a list (this files will be delete in the end)
            chunk_file = prefix+ "_chunk_" + str(j) + ".wav"

            self.file_list.append(chunk_file)
            # create Chunk istance and add it to a list
            self.chunks.append(Chunk(j - 1, chunk, chunk_file, self.ms_start, self.ms_start + chunk_size))

            # update var for while loop
            self.ms_start += chunk_size
            i = self.ms_start
            j += 1
            print_d(str(j/tmp_size*100)+"%", 1, end="\r")
        print_d("chunks created!", 0)

    def init_threads(self):

        if len(self.chunks) == 0:
            self.create_chunks(chunk_size=len(self.audio))
        chunks_num = len(self.chunks)  # number of chunks created
        print_d("#Chunks: " + str(chunks_num), 1)
        # if there are more threads than chunks, set threads number to chunks number
        if chunks_num < misc.THREADS:
            misc.THREADS = chunks_num

        # split in equal part chunks to threads. If odd, the last thread will have more chunks
        i = 0
        split_chunks = [[] for i in range(misc.THREADS)]
        for c in self.chunks:
            split_chunks[i % misc.THREADS].append(c)
            i += 1
        i = 0
        n_thread = 0
        for chunk in split_chunks:
            self.threads.append(_Parsing(self, self.qt, chunk, n_thread))
            n_thread += 1
        _Parsing.text = [False] * (chunks_num)  # used to print partial result in log text box

    def start_parsing(self):
        # start parsing
        if len(self.threads) == 0:
            self.init_threads()

        starter = _Start(self, self.threads, self.qt)
        starter.start()
        starter.join()
        self.finish_parse(starter._text)

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
        # save result on file
        with open(self.output, "w+") as f:
            print_d("Writing response on file " + self.output + "...", 0)
            text = text[0].upper() + text[1:].lower()
            print_d(text)
            f.write(text)
            print_d("finish to write on file!", 0)

        # delete files
        for f in self.file_list:
            print_d("Deleting file " + str(f) + "...", 1)
            os.remove(f)
        print_d("All deleted!", 1)

        # (SystemJob(self, 'vlc "' + self._file + '"')).start()

    @staticmethod
    def check_file(file):
        """ Check if a file is selected or if the format is allowed
        :param file: string, selected file, label on "b_selected_file"
        :return: the file extension if it's ok, False otherwise
        """
        # if no file selected, return
        if file == "":
            return Didi.NO_FILE_SELECTED

        # if audio file is not an allowed format
        else:
            ext = file[file.rfind(".") + 1:]
            if ext not in Didi.SUPPORTED_FILE:
                print_d("file not supported yet, exit!", 1)
                return Didi.NO_ALLOWED_EXTENSION
            else:
                return ext

class _Start(Thread):

    def __init__(self, context, threads, qt=None):
        """ Init

        Parameters:
            threads (list): list of Threads from multithread.Parsing
            loading_thread (QThread): Thread that print a loading string while computing
        """
        Thread.__init__(self)
        self.context = context
        self.qt = qt
        self._threads = threads
        self.exiting = False
        self._text = ""

    def run(self):
        start_time = time.time()

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
            t.join()

        # at the end, save the result in text
        text = _Parsing.text
        for t in text:
            if t:
                self._text += t + "\n"
        _Parsing.text = []

        # stop parsing thread
        self.elapsed_time = time.time() - start_time

        self.context.all_listener.update(_Listener.ALL_FINISH, self)
        print_d("Run time: " + str(self.elapsed_time))


class _Parsing(Thread):

    file = None
    text = []

    def __init__(self, context, qt=None, chunks=[], name=""):
        Thread.__init__(self)
        self._r = sr.Recognizer()
        self.context = context
        self._qt = qt
        self._chunks = chunks
        self._done = 0
        self._text = ""
        self._name = str(name)
        self.exiting = False

    def run(self):
        print_d("Thread #" + self._name + " starting...")
        for c in self._chunks:
            print_d("Thread #" + self._name + " start " + str(c))
            c._chunk.export(c._filename, format="wav")
            wav = sr.AudioFile(c._filename)

            with wav as source:
                self._r.pause_threshold = 3.0
                listen = self._r.listen(source)

            try:
                print_d("Thread #" + self._name + " recongizing...")
                text_tmp = self._r.recognize_google(listen, language="it-IT")
                print_d("Thread #" + self._name + " recongized!")
                self.finish_a_chunk(c, text_tmp)
            except Exception as e:
                print(e)

        print_d("Thread #" + self._name + " finished")
        self.context.thread_listener.update(_Listener.THREAD_FINISH, self)
        pass

    def finish_a_chunk(self, chunk, txt):
        self._text += "\n" + txt
        chunk._done = True
        _Parsing.text[chunk._number] = txt
        chunk._text = txt
        self._done += 1
        if self._qt:
            self._qt.done += 1
        self.context.chunk_listener.update(_Listener.CHUNK_FINISH, chunk)
        print_d("Thread #" + self._name + " finishes a chunk")

    def __str__(self):
        return ("File: " + str(self._chunks))


class _Listener:

    CHUNK_FINISH = "CHUNK_FINISH"
    THREAD_FINISH = "THREAD_FINISH"
    ALL_FINISH = "ALL_FINISH"

    def __init__(self):
        self._readers = dict()

    def update(self, topic, data=None):
        if topic in self._readers:
            for reader in self._readers[topic]:
                print_d("["+str(topic)+"] Updating "+str(reader))
                reader.update(topic, data)

    def addReader(self, topic, object):
        if topic not in self._readers:
            self._readers[topic] = []
        self._readers[topic].append(object)
