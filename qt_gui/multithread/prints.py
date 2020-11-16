import time, sys, os, speech_recognition as sr
from threading import Thread
from qt_gui.utils.misc import print_d
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from qt_gui.core.didi import _Parsing, _Start
from qt_gui.utils.waitingspinnerwidget import QtWaitingSpinner

class PrintFinish(QObject):

    finish_signal = pyqtSignal(_Start)

    def __init__(self):
        QObject.__init__(self)

    def update(self, topic, data):
        print_d("Finish all update", 2)
        self.finish_signal.emit(data)

class PrintPartial(QObject):

    print_partial = pyqtSignal(str)
    DONE = 1
    TOTAL = 100


    def __init__(self, chunks_num):
        QObject.__init__(self)
        self.chunks = [-1]*chunks_num
        PrintPartial.TOTAL = chunks_num
        self.now = 0
        pass

    def update(self, topic, data):
        print_d("printpartial update")
        PrintPartial.DONE += 1
        number = data._number
        self.chunks[number] = data
        if self.chunks[self.now] != -1:
            if self.now == 0:
                text = "---------- PARTIAL RESULT -----------\n"+self.chunks[self.now]._text
            else:
                text = self.chunks[self.now]._text
            print_d(str(self.now)+": to print")
            self.now += 1
            self.print_partial.emit(text) # refers to didispeech.start_parse

class PrintLoadingAudio(QThread):
    # FIXME: CLOSE THAT SHIT
    def __init__(self, context, t_get_audio):
        QThread.__init__(self, context)
        self._context = context
        self._t_get_audio = t_get_audio
        self._running = True

    def stop(self):
        self.dialog.close()
        self.spinner.stop()

    def run(self):

        self.dialog = QDialog()
        grid = QGridLayout()
        groupbox1 = QGroupBox()
        groupbox1_layout = QHBoxLayout()
        self.dialog.setLayout(grid)
        self.dialog.setWindowTitle("QtWaitingSpinner Demo")
        self.dialog.setWindowFlags(Qt.Dialog)

        # SPINNER
        self.spinner = QtWaitingSpinner(self.dialog)
        self.spinner.setRoundness(70.0)
        self.spinner.setMinimumTrailOpacity(15.0)
        self.spinner.setTrailFadePercentage(70.0)
        self.spinner.setNumberOfLines(12)
        self.spinner.setLineLength(10)
        self.spinner.setLineWidth(5)
        self.spinner.setInnerRadius(10)
        self.spinner.setRevolutionsPerSecond(1)
        self.spinner.setColor(QColor(81, 4, 71))
        # Layout adds
        groupbox1_layout.addWidget(self.spinner)
        groupbox1.setLayout(groupbox1_layout)

        grid.addWidget(groupbox1, *(1, 1))

        self.spinner.start()
        self.dialog.exec_()


class PrintLoading(QThread):

    print_loading = pyqtSignal(str,bool)

    def __init__(self, parent, fixed_text="Loading", changing_text=[".","..","..."]):
        QThread.__init__(self, parent)
        self._parent = parent
        self._fixed_text = fixed_text
        self._changing_text = changing_text
        self._last_printed = fixed_text

    def run(self):
        i = 0
        tb_text = self._fixed_text
        percent = 0
        while PrintPartial.DONE < PrintPartial.TOTAL:
            self.print_loading.emit(tb_text,True)
            time.sleep(0.8)
            print("DONE"+ str(PrintPartial.DONE))
            print(PrintPartial.TOTAL)
            if PrintPartial.TOTAL != 0:
                percent = round( (PrintPartial.DONE / PrintPartial.TOTAL)*100, 2)
            tb_text = self._parent.tb_get_text()
            new_print = str(percent)+"%\t" + self._fixed_text + str(self._changing_text[i])
            tb_text = tb_text.replace(self._last_printed, new_print)
            self._last_printed = new_print

            i = (i+1)%len(self._changing_text)