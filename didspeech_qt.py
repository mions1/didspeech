import speech_recognition as sr
import sys, os, math, time, argparse
import PyQt5.QtWidgets as qt
from os import path

from os import path
from pydub import AudioSegment
from threading import Thread
from qt_gui.utils import misc
from qt_gui.utils.misc import print_d, time_2_ms
from qt_gui.multithread import *
from PyQt5.QtGui import QIcon, QPalette, QBrush, QPixmap
from qt_gui.gui.didspeech import Didspeech
from qt_gui.utils import misc

if __name__=='__main__':
	# Creating app:
	#   > create all widgets and layout
	#	> put widgets inside layout
	#	> set up button behave
	params = misc.get_params()

	didspeech = Didspeech()
	didspeech.init()

	#-------------- Create window ---------------------------------------------
	window = qt.QFrame()
	main_frame = qt.QGridLayout()
	
	# put all subframe created earlier inside main_frame
	main_frame.addLayout(didspeech._f_select_file, 0,0)
	main_frame.addLayout(didspeech._f_options, 1,0,1,1)
	main_frame.addLayout(didspeech._f_output, 2,0,2,2)

	window.resize(700, 500)
	window.setLayout(main_frame)
	
	window.show()

	window.setStyleSheet(" background-image: url(resources/wallpaper3.jpg); background-attachment: fixed;") 
	didspeech.exec_()
