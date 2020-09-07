"""mathmusic utility module.

This package contains defaults and utility functions, values, and
classes.
"""
from typing import TypeVar, Generic, Optional, Dict, Callable, Union
from collections import defaultdict
from random import choices, random


T = TypeVar("T")
K = TypeVar("V")


NOTE_LENS = {"w": 4, "H": 3, "h": 2, "Q": 1.5, "q": 1, "E": 0.75, "e": 0.5,
			 "s": 0.25, "t": (1/3), "T": (2/3), ' ': 1, ".": 0.5, "_": 2,
			 ",": 0.25, "-": 4, "G": 0.125, "g": 0,  # Below notes for reading
			 "1": 1.25, "2": 1.75, "3": 2.25, "4": 2.5, "5": 2.75, "6": 3.25,
			 "7": 3.5, "8": 3.75}
INV_NOTE_LENS = {ln: n for n, ln in NOTE_LENS.items() if n not in ",. _-"}
REST_LENS = {4: "-", 2: "_", 1: " ", 0.5: ".", 0.25: ","}


class Biases(Generic[T, K]):
	"""A multi-layered Markov/entropy probabilities table."""
	def __init__(self, biases: Optional[Dict[T, Dict[K, int]]]=None) -> None:
		"""Inits a Biases object with the specified biases.
		
		Args:
			biases: A dictionary mapping single-level conditions to sets
				of biases, dictionaries of results and their biases. If
				this field is omitted or passed as None, it defaults to
				an empty dictionary (no biases). (Default None)
		"""
		self.biases = [biases if biases else {}]
	
	def get(self, *cond: T, deg_rate: Callable[[int], float]=lambda n: 1) -> K:
		"""Selects a result from the biases with the passed conditions.
		
		Args:
			*cond: An arbitrary number of positional arguments, each an
				element of the conditions trace to use for determining
				the appropriate biases to use. (Required)
			deg_rate: A function or lambda, taking one argument, which
				represents the bias given to each layer of biases, so
				`deg_rate(n)` represents the bias given to the biases
				with n+1 elements of condition. (Default lambda n: 1)
		
		Returns:
			The randomly selected result.
		"""
		probs = {}
		hist = ()
		total = 0.0
		for i, e in enumerate(cond[::-1]):
			hist = (e,) + hist
			if i == 0 and e in self.biases[0]:
				sm = sum(self.biases[0][e].values())
				probs = defaultdict(lambda: 0, {k: p/sm for k, p in self.biases[0][e].items()})
				total = deg_rate(0)
			elif i >= len(self.biases):
				break
			elif hist in self.biases[i]:
				sm = sum(self.biases[i][hist].values())
				deg = deg_rate(i)
				for k in probs:
					probs[k] *= total / (total + deg)
				total += deg
				for k, b in self.biases:
					probs[k] += b * deg / total / sm
		keys = []
		bias = []
		for key, val in probs.items():
			keys.append(key)
			bias.append(val)
		return choices(keys, bias)[0]
	
	def add_bias(self, bias: K, weight: int, *cond: T):
		while len(cond) > len(self.biases):
			self.biases.append({})
		if len(cond) > 1:
			self.biases[len(cond)-1][tuple(cond)][bias] = weight
		else:
			self.biases[0][cond[0]][bias] = weight
	
	def get_bias(self, bias: K, *cond: T, default: Union[int, None]=0):
		cnd = tuple(cond) if len(cond) > 1 else cond[0]
		if cnd in self.biases[len(cond)-1] and bias in self.biases[len(cond)-1][cnd]:
			return self.biases[len(cond)-1][cnd][bias]
		else:
			return 0
	
	def get_conds(self, max_len: int=1):
		res = set()
		for i in range(max_len):
			res |= self.biases[i].keys()
		return res
	
	def get_biases(self, max_len: int=1):
		res = set()
		for i in range(max_len):
			for v in self.biases[i].values():
				res |= v.keys()
		return res
	
	def __add__(self, other: 'Biases'):
		for i, d in enumerate(other.biases):
			for c, bs in d.items():
				for b, w in bs.items():
					if i == 1:
						self.add_bias(b, w + self.get_bias(b, c), c)
					else:
						self.add_bias(b, w + self.get_bias(b, *c), *c)
