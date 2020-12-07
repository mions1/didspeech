import threading, os
import PyQt5.QtWidgets as qt
import PyQt5.QtCore as qtc
import PyQt5.QtGui as qtg

from os import path
from pydub import AudioSegment
from qt_gui.utils.misc import print_d, time_2_ms, ms_2_time, is_video, get_audio
from qt_gui.multithread.multithread import GetAudio
from qt_gui.multithread.prints import PrintPartial, PrintLoading, PrintFinish, PrintLoadingAudio
from qt_gui.core.didi import Didi, _Start

import moviepy.editor

class Start(qtc.QThread):
    """ Handle the thread which is parsing, in order to let GUI responsive.
        The main job is to start thread and wait the end of the parse.
        In the end, it emit a signal and send the output,
        which is the extracted text.
    """
    is_finish = qtc.pyqtSignal(str)	 # signal to notify end of jobs

    def __init__(self, context, didi_core):
        """ Init

        Parameters:
            context (Didspeech): the QApp, used for __init__ of QThread
            didi (core.Didi): the core of the app
        """
        qtc.QThread.__init__(self, context)
        self.didspeech = context
        self.didi_core = didi_core

    def run(self):
        self.didi_core.start_parsing()


class Didspeech(qt.QApplication):
    """ Handle application.
        Create layouts and widgets, connect buttons and
        handle their functions.
    """

    elapsed_time = 0
    done = 0
    chunks_num = 0

    def __init__(self, file="Select file...", chunk_size=50000, output_file="save.txt", options=[]):
        """ Main class, application

        Parameters:
            file (str): input file. If it is not selected, there is a fixed string "Select file..."
            chunk_size (int): length of every chunk (so, a piece of audio)
            output_file (str): output file name
            options (list): options for super.__init__
        """
        super().__init__(options)
        self._file = file
        self._start = ""
        self._end = ""
        self._chunk_size = chunk_size
        self._output_file = output_file
        self.left = 0
        self.done = 0

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
        """ Check if a file is selected or if the format is allowed
        :param selected: string, selected file, label on "b_selected_file"
        :return: the file extension if it's ok, False otherwise
        """

        res = Didi.check_file(selected)
        if res == Didi.NO_ALLOWED_EXTENSION:
            self.message_dialog("Error",
                                "Please, audio file must be in a supported type" + str(Didi.SUPPORTED_FILE),
                                icon=qt.QMessageBox.Critical)
            return False
        elif res == Didi.NO_FILE_SELECTED:
            self.message_dialog("Error", "Please, select a file first", icon=qt.QMessageBox.Critical)
            return False
        else:
            return res

    def set_file(self):
        """ Browse into filesystem to choose an audio file

        """

        all_supported = "All supported format ("
        file_types = []
        for file_type in Didi.SUPPORTED_FILE:
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

            # FIXME: EXCLUDE M4A FROM ALLOWED FORMAT

            t_get_audio = GetAudio(self, self._file)
            t_loading_audio = PrintLoadingAudio(self, t_get_audio)

            t_get_audio.start()
            t_loading_audio.start()

            t_get_audio.audio_loaded_signal.connect(t_loading_audio.stop)
            t_get_audio.audio_loaded_return_signal[object].connect(self.set_audio)

            """
            print(self.audio)
            self.audio = get_audio(self._file)
            self._audio = AudioSegment.from_file(self._file, file_type)
            print_d("Audio len: "+str(ms_2_time(len(self._audio))), 1)
            self._e_end.setText(ms_2_time(len(self._audio)))
            self._b_start.setEnabled(True)
            return choose[0]
            """

    def set_audio(self, audio):
        self._audio = audio
        print("AUDIO: ", self._audio)
        print_d("Audio len: " + str(ms_2_time(len(self._audio))), 1)
        self._e_end.setText(ms_2_time(len(self._audio)))
        self._b_start.setEnabled(True)

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

        # if ms_start == 0 maybe self._start is unset, so adjust it
        if ms_start == 0:
            self._start = "00:00:00"
        # same for ms_end. Further, if ms_end == 0, set ms_end to audio length
        if ms_end == 0:
            self._end = "00:00:00"
            ms_end = len(self._audio)

        #---------- Setting up threads ----------------------------------------
        print_d("File: "+self._file+"\nStart: "+self._start+" ("+str(ms_start)+") \nEnd: "+self._end+" ("+str(ms_end)+" ms)")

        didi = Didi(self, audio=self._audio, ms_start=ms_start, ms_end=ms_end, output=self._output_file)
        didi.create_chunks(prefix=self._file, chunk_size=5000)
        self.file_list = didi.file_list
        self.left = len(didi.chunks)

        # start parsing
        starter = Start(self, didi)
        starter.start()

        # loading_thread is for print loading string
        print_d("Print Loading...", 2)
        loading_thread = PrintLoading(self, "Loading", [".","..","..."])
        loading_thread.start()
        loading_thread.print_loading[str,bool].connect(self.tb_insert)

        # disable button to avoid problems
        self._b_start.setEnabled(False)
        # start thread that print partial result in order. See class PrintPartial for more information

        print_partial = PrintPartial(len(didi.chunks))
        didi.addChunkListener(print_partial)
        print_partial.print_partial[str].connect(self.tb_insert)

        finish = PrintFinish()
        didi.addAllListener(finish)
        finish.finish_signal[_Start].connect(self.finish_parse)

    def finish_parse(self, data):
        """ Invoke at the end of parsing. It save the result on file and show it
            on log text box. Furthermore, delete created chunks file and show a pop up
            that inform for the finish.

        Parameters:
            text (str): result
            file_list (list): list of file to be delete (chunks)
            filename (str): file to save result
            gui (ScrolledText): text box to show result
            data (_Start): result
        """

        text = data._text
        # re-enable button
        self._b_start.setEnabled(True)
        print_d("Finish!")

        # show result in text box and show pop up
        self.tb_insert("------------ RESULT -----\n"+text, replace=True)
        self.message_dialog("Finish", "Parsing finished in "+str(round(data.elapsed_time, 2))+"s.", "Result saved on "+self._output_file, qt.QMessageBox.Information)

        # (SystemJob(self, 'vlc "'+self._file+'"')).start()

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
