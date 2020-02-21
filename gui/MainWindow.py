import tkinter as tk
from tkinter import scrolledtext
from threading import Thread

class MainWindow(tk.Tk):
	
	def __init__(self, size_x=700, size_y=400, resizable_x=True, resizable_y=True, title="Title"):
		super().__init__()
		self._size_x = size_x
		self._size_y = size_y
		self._resizable_x = resizable_x
		self._resizable_y = resizable_y
		self._title = title

	def create_window(self):
		super().geometry(str(self._size_x)+"x"+str(self._size_y))
		super().title(self._title)
		super().resizable(self._resizable_x, self._resizable_y)
