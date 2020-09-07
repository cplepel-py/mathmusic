"""mathmusic composition module.

This is the main module of the mathmusic music composition package,
which defines functions used for algorithmically composing music from
specified (mainly statistical) parameters.
"""
from typing import List, Dict, Tuple, Sequence, Optional, Collection, Callable, Mapping, Union, Generator
from math import log, exp
from random import choices, random

from mathmusic.util import Biases, NOTE_LENS, INV_NOTE_LENS, REST_LENS


def get_pass_func(ratio: float=0.8, rigidity: float=2):
	"""Returns a function for the pass_func parameter of refine().
	
	Returns a lambda expression, (s, l) -> p, which returns the
	probability, p, of adding a passing note to bride a leap between
	two notes encountered by the refine() function, given s steps and
	l leaps preceding the leap being considered.
	
	Args:
		ratio: The target ratio of steps / (steps + leaps) for the
			melody. Melodies refined with the generated lambda
			expression will converge to the specified ratio. The
			returned expression is static (essentially a constant value)
			when ratio is 0.5.
			(Default 0.8)
		rigidity: The rate at which the generated lambda expression
			returns to the specified ratio of steps and leaps. The
			returned expression is static (essentially a constant value)
			when rigidity is 1.
			(Default 2)
	
	Raises:
		ZeroDivisionError: ratio parameter was not in range (0, 1).
	"""
	# function is static when bx+a is horizontal
	#   when b is 0
	#   when ln(ratio/(1-ratio))-a is 0
	#   when ln(ratio/(1-ratio)) = a
	#   when ln(ratio/(1-ratio)) = rigidity * lg
	#   when ln(ratio/(1-ratio)) = rigidity * ln(ratio/(1-ratio))
	#   when rigidity = 1 or ln(ratio/(1-ratio)) = 0
	#   when rigidity = 1 or ratio/(1-ratio) = 1
	#   when rigidity = 1 or ratio = 1 - ratio
	#   when rigidity = 1 or ratio = 0.5
	if ratio == 1: return lambda s, l: 1
	lg = log(ratio / (1-ratio))
	m = -ratio/(ratio-1)
	a = rigidity * lg
	def pass_func(s: int, l: int):
		if l == 0: l = 0.0001
		b = (lg - a) / (m*l)
		if b*s+a > 709:
			return 0.999999999999
		return exp(b*s+a) / (1 + exp(b*s+a))
	return pass_func


def duration(rhythm: str):
	"""Returns the duration of a rhythm passed as a string.
	
	Args:
		rhythm: The rhythm string to calculate the duration of.
			(Required)
	
	Returns:
		The duration, in quarter note beats, of the rhythm represented
		by the passed string.
	"""
	dur = 0
	for r in rhythm:
		dur += NOTE_LENS[r]
	return dur


def count_notes(rhythm: str):
	"""Counts the number of played notes in a rhythm.
	
	Args:
		rhythm: The rhythm string to count the played notes in.
			(Required)
	
	Returns:
		The number of played (non-rest) notes in the passed rhythm.
	"""
	return sum(0 if r in "_- ,." else 1 for r in rhythm)


def fill_rests(beats: int,
			   rests: Dict[int, str]=REST_LENS):
	"""Returns a rhythm string of rests lasting a specified duration.
	
	Args:
		beats: The number of beats to fill with silence. (Required)
		rests: A dictionary mapping lengths (in beats) of rests to the
			representation of those rests.
			(Default mathmusic.util.REST_LENS)
	"""
	res = ""
	time = 0
	keys = sorted(rests.keys(), reverse=True)
	while time + keys[0] <= beats:
		res += rests[keys[0]]
		time += keys[0]
	for key in keys[1:]:
		if time + key <= beats:
			res += rests[key]
			time += key
	return res


