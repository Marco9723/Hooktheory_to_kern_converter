import json
import sys
import os
from fractions import Fraction # for exact ractionals
from typing import List, Dict,Tuple, Optional, Any, Set

# costants and lookup tables (with dictionaries): code-independent data structures
# key with tuples because immutable, no lists because are mutable

# semitones between tonic and 3rd AND 3rd and 5th
# dict (diverso da Dict) as data structure, tuples as key
INTERVALS_TO_CHORD_QUALITY = {
    (4,3): 'maj', # Ex: C E G (4 semitones between C and E, 3 semitones between E and G)
    (3,4): 'min',
    (3,3): 'dim',
    (4,4): 'aug',
    (2,5): 'sus2',
    (5,2): 'sus4',
    (4, 3, 3): 'dom7',    
    (4, 3, 4): 'maj7',    
    (3, 4, 3):  'min7',   
    (3, 3, 4):  'hdim7',   
    (3, 3, 3):  'dim7',   
    (4, 4, 2):  'augmaj7', 
    (2, 5, 3):  'sus4m7',
    (4, 3, 3, 4): 'dom9',
    (4, 3, 4, 3): 'maj9',
    (3, 4, 3, 3): 'min9',
    # other chords ?
}

# another dict for conversion to mxhm notation (roman numbers for now)
# maj to I, min to i, dim to o, dom7 to 7, etc.
# tag: values of INTERVALS_TO_CHORD_QUALITY
# values: tuple with chord quality to append (suffix) + True/False if major or minor
CHORD_QUALITY_TO_MXHM = {
    'maj': ('',     False), 
    'min': ('',     True),    
    'dim': ('o',    True),  
    'aug': ('+',    False), 
    'sus2': ('sus2', False),
    'sus4': ('sus4', False),
    'dom7': ('7',    False),  # example: ii7
    'maj7': ('M7',   False), 
    'min7': ('m7',   True),  
    'hdim7': ('ø7',   True),  
    'dim7':  ('o7',   True),  
    'augmaj7': ('+M7',  False),
    'sus4m7': ('sus4m7', False),
    'dom9': ('9',    False),
    'maj9':  ('M9',   False),
    'min9': ('m9',   True),
}

# dict for chords' functions
# maybe better with chord names ... <------- NB
MAJOR_FUNCTION = {1:'I', 2:'II', 3:'III', 4:'IV', 5:'V', 6:'VI', 7:'VII'}
MINOR_FUNCTION = {1:'i', 2:'ii', 3:'iii', 4:'iv', 5:'v', 6:'vi', 7:'vii'}

# note names for kern notation (independent from the octave)
# no b, only # 
KERN_NOTE_NAME = { 0:'c',  1:'c#', 2:'d',  3:'d#', 4:'e', 5:'f',  6:'f#', 7:'g',  8:'g#', 9:'a', 10:'a#', 11:'b'}

# note names for screen output
SCREEN_NOTE_NAME = { 0:'C', 1:'C#', 2:'D', 3:'D#', 4:'E', 5:'F', 6:'F#', 7:'G', 8:'G#', 9:'A', 10:'A#', 11:'B'}

# note duration / denominator (power of 2), with list
KERN_NOTE_DURATIONS = [1, 2, 4, 8, 16, 32, 64, 128]

# orders of accidentals, sharps and flats
SHARPS = ['f','c','g','d','a','e','b']
FLATS = ['b','e','a','d','g','c','f']

# sharps and flats for major keys (and subsequently for relative minor keys)
# positive for sharps, negative for flats
MAJOR_KEY_ALTERATIONS = {
    0:0,  # C
    7:1,  # G (f#)
    2:2,  # D (f#,c#)
    9:3,  # A (f#,c#,g#)
    4:4,  # E (f#,c#,g#,d#)
    11:5, # B (f#,c#,g#,d#,a#)
    6:6,  # F# maj or Gbmaj (f#,c#,g#,d#,a#,e#) or (Bb, Eb, Ab, Db, Gb)
    5:-1, # F (Bb)
    10:-2, # Bb (Bb, Eb)
    3:-3,  # Eb (Bb, Eb, Ab)
    8:-4,  # Ab (Bb, Eb, Ab, Db)
    1:-5   # Db (Bb, Eb, Ab, Db, Gb)
}

# diatonic modes
# also here tuples as keys because lists are not hashable
INTERVALS_TO_MODE= {
    (2,2,1,2,2,2): 1,  # ionian
    (2,1,2,2,2,1): 2,  # dorian
    (1,2,2,2,1,2): 3,  # phrygian
    (2,2,2,1,2,2): 4,  # lydian
    (2,2,1,2,2,1): 5,  # mixolydian
    (2,1,2,2,1,2): 6,  # aeolian
    (1,2,2,1,2,2): 7,  # locrian
}


MODES = {1: 'ion', 2:'dor', 3:'phr', 4:'lyd', 5:'mix', 7:'loc'}


