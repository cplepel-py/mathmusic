"""mathmusic file input/output module

This module contains the file input and output functions used in the
mathmusic package. These functions read and write files in the MusicXML
format.
"""
from typing import Sequence, List, Optional
import os

from jinja2 import Environment, FileSystemLoader

from mathmusic.music import Part
from mathmusic.util import NOTE_LENS, INV_NOTE_LENS, REST_LENS


class Instrument:
	def __init__(self, name: str, abbr: Optional[str]=None, midi: int=1,
				 clef: str="G") -> None:
		"""Inits an Instrument.
		
		Args:
			name: A string, the name of this instrument. (Required)
			abbr: A string, the abbreviation of this instrument. If
				omitted or passed as None, the name of this instrument
				is also used as its abbreviation. (Default None)
			midi: An integer, the MIDI program number used to perform
				this instrument. (Default 1)
			clef: A string, the (letter) name of the clef this
				instrument's part is written in. (Default "G")
		"""
		self.name = name
		self.abbr = abbr if abbr else name
		self.midi = midi
		self.clef = clef
	
	def copy(self, name: str=None, abbr: str=None, midi: int=None, clef: str=None):
		"""Returns a copy of this Instrument.
		
		This function accepts all parameters accepted when initializing
		a new Instrument. If supplied, the copy will have the properties
		as specified by the arguments passed to this function, rather
		than those of this Instrument.
		"""
		return Instrument(name if name is not None else self.name,
						  abbr if abbr is not None else self.abbr,
						  midi if midi is not None else self.midi,
						  clef if clef is not None else self.clef)
	
	def __hash__(self):
		return (self.name, self.abbr, self.midi, self.clef).__hash__()


instruments = {
	"Keyboard": {
		"Piano": Instrument("Piano", "Pno.", 1),
		"Electric Piano": Instrument("Electric Piano", "E. Pno.", 5),
		"Organ": Instrument("Organ", "Organ", 20)
	},
	"Pitched Percussion": {
		"Celesta": Instrument("Celesta", "Cel.", 9),
		"Glockenspiel": Instrument("Glockenspiel", "Glock.", 10),
		"Vibraphone": Instrument("Vibraphone", "Vib.", 12),
		"Marimba": Instrument("Marimba", "Mar.", 13),
		"Xylophone": Instrument("Xylophone", "Xyl.", 14),
		"Chimes": Instrument("Chimes", "Chimes", 15),
		"Timpani": Instrument("Timpani", "Timp.", 48, "D")
	},
	"Strings": {
		"Guitar": Instrument("Guitar", "Gtr.", 25),
		"Jazz Electric Guitar": Instrument("Electric Guitar", "E. Gtr.", 27),
		"Clean Electric Guitar": Instrument("Electric Guitar", "E. Gtr.", 28),
		"Bass": Instrument("Bass", "Bass", 33, "D"),
		"Electric Bass": Instrument("Electric Bass", "E. Bass", 34, "D"),
		"Violin": Instrument("Violin", "Vln.", 41),
		"Viola": Instrument("Viola", "Vla.", 42),
		"Violoncello": Instrument("Violoncello", "Vc.", 43, "D"),
		"Double Bass": Instrument("Double Bass", "D. B.", 44, "D"),
		"Pizzicato Strings": Instrument("Pizzicato Strings", "Pizz. Str.", 46),
		"Harp": Instrument("Harp", "Harp", 47),
	},
	"Brass": {
		"Trumpet": Instrument("Trumpet", "Tpt.", 57),
		"Trombone": Instrument("Trombone", "Tbn.", 58, "D"),
		"Tuba": Instrument("Tuba", "Tuba", 59, "D"),
		"French Horn": Instrument("French Horn", "Hrn.", 61),
	},
	"Woodwinds": {
		"Soprano Saxophone": Instrument("Soprano Saxophone", "S. Sax.", 65),
		"Alto Saxophone": Instrument("Alto Saxophone", "A. Sax.", 66),
		"Tenor Saxophone": Instrument("Tenor Saxophone", "T. Sax.", 67, "D"),
		"Baritone Saxophone": Instrument("Baritone Saxophone", "B. Sax.", 68, "D"),
		"Oboe": Instrument("Oboe", "Ob.", 69),
		"English Horn": Instrument("English Horn", "E. Hrn.", 70),
		"Bassoon": Instrument("Bassoon", "Bsn.", 71, "D"),
		"Clarinet": Instrument("Clarinet", "Cl.", 72),
		"Piccolo": Instrument("Piccolo", "Picc.", 73),
		"Flute": Instrument("Flute", "Fl.", 74)
	}
}