def clip_pitch(pitch: int, min_pitch: int=1, max_pitch: int=11):
	if pitch < min_pitch:
		return pitch + 7 * ceil((min_pitch-pitch)/7)
	if pitch > max_pitch:
		return pitch - 7 * ceil((pitch-max_pitch)/7)
	else:
		return pitch


class Chord:
	"""A chord, or group of pitches."""
	
	def __init__(self, pitches: Collection[int]=(1,3,5)) -> None:
		"""Inits a Chord with the provided pitches.
		
		Args:
			pitches: A collection of pitches, in any order. The pitches
				will be sorted in the Chord, so the bass pitch is always
				the lowest pitch in the Chord. (Default (1, 3, 5))
		"""
		pitches = set(pitches)
		root = min(pitches)
		self.pitches = sorted(pitches, key=lambda x: (x-root)%7)
		self.pitches = [(p-root)%7+root for p in self.pitches]
	
	def get_pitches(self, min_pitch: int=-16, max_pitch: int=-6,
					repeat_mode: int=1) -> Tuple[int]:
		"""Returns a tuple of pitches in the chord in a given range.
		
		The returned tuple contains pitches in the chord in the given
		range, with the lowest chord in the tuple being the bass tone
		of the chord.
		
		By default, the returned tuple only contains each pitch in the
		chord in one octave (except for the root pitch), but this
		behavior can be altered by setting the `repeat_mode` parameter
		to `True`.
		
		To return a simple triad from a major chord, the `repeat_mode`
		parameter can be set to 0, to return a triad with the bass tone
		repeated in a higher octave, set `repeat_mode` to 1 or omit it.
		Setting the `repeat_mode` to 6 will return as many pitches in
		chord in the given range as possible. Other values of the
		`repeat_mode` parameter have other effects, as described in the
		description of the `repeat_mode` parameter.
		
		Args:
			min_pitch: The lowest pitch to include, passed as a numeric
				scale degree. (Default -16)
			max_pitch: The highest pitch to include, passed as a numeric
				scale degree. (Default -6)
			repeat_mode: A three-bit integer (if the bit length of the
				passed value is greater than three, only the three least
				significant bits are used), determining whether to use
				pitches of the chord in multiple octaves. If the least
				significant bit is set, the bass pitch is repeated as
				the highest pitch in the set of returned pitches. If
				second least most significant bit is set, the other
				pitches are also repeated in higher octaves. If the
				third least significant bit is set, pitches above the
				bass pitch may be repeated in octaves below the lowest
				returned bass note. No repeated pitch will be included
				if it is higher than the value passed as the `max_pitch`
				argument or lower than the value passed as the
				`min_pitch` argument. (Default 1)
		"""
		bass = ((((self.pitches[0]-1)%7)-((min_pitch-1)%7))%7) + min_pitch
		mod = bass - self.pitches[0]
		res = [bass]
		i = 0
		if not repeat_mode&3:
			max_pitch = min(max_pitch, self.pitches[-1] + mod)
		elif repeat_mode&3 == 1:
			max_pitch = min(max_pitch,
				((self.pitches[0]-self.pitches[-1])%7)+self.pitches[-1]+mod)
		while res[-1] < max_pitch:
			i += 1
			if not repeat_mode & 3 and i == len(self.pitches):
				break
			elif not repeat_mode & 2 and i > len(self.pitches):
				break
			if i % len(self.pitches) == 0:
				mod = ((((((self.pitches[0]-1)%7)-((res[-1]-1)%7))%7) + res[-1])
					   - self.pitches[0])
			res.append(self.pitches[i % len(self.pitches)] + mod)
		if res[-1] > max_pitch:
			res = res[:-1]
		while (repeat_mode & 3 == 3 and res[-1]%7 != self.pitches[0]%7
			   and len(res) > len(self.pitches)):
			res.pop()
		i = -1
		while repeat_mode & 4 and res[0] > min_pitch:
			res.insert(0, self.pitches[i] + bass - self.pitches[0] - 7)
			i -= 1
			i %= len(self.pitches)
		if res[0] < min_pitch:
			res.pop(0)
		return res
	
	def scale_intervals(self):
		"""Returns the numeric scale degree intervals of this chord.
		
		Returns:
			A list, `[p - root for p in self.pitches]`, where `root` is
			the lowest pitch of this chord.
		"""
		root = self.pitches[0]
		return [p - root for p in self.pitches]
	
	def nearest(self, pitch: int):
		"""Returns the pitch of this chord nearest to a given pitch.
		
		Args:
			pitch: An integer representing the pitch to find the nearest
				pitch to, as a numeric scale degree. (Required)
		
		Returns:
			The pitch of this chord nearest to the pitch passed, as a
			numeric scale degree.
		"""
		mod_out = (pitch - self.pitches[0]) % 7
		mod_in = min(self.scale_intervals(), key=lambda x: min(abs(x-mod_out), 7-abs(x-mod_out)))
		mod = mod_in - mod_out
		if abs(mod) > 3.5:
			mod += 7
		return pitch + mod
	
	def _next_pitch(self, previous: int, change: int=0):
		"""A utility for generating skeleton melodies."""
		previous = self.nearest(previous)
		deltas = self.scale_intervals()
		prev = (previous - self.pitches[0])%7
		prev_ix = deltas.index(prev)
		octs = ((prev_ix+change)//len(deltas))
		return deltas[(prev_ix+change)%len(deltas)]+previous-prev+7*octs
	
	def __eq__(self, other):
		"""Two chords in any octaves with the same pitches are equal."""
		if len(self.pitches) != len(other.pitches):
			return False
		elif self.pitches[0] % 7 != other.pitches[0] % 7:
			return False
		elif all(self.pitches[i] - self.pitches[0] ==
				 other.pitches[i] - other.pitches[0]
				 for i in range(1, len(self.pitches))):
			return True
		return False
	
	def __hash__(self):
		mod = self.pitches[0] % 7 - self.pitches[0]
		return tuple(p + mod for p in self.pitches).__hash__()
	
	def __repr__(self):
		return f"Chord({self.pitches})"


PROGRESSION = Biases({
	Chord((1, 3, 5)): {Chord((1, 3, 5)): 1, Chord((2, 4, 6)): 1,
		Chord((3, 5, 7)): 1, Chord((4, 6, 8)): 1, Chord((5, 7, 9)): 1,
		Chord((6, 8, 10)): 1, Chord((7, 9, 11)): 1},
	Chord((2, 4, 6)): {Chord((5, 7, 9)): 1, Chord((7, 9, 11)): 1},
	Chord((3, 5, 7)): {Chord((6, 8, 10)): 1},
	Chord((4, 6, 8)): {Chord((7, 9, 11)): 1, Chord((5, 7, 9)): 1},
	Chord((5, 7, 9)): {Chord((1, 3, 5)): 1},
	Chord((6, 8, 10)): {Chord((2, 4, 6)): 1, Chord((4, 6, 8)): 1},
	Chord((7, 9, 11)): {Chord((1, 3, 5)): 1}})  # type: Biases[Chord, Chord]


RYTH = Biases({1: {"q": 4, " ": 0.25}, 2: {'q': 27, 'h': 9, ' ': 0.25},
	3: {"q": 12, 'h': 4, 'H': 6, ' ': 0.25},
	4: {"q": 12, "h": 6, "H": 2, "w": 1, " ": 0.25}})  # type: Biases[int, str]


BREAKS = Biases({"w": {"hh": 1, "Hq": 1}, "H": {"hq": 1}, "h": {"qq": 4, "Qe": 1},
	"Q": {"qe": 1}, "q": {"ee": 9, "Es": 1}, "E": {"es": 1},
	"e": {"ss": 1}, "s": {"GG": 1}, "G": {"Gg": 1}, "g": {"gg": 1}})  # type: Biases[str, str]


INTERVALS = Biases({0: {0: 1, 1: 1, -1: 1}, 1: {0: 3, 1: 3, -1: 4},
	-1: {0: 3, 1: 4, -1: 3}})  # type: Biases[int, int]


CHD_LEN = Biases({0: {4: 1}, 1: {4: 1}, 2: {4: 1}, 3: {4: 1}, 4: {4: 1}})


class Part:
	"""A part in a musical score.
	
	Attributes:
		notes: A list of numeric scale degrees, representing the pitches
			of the notes in the part.
		rhythms: A string representing the rhythm of the notes and rests
			in the part.
	"""
	def __init__(self, notes: List[int]=None, rhythms: str=None,
				 chd_lens: List[int]=None) -> None:
		"""Inits a Part object with the specified notes and rhythms.
		
		Args:
			notes: A list of numeric scale degrees, representing the
				pitches of the notes in this part. Passing None will
				initialize notes to an empty list. (Default None)
			rhythms: A string representing the rhythm of the notes and
				rests in the part. Passing None will initialize rhythms
				to an empty string. (Default None)
			instrument: An `Instrument` enum representing the instrument
				playing this part.
		"""
		self.notes = notes if notes else []
		self.rhythms = rhythms if rhythms else ""
		self.chd_lens = chd_lens if chd_lens else [4 for _ in range(0, round(duration(self.rhythms)), 4)]
		if notes:
			self.min_note, self.max_note = min(self.notes), max(self.notes)
		else:
			self.min_note, self.max_note = 0, 0
	
	def refine(self,
			   pass_func: Callable=get_pass_func(ratio=0.8, rigidity=2),
			   aux_func: Callable=lambda n: 1 / (6-n),
			   end_tonic: bool=True,
			   breaks: Biases[str, str]=BREAKS,
			   debug_on: bool=False) -> 'Part':
		"""Refines this melody with passing and auxiliary notes.
		
		Args:
			pass_func: A function or lambda expression, taking two
				arguments. `pass_func(s, l)` is the probability of
				adding a passing note between two nonadjacent
				consecutive notes given s steps and l leaps preceding
				the leap being considered for a passing note.
				(Default get_pass_func(ratio=0.8, rigidity=2))
			aux_func: A function or lambda expression, taking one
				argument. `aux_func(n)` is the probability of adding an
				auxiliary note between the nth and (n+1)th note of the
				same pitch. (Default lambda n: 1 / (6-n))
			end_tonic: A boolean determining whether to force the
				refined melody to end on the tonic note
				(pitch 1, 8, etc.). (Default True)
			breaks: A single-level Biases object of rhythms to pairs
				of shorter rhythms of the same total duration for use
				in adding passing and auxiliary notes. The condition is
				the rhythm of the note being broken into two shorter
				notes, and the result is a possible combination of
				shorter rhythms, the first being the original note the
				second being the added passing or auxiliary note.
				(Default BREAKS)
			debug_on: A boolean determining whether to print debug
				information. If set to True, debug information will be
				printed using the print() function. (Default False)
		
		Returns:
			A new Part object, the refined part.
		"""
		# Result Variable
		ref = Part(self.notes, self.rhythms)
		# Initialize counters
		reps = 0
		steps = 0
		leaps = 0
		note_num = 0
		i = 0
		while i < len(ref.rhythms):  # each note, including added notes
			r = ref.rhythms[i]
			if note_num+1 >= len(ref.notes):  # if this is the last non-rest
				if debug_on: print(f"END: no more notes")
				break
			elif r in " _-.,":  # if this is a rest
				i += 1
				continue
			else:  # If this is a note
				n = ref.notes[note_num]
				if debug_on: print(f"notes: {note_num}, {note_num+1};  {ref.notes[note_num:note_num+2]}")
				if debug_on: print(f"rhythm: {r}")
				note_num += 1
			if n == ref.notes[note_num]:  # repeated note
				threshold = aux_func(reps)
				if random() < threshold:
					if debug_on: print("aux ({threshold})")
					aux = n + 1 if random() > 0.5 else n - 1
					ref.notes.insert(note_num, aux)
					ref.rhythms = (ref.rhythms[:i] + breaks.get(r) +  # TODO: Change deg_rate?
								   ref.rhythms[i+1:])
					reps = 1
				else:
					if debug_on: print(f"no aux ({threshold})")
					reps += 1
			elif abs(n - ref.notes[note_num]) > 1:  # leap
				threshold = pass_func(steps, leaps)
				if random() < threshold:
					if debug_on: print(f"passing ({threshold})")
					ref.rhythms = (ref.rhythms[:i] + breaks.get(r) +
								   ref.rhythms[i+1:])
					if n > ref.notes[note_num]:
						ref.notes.insert(note_num, n-1)
					else:
						ref.notes.insert(note_num, n+1)
					steps += 1
				else:
					if debug_on: print(f"no pass ({threshold})")
					leaps += 1
				reps = 0
			elif abs(n - ref.notes[note_num]) <= 1:
				if debug_on: print("step")
				steps += 1
				reps = 0
			if debug_on: print(f"notes: {ref.notes}, ryth: {ref.rhythms}")
			i += 1
		if end_tonic and (ref.notes[-1]-1) % 7 != 0:
			# last note must be changed to tonic
			last = (ref.notes[-1]-1)%7
			if last < 4:  # 0123 4567 = CDEF GABC
				nearest = ref.notes[-1] - last
			else:
				nearest = ref.notes[-1] - last + 7
			if ref.rhythms[-1] in " ,.-_":
				ref.rhythms = (ref.rhythms[:-1] +
							   "qsewh"[" ,.-_".index(ref.rhythms[-1])])
			else:
				ref.rhythms = ref.rhythms[:-1] + breaks.get(ref.rhythms[-1])
			ref.notes.append(nearest)
		return ref
	
	def extend(self, part: 'Part') -> None:
		"""Extends this part with another part.
		
		Adds the notes and rhythms of another part to the end of this
		part.
		
		Args:
			part: The part to extend this part with. (Required)
		"""
		self.notes.extend(part.notes)
		self.rhythms += part.rhythms
		self.min_note = min(self.min_note, part.min_note)
		self.max_note = min(self.max_note, part.max_note)
	
	def get_notes(self) -> Generator[Tuple[str, Union[Tuple[int], int]], None, None]:
		"""Iterates through the notes of this part.
		
		Yields:
			A tuple, (l, p), for each rhythm in this part, where l is
			the duration, in quarter note beats, of the rhythm, and p is
			the pitch or tuple of pitches of the corresponding note. If
			the rhythm is a rest, p is an empty tuple.
		"""
		n = 0
		for r in self.rhythms:
			if r in "-_ ,.":
				yield (NOTE_LENS[r], ())
			else:
				yield (NOTE_LENS[r], self.notes[n])
				n += 1
	
	def copy(self) -> 'Part':
		"""Returns a shallow copy of this Part."""
		return Part(self.notes, self.rhythms)
	
	def transpose(self, interval: int=0) -> None:
		self.notes = [n+interval for n in self.notes]
	
	def clip(self, min_pitch: int=-1, max_pitch: int=11):
		assert max_pitch >= min_pitch+7
		self.notes = [clip_pitch(p, min_pitch, max_pitch) for p in self.notes]
	
	def measures(self, meter: int=4):
		"""Iterates over the measures of this Part.
		
		Args:
			meter: The length of each measure to return. (Default 4)
		
		Yields:
			A tuple, `(notes, ryth)`, for each measure in this part,
			where `notes` is a list of the notes in the measure and
			`ryth` is a string representing the rhythms of the notes
			and rests in the measure.
		"""
		m_notes = []
		m_ryth = ""
		ni = 0
		for r in self.rhythms:
			if r not in "-_ ,.":
				m_notes.append(self.notes[ni])
				ni += 1
			m_ryth += r
			if duration(m_ryth) >= meter:
				yield m_notes, m_ryth
				m_notes = []
				m_ryth = ""


class Progression:
	"""A chord progression, or series of chords under a melody.
	
	Attributes:
		chords: The list of chords in the progression.
	"""
	def __init__(self, chords: Sequence[Chord]) -> None:
		"""Inits a Progression object with the specified chord sequence.
		
		Args:
			chords: A sequence of Chord objects to use as the chords in
				the progression. (Required)
		"""
		self.chords = list(chords)
	
	def chord_background(self, rhythm: Union[str, Sequence[str]]="w",
						 min_pitch: int=-16,
						 max_pitch: int=-6,
						 repeat_mode: int=1) -> Part:
		"""Creates a part playing a full chord progression.
		
		Generates a Part object representing an instrument playing this
		chord progression in full, including all notes of each chord.
		
		Args:
			rhythm: A string representing the rhythm to play the chords
				in for each measure, or a sequence of strings
				representing a pattern of rhythms to play the chords in
				(each being one measure). Any and all rhythms passed
				must be equal in length to the length of each chord in
				the chord progression being played. (Default "w")
			min_pitch: The minimum pitch (of the bass note) for the
				chords, passed as a numeric scale degree. (Default -16)
			max_pitch: The maximum pitch (of the highest note) for the
				chords, passed as a numeric scale degree. (Default -6)
			repeat_mode: A three-bit integer (if the bit length of the
				passed value is greater than three, only the three least
				significant bits are used), determining whether to use
				pitches of the chord in multiple octaves. If the least
				significant bit is set, the bass pitch is repeated as
				the highest pitch in the set of returned pitches. If
				second least most significant bit is set, the other
				pitches are also repeated in higher octaves. If the
				third least significant bit is set, pitches above the
				bass pitch may be repeated in octaves below the lowest
				returned bass note. No repeated pitch will be included
				if it is higher than the value passed as the `max_pitch`
				argument or lower than the value passed as the
				`min_pitch` argument. See `Chord.get_pitches`
				(Default 1)
		"""
		ryths = (rhythm,) if type(rhythm) is str else rhythm
		part = Part()
		reps = []
		i = 0
		for chd in self.chords:
			if i >= len(reps):
				reps.append(count_notes(ryths[i]))
			part.rhythms += ryths[i]
			part.notes.extend([chd.get_pitches(min_pitch, max_pitch, repeat_mode)] * reps[i])
			i += 1
			i %= len(ryths)
		return part
	
	def get_voice(self, voice: int=0, rhythm: Union[str, Sequence[str]]="w",
				  min_pitch: int=-16, max_pitch: int=-6,
				  repeat_mode: int=1) -> Part:
		"""Creates a part playing a voice of the chord progression.
		
		Generates a Part object representing an instrument playing one
		voice in this chord progression, including only one note of each
		chord.
		
		Args:
			rhythm: A string representing the rhythm to play the chords
				in for each measure, or a sequence of strings
				representing a pattern of rhythms to play the chords in
				(each being one measure). Any and all rhythms passed
				must be equal in length to the length of each chord in
				the chord progression being played. (Default "w")
			min_pitch: The minimum pitch (of the bass note) for the
				chords, passed as a numeric scale degree. (Default -16)
			max_pitch: The maximum pitch (of the highest note) for the
				chords, passed as a numeric scale degree. (Default -6)
			repeat_mode: A three-bit integer (if the bit length of the
				passed value is greater than three, only the three least
				significant bits are used), determining whether to use
				pitches of the chord in multiple octaves. If the least
				significant bit is set, the bass pitch is repeated as
				the highest pitch in the set of returned pitches. If
				second least most significant bit is set, the other
				pitches are also repeated in higher octaves. If the
				third least significant bit is set, pitches above the
				bass pitch may be repeated in octaves below the lowest
				returned bass note. No repeated pitch will be included
				if it is higher than the value passed as the `max_pitch`
				argument or lower than the value passed as the
				`min_pitch` argument. See `Chord.get_pitches`
				(Default 1)
		"""
		ryths = (rhythm,) if isinstance(rhythm, str) else rhythm
		tacet = fill_rests(duration(ryths[0]))
		part = Part()
		reps = []
		i = 0
		for chd in self.chords:
			if i >= len(reps):
				reps.append(count_notes(ryths[i]))
			pitches = chd.get_pitches(min_pitch, max_pitch, repeat_mode)
			if voice < len(pitches):
				part.rhythms += ryths[i]
				part.notes.extend([pitches[voice]] * reps[i])
			else:
				part.rhythms += tacet
			i += 1
			i %= len(ryths)
		return part
	
	def old_skeleton(self, chd_len: int=4, ryths: Biases[int, str]=RYTH,
				 min_pitch: int=1, max_pitch: int=11,
				 debug_on: bool=False) -> Part:
		"""Creates a skeleton melody on top of this chord progression.
		
		This function does not add any passing or auxiliary notes; use
		the `refine()` method of the generated Part to add passing and
		auxiliary notes to a skeleton melody.
		
		Args:
			chd_len: The number of beats (in 4/4 time) given to each
				chord. (Default 4)
			ryths: A single-level Biases object of quarter note beats
				remaining in the measure to rhythms to insert in the
				measure with the specified number of quarter not beats
				remaining. (Default RYTH)
			min_pitch: The minimum pitch, represented as a numeric scale
				degree, to include in the skeleton melody. (Default 1)
			max_pitch: The maximum pitch, represented as a numeric scale
				degree, to include in the skeleton melody. (Default 11)
			debug_on: A boolean determining whether to print debug
				information. If set to True, debug information will be
				printed using the `print()` function. (Default False)
		
		Returns:
			A new `Part` object representing the generated skeleton
			melody.
		"""
		notes = []
		ryth = ""
		pre = 1
		for chd in self.chords:
			harm = chd.get_pitches(min_pitch, max_pitch, 6)
			if debug_on: print(f"harm: {harm}")
			rem = chd_len
			if debug_on: print(f"rem: {rem}")
			temp_notes = []
			while rem:
				if not temp_notes and pre in harm:
					note = harm.index(pre)
					if debug_on: print("same")
				elif not temp_notes:
					note = min(harm, key=lambda n: abs(pre - n))
					note = harm.index(note)
					if debug_on: print("nearest")
				else:
					if pre == 0:
						note = choices([0, 1], [1, 2])[0]
					elif pre == len(harm)-1:
						note = choices([pre-1, len(harm)-1], [2, 1])[0]
					else:
						note = choices([pre-1, pre, pre+1])[0]
					if debug_on: print("range")
				if debug_on: print(f"note: {note}")
				ryth += ryths.get(rem)  # TODO: Change deg_rate arg?
				if ryth[-1] not in ",. _-":
					temp_notes.append(note)
					pre = note
				if debug_on: print(f"ryth: {ryth[-1]}")
				rem -= NOTE_LENS[ryth[-1]]
				if debug_on: print(f"rem: {rem}")
				if debug_on: print(f"pre: {pre}")
			if debug_on: print(f"harm: {harm}")
			if debug_on: print(f"temp: {temp_notes}")
			pre = harm[pre]
			for n in temp_notes:
				notes.append(harm[n])
			if debug_on: print(f"notes: {notes}")
			if debug_on: print(f"ryth: {ryth}")
		if debug_on: print(f"Skeleton: {notes, ryth}")
		return Part(notes, ryth)
	
	def skeleton(self, meter: int=4, chd_len: Biases[int, int]=CHD_LEN,
				 ryths: Biases[int, str]=RYTH, min_pitch: int=1,
				 max_pitch: int=11, interval: Biases[int, int]=INTERVALS,
				 debug_on: bool=False) -> Part:
		"""Creates a skeleton melody on top of this chord progression.
		
		This function does not add any passing or auxiliary notes; use
		the `refine()` method of the generated Part to add passing and
		auxiliary notes to a skeleton melody.
		
		Args:
			meter: The number of beats in each measure. (Default 4)
			chd_len: A Biases object that determines the length of a
				chord, given the beat of the measure it starts on.
				(Default CHD_LEN)
			ryths: A single-level Biases object of quarter note beats
				remaining in the measure to rhythms to insert in the
				measure with the specified number of quarter not beats
				remaining. (Default RYTH)
			min_pitch: The minimum pitch, represented as a numeric scale
				degree, to include in the skeleton melody. (Default 1)
			max_pitch: The maximum pitch, represented as a numeric scale
				degree, to include in the skeleton melody. (Default 11)
			interval: A Biases object, defining the probability of a
				given interval between notes in the skeleton melody,
				given past intervals. (Default INTERVALS)
			debug_on: A boolean determining whether to print debug
				information. If set to True, debug information will be
				printed using the `print()` function. (Default False)
		
		Returns:
			A new `Part` object representing the generated skeleton
			melody.
		"""
		notes = []
		ryth = ""
		pre = min_pitch+(7-((min_pitch-1)%7))%7
		intervals = [0]
		chd_lens = []
		for chd in self.chords:
			rem = chd_len.get(duration(ryth)%meter)
			chd_lens.append(rem)
			while rem:
				ryth += ryths.get(rem)  # TODO: Change deg_rate arg?
				if ryth[-1] not in ",. _-":
					next_interval = interval.get(*intervals)
					note = chd._next_pitch(pre, next_interval)
					if note > max_pitch:
						note = chd._next_pitch(pre, -+next_interval)
					elif note < min_pitch:
						note = chd._next_pitch(pre, +next_interval)
					notes.append(note)
					pre = note
				rem -= NOTE_LENS[ryth[-1]]
		return Part(notes, ryth, chd_lens=chd_lens)
	
	def from_biases(biases: Biases[Chord, Chord]=PROGRESSION,
					first: List[Chord]=[Chord((1, 3, 5))], min_len: int=4,
					force_end: List[Chord]=[Chord((5, 7, 9)), Chord((1, 3, 5))],
					deg_rate: Callable[[int], float]=lambda n: 1) -> 'Progression':
		"""Creates a chord progression.
		
		Args:
			biases: A Biases object of chord progression rules, where
				the condition trace is the list of previous chords and
				the result is the next chord in the progression.
				(Default PROGRESSION)
			first: A list containing the the starting chords of the
				progression. This list must contain at least one entry.
				(Default [Chord((1, 3, 5))])
			min_len: The minimum number of chords in the progression.
				(Default 4)
			force_end: The last chords of the chord progression. The chord
				progression will not end until this sequence occurs to end
				the progression.
				(Default [Chord((5, 7, 9)), Chord((1, 3, 5))])
			deg_rate: A function or lambda, taking one argument, which
				represents the bias given to each layer of chord
				progression rules. See the `deg_rate` parameter of the
				`Biases.get` method. (Default lambda n: 1)
		
		Returns:
			The `Progression` object created from the parameters and rules.
		
		Raises:
			KeyError: An incomplete rule set was passed for `prog`.
		"""
		end_len = len(force_end)
		res = first[:]
		while True:
			res.append(biases.get(*res, deg_rate=deg_rate))
			if res[-end_len:] == force_end and len(res) >= min_len:
				break
		return Progression(res)
	
	def __len__(self):
		return len(self.chords)
