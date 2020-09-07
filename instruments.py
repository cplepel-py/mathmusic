class Instrument:
	def __init__(self, name: str, abbr: str=None, midi: int=1, clef: str="G"):
		self.name = name
		self.abbr = abbr if abbr else name
		self.midi = midi
		self.clef = clef
	
	def write(self, num=0):
		return f"""<score-part id="P{num}">
			<part-name>{self.name}</part-name>
			<part-abbreviation>{self.abbr}</part-abbreviation>
			<midi-instrument id="P{num}-I1">
				<midi-channel>1</midi-channel>
				<midi-program>{self.midi}</midi-program>
				<volume>80</volume>
				<pan>0</pan>
			</midi-instrument>
		</score-part>"""
