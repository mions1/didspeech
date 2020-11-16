class Chunk():
	def __init__(self, number, chunk, filename, start="00:00:00", end="00:00:00"):
		self._number = number
		self._chunk = chunk
		self._filename = filename
		self._start = start
		self._end = end
		self._done = False
		self._text = ""

	def __str__(self):
		return ("File: "+str(self._filename)+" Start: "+str(self._start)+" End: "+str(self._end))