#!/usr/bin/python3

import PyQt5.QtWidgets as qt
from os import path
from qt_gui.gui.didspeech import Didspeech
from qt_gui.utils import misc
from qt_gui.core.didi import Didi


if __name__=='__main__':

	# Creating app:
	#   > create all widgets and layout
	#	> put widgets inside layout
	#	> set up button behave
	params = misc.get_params()

	if params["nogui"]:
		audio = misc.get_audio(params["file"])
		ms_s, ms_e = misc.time_2_ms(params["start"], params["end"])
		didi = Didi(None, audio, ms_s, ms_e, params["output"])
		didi.create_chunks(params["file"], chunk_size=10000)
		didi.start_parsing()
		exit()

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

	window.setStyleSheet(" background-image: url(" +path.join("resources", "images","wallpaper.jpg")+ "); background-attachment: fixed;") 
	didspeech.exec_()
