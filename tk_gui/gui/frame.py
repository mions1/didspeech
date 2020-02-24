import tkinter as tk


class SelectFileFrame(tk.Frame):

	def __init__(self, master=None, x=0.0, y=0.0, h=0.25, w=0.4):
		super().__init__(master)
		super().place(relx=x, rely=y, relheight=h, relwidth=w)

class OptionsFrame(tk.Frame):

	def __init__(self, master=None, x=0.5, y=0.0, h=0.25, w=0.4):
		super().__init__(master)
		super().place(relx=x, rely=y, relheight=h, relwidth=w)

class OutputFrame(tk.Frame):

	def __init__(self, master=None, x=0.5, y=0.0, h=0.25, w=0.4):
		super().__init__(master)
		super().place(relx=x, rely=y, relheight=h, relwidth=w)