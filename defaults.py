"""mathmusic default values.

This module contains many of the default values used in the mathmusic
`music` package.

Attributes:
	PROGRESSION (list): A default value for the `prog` parameter of the
		chords() function in the composition module, which includes the
		basic rules of chord progression, and tries to avoid too much
		repetition of the same chord.
	RYTH (list): A default value for the `ryths` parameter of the
		melody() function in the composition module, which represents
		default biases for note addition at given amounts of remaining
		time in a chord/measure.
	NOTE_LENS (dict): A dictionary where each entry {k: n} notes that
		the rhythm abbreviation k represents a rhythm equivalent to n
		quarter notes (n beats in 4/4 time).
	BREAKS (dict): A dictionary of dictionaries, of the form
		{l: {s: b, ...}, ...} for use in adding passing and auxiliary
		notes. l is the rhythm of the note being broken into two shorter
		notes, s is a possible combination of shorter rhythms, the first
		being the original note the second being the added passing or
		auxiliary note, and b is the bias for s to be the substitution
		of l to accommodate the extra note.
	NUMS_TO_NAME (dict): A dictionary of the form {notes: name} which
		maps the chord defined by the pitches in the tuple, notes, of
		numeric scale degrees to the string, name, that represents the
		defined chord.
	INV_NOTE_LENS (dict): A dictionary mapping a number representing the
		length, in quarter note beats, of a note to the string
		representation of that note.
	DEF_CHORD_NAMES (list): A list of the names of the chords used in
		this package by default.
	BASE_OCT (int): The base octave to use for numerical scale pitches.
		Since BASE_OCT is 5, numerical scale pitch 1 represents C5.
	SCALES (dict): A dictionary of dictionaries of the form
		{name: {pitch: m21name, ...}, ...} where name is the name of a
		scale (for example, "C"), pitch is a numeric scale degree
		representing a pitch in the scale, and m21name is the string
		accepted by music21 as the name of the represented pitch.
	CHD_LIST (list): A list of tuples of numeric scale degrees
		representing the chords used by default in the mathmusic
		package.
	STRONGS (list): A list where STRONGS[i] is the set of beats usually
		considered "strong" in a measure with i beats.
"""
from mathmusic.util import Biases
from mathmusic.io import instruments, Instrument
from mathmusic.music import Chord

Vn1 = instruments["Strings"]["Violin"].copy("Violin 1", "Vn. 1")
Vn2 = instruments["Strings"]["Violin"].copy("Violin 2", "Vn. 2")
Va = instruments["Strings"]["Viola"]
Vc = instruments["Strings"]["Violoncello"]
DB = instruments["Strings"]["Double Bass"]

Fl = instruments["Woodwinds"]["Flute"]
Cl = instruments["Woodwinds"]["Clarinet"]
Hn = instruments["Brass"]["French Horn"]
Tpt = instruments["Brass"]["Trumpet"]
Tbn = instruments["Brass"]["Trombone"]
Ob = instruments["Woodwinds"]["Oboe"]
EHn = instruments["Woodwinds"]["English Horn"]
Bsn = instruments["Woodwinds"]["Bassoon"]
Tmp = instruments["Pitched Percussion"]["Timpani"]
Pno = instruments["Keyboard"]["Piano"]
Xyl = instruments["Pitched Percussion"]["Xylophone"]

Gtr = instruments["Strings"]["Guitar"]
EGtr = instruments["Strings"]["Clean Electric Guitar"]
Bass = instruments["Strings"]["Bass"]
EBass = instruments["Strings"]["Electric Bass"]


# If a number is not found, check 0.5, then progress towards 0 (integer values)
instrument_biases = {"strings": Biases({
		-1: {Vn1: 9, Vc: 2, Va: 1},  # Melody
		0: {Vn2: 3, Va: 1},  # Soprano
		1: {Va: 3, Vn2: 1},  # Alto
		2: {Vc: 3, Va: 1},  # Tenor
		3: {DB: 2, Vc: 1},  # Bass
		-2: {Vn1: 1, Vc: 1, Va: 1},  # Counter melody
		-3: {Vc: 12, Va: 3},  # Walking
		0.5: {Vn1: 12, Va: 6, Vc: 9}  # Default
		}),
	"orchestra": Biases({
		-1: {Vn1: 13, Va: 1, Vc: 2, Fl: 5, Cl: 5, Hn: 5, Ob: 4, Tpt: 1, Tbn: 2, EHn: 3, Pno: 2, Xyl: 1},
		0: {Vn2: 12, Va: 2, Fl: 2, Cl: 1, Hn: 3, Tpt: 2, EHn: 4},
		1: {Vn2: 4, Va: 12, Cl: 4, Hn: 2, Tpt: 1, Ob: 1, EHn: 9, Bsn: 2},
		2: {Va: 4, Vc: 12, Cl: 2, Hn: 1, Ob: 6, EHn: 2, Bsn: 9},
		3: {Vc: 6, DB: 12, Ob: 4, Bsn: 3, Tmp: 9},
		-2: {Vn1: 12, Vc: 12, Va: 12, Fl: 9, Cl: 8, Hn: 9, Ob: 9, Tbn: 6, EHn: 4},
		-3: {Vc: 12, Va: 3, Ob: 9, Tbn: 2, EHn: 3, Bsn: 8},
		0.5: {Vn1: 12, Va: 2, Ob: 7, Vc: 3, Fl: 3, Cl: 3, Hn: 3, Tpt: 1, Tbn: 2, EHn: 3, Pno: 4}
		}),
	"pop": Biases({
		-1: {EGtr: 12, Gtr: 1, Vn1: 7, Tpt: 4, Pno: 15, Fl: 3, Cl: 2},
		0: {EGtr: 12, Gtr: 2, Vn1: 9, Tpt: 6, Pno: 12, Fl: 5, Cl: 1},
		1: {EGtr: 3, Gtr: 1, Vn1: 4, Va: 2, Tpt: 2, Pno: 12, Cl: 6},
		2: {EGtr: 1, Gtr: 1, Va: 2, Tpt: 1, Pno: 12, Tbn: 8, Cl: 2},
		3: {Bass: 3, EBass: 12, Vc: 1, Tbn: 1, Pno: 12},
		-3: {Bass: 3, EBass: 5, Tbn: 2, Pno: 2, Va: 4},
		0.5: {Vn1: 2, Cl: 5, Pno: 2, EGtr: 1}
		})
	}

major_key_chords = {"I": Chord((1, 3, 5)), "ii": Chord((2, 4, 6)),
	"iii": Chord((3, 5, 7)), "IV": Chord((4, 6, 8)), "V": Chord((5, 7, 9)),
	"vi": Chord((6, 8, 10)), "vii*": Chord((0, 2, 4))}