class Score:
	"""A musical score, a collection of parts performed by instruments.
	
	Attributes:
		parts: A list of the parts in this score.
		instruments: A list of the instruments in this score, where
			`instruments[i]` is the instrument playing `parts[i]`.
		dynamics: The volumes each part is performed at, as a list
			of integers representing the MIDI velocity values used
			for each part.
	"""
	def __init__(self, parts: Sequence[Part], instruments: Sequence[Part],
				 dynamics: Optional[List[int]]=None) -> None:
		"""Inits a score with the specified parts and instruments.
		
		Args:
			parts: A sequence of parts in this score. (Required)
			instruments: A sequence of instruments in this score, where
				the ith instrument plays the ith part. The `instruments`
				sequence must be as long as the `parts` sequence.
				(Required)
			dynamics: The volumes to play each part at, passed as a list
				of integers representing the MIDI velocity values to use
				for each part. If omitted or passed as None, reasonable
				defaults, featuring the first part, are used.
				(Default None)
		"""
		self.parts = list(parts)
		self.instruments = list(instruments)
		if dynamics is None:
			self.dynamics = [80, 70] + [62] * (len(parts)-3) + [75]
		else:
			self.dynamics = dynamics + [62] * (len(parts) - len(dynamics))
		self.dynamics = self.dynamics[:len(self.parts)]
	
	def write(self, title="Composition", chd_len: int=4,
			  composer: str="mathmusic.py", playable: bool=True,
			  debug_on: bool=False) -> str:
		"""Writes a MusicXML file representing this score.
		
		Args:
			title: The title of the composition. (Default "Composition")
			chd_len: The number of beats given to each chord change in
				this composition. (Default 4)
			composer: The composer of this score. (Default "mathmusic.py")
			playable: A boolean determining whether to modify parts to
				place them in the appropriate octaves for the instruments
				playing those lines. (Default True)
		"""
		env = Environment(loader=FileSystemLoader("mathmusic/ref"))
		if debug_on:
			print(env.list_templates())
			print(env.loader.searchpath)
		template = env.get_template('template.musicxml')
		parts = []  # parts list
		for i, part in enumerate(self.parts):
			parts.append([])  # measures in this part
			m = 0
			parts[-1].append([])  # a measure
			for note in part.get_notes():  # parameter: self.instruments if playable else None
				if m >= chd_len:
					parts[-1].append([])  # a new measure
					m %= chd_len
				if note[1] == ():
					parts[-1][-1].append(("R", note[0]))
				elif isinstance(note[1], (tuple, list, set)):
					parts[-1][-1].append(("C", note[0], note[1]))
				else:
					parts[-1][-1].append(("N", note[0], note[1]))
				m += note[0]
		if debug_on: print(parts)
		return template.render(foo='Hello World!', chd_len=chd_len,
			composer=composer, instruments=self.instruments, parts=parts,
			dynamics=self.dynamics)
	
	def add_part(self, part: Part,
				 instrument: Instrument=instruments["Keyboard"]["Piano"],
				 dynamics: int=75):
		"""Adds a part to the score.
		
		Args:
			part: The part to add to the score. (Required)
			instrument: The instrument to play the added part.
				(Default mathmusic.io.instruments['Keyboard']['Piano'])
			dynamics: The volume to play the part at, passed as an
				integer representing a MIDI velocity value. (Default 75)
		"""
		self.parts.append(part)
		self.instruments.append(instrument)
		self.dynamics.append(dynamics)
	
	def measures(self, chd_len: int=4):
		"""Iterates over the measures of this Score.
		
		Args:
			meter: The length of each measure to return. (Default 4)
		
		Yields:
			A tuple of the tuples returned by the Parts that compose
			this Score for each measure.
			See `mathmusic.music.Part.measures()`
		"""
		for m in zip(*[part.measures(chd_len) for part in self.parts]):
			yield m
