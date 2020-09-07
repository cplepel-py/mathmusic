"""mathmusic mathematical music composition package

This package provides a variety of functions for the mathematical and
algorithmic (and largely autonomous) composition of music. This package
is divided into three main modules, `music` (main functions), `io`
(input and output capabilities), and `defaults` (reasonable defaults
and static values used elsewhere in the package).

Modules:
	music: The main module, containing functions for generating
		   melody and chord progressions, and writing musical scores.
	io: A module with useful MusicXML file input/output functions.
	defaults: A module mainly for internal use that contains various
			  default an static values.
"""
from mathmusic import music
from mathmusic import util
from mathmusic import io
from mathmusic import defaults