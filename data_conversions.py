# functions to transform one data format/type in another one
# to manage the data flux!
# one task --> one function
from data_structures import KERN_NOTE_NAME, KERN_NOTE_DURATIONS, INTERVALS_TO_CHORD_QUALITY, SCREEN_NOTE_NAME, CHORD_QUALITY_TO_MXHM, MAJOR_FUNCTION, MINOR_FUNCTION, MAJOR_CHORD_SYMBOL, MINOR_CHORD_SYMBOL
from fractions import Fraction # for exact ractionals
from typing import List, Dict,Tuple

# we do not convert really in midi, we use midi numbers only as a reference
# example: C-1=0 (+1!!), C0=12, C1=24, C2=36, C3=48, C4=60 (middle C), C5=72, C6=84
# remeber the different Hooktheory/kern convention: octave 0 is octave 4 in MIDI, octave 1 is octave 5 in MIDI, octave -1 is octave 3 in MIDI, ...
# midi = (octave + 4 + 1) * 12 + pitch_class

def pitch_to_midi(octave: int, pitch_class: int):
    return (octave + 5) * 12 + pitch_class

def midi_to_kern_pitch(midi: int):
    octave = (midi // 12) - 1               # integer division
    pitch_class = midi % 12                 # rest
    base = KERN_NOTE_NAME[pitch_class]      # ex: c#
    letter = base[0]                        # ex: c (first character of string "c#")
    alterations = base[1:]                  # ex: everything after letter: "#" or " "
    if octave >= 4:
        reps = octave - 4 + 1               # how many times i have to repeat the letter
        return letter.lower() * reps + alterations   # + alterations: concatenate "#" or nothing 
    else:
        reps = 4 - octave
        return letter.upper() * reps + alterations


# converts duration in beat in the relative kern duration (beat unit default=4)
def duration_to_kern(beats_dur: float, beat_unit: int = 4):
    '''
    beats_dur: absolute duration in beat (1.0, 1.5, 2.0, ...)
    beat_unit: denominator of the metric (if meter is 3/4 --> 4)
    
    To remember:
    in 4/4 (beat_unit=4): 1 beat = 1 quarter note (semiminima) = 4 in kern
    in 6/8 (beat_unit=8): 1 beat = 1 octave note (croma)  = 8 in kern
        
    MAIN IDEA/LOGIC: in kern the duration is the denominator wrt quarter notes
          we have to express beats_dur as fraction of quarter notes!!!
    '''
    # duration wrt to quarter notes!!
    # beats_dur*4/beat_unit: converts beats into quarter notes: 
    # In 4/4, a pointed quarter note is 1,5 times a quarter note: 1.5 * 4 / 4 = 1.5   
    # In 6/8 (beat_unit=8): 1 octave note = 0.5 quarter notes: 1.0 * 4 / 8 = 0.5
    quarter_note = Fraction( int(round(beats_dur * 1024 * 4 / beat_unit)), 1024).limit_denominator(1024) 
    # * 1024 in order to multiply by a big integer --> to get more precision!
    # roud for floating point
    # int for Fraction 

    # standard/simple durations. Ex: quarter_note = 1 --> k=4 --> '4'
    for k in KERN_NOTE_DURATIONS:
        if quarter_note == Fraction(4,k):
            return str(k)
    
    # single-pointed durations
    for k in KERN_NOTE_DURATIONS:
        if quarter_note == Fraction(4, k) * Fraction(3, 2):
            return f"{k}."
    
    # double -pointed durations
    for k in KERN_NOTE_DURATIONS:
        if quarter_note == Fraction(4, k) * Fraction(7, 4):
            return f"{k}.."
    
    # groups of 3
    for k in KERN_NOTE_DURATIONS:
        if quarter_note == Fraction(4, k) * Fraction(2, 3):
            return f"{k}%3"
        
    # groups of 5
    for k in KERN_NOTE_DURATIONS:
        if quarter_note == Fraction(4, k) * Fraction(4, 5):
            return f"{k}%5"
    
    # groups of 7
    for k in KERN_NOTE_DURATIONS:
        if quarter_note == Fraction(4, k) * Fraction(4, 7):
            return f"{k}%7"
    
    # RIVEDI  <---------
    best= KERN_NOTE_DURATIONS[0]
    for k in KERN_NOTE_DURATIONS:
        best = min(best, abs(Fraction(4, k) - quarter_note))
    
    print("Warning: note approximated")    
    return str(best)
    
    
            
def build_scale(tonic: int, intervals: List[int]):
    # d major (tonic=2, intervals=[2,2,1,2,2,2])
        
    scale_degrees = []
    t=tonic
    
    # scale degrees: for example in c {0,2,4,5,7,9,11}  << pitch class
    for i in range(7):         
        scale_degrees.append(t % 12)  # to stay in range 0-11
        
        if i < len(intervals):
            t += intervals[i]  # updates new t
    
    # same list, but Dict, for harmonic analysis (pitch class >> grade)
    # {2: 1, 4: 2, 6: 3, ...}  (pitch_class >> grade from 1 to 7)
    pitch_class_to_degree = {
        pc_val: idx + 1  # Alla nota pc_val assegna il grado idx + 1
        for idx, pc_val in enumerate(scale_degrees)
    }
    
    return pitch_class_to_degree, scale_degrees
        
        
def intervals_to_chord_quality(intervals: Tuple[int,...]):       
    quality = INTERVALS_TO_CHORD_QUALITY.get(intervals)
    if quality:
        return quality
    
    # more possibilities with this chord structure can exist
    if len(intervals) >= 2:
        basic_chord_structure = INTERVALS_TO_CHORD_QUALITY.get(intervals[:2])  # take first 2 elements
        if basic_chord_structure:
            return basic_chord_structure
        else:
            print("Chord not recognized")
            
    return 'maj'
    

# for now roman numbers
def pitch_class_to_roman_numbers(root_pitch_class: int, quality: str, inversion: int, pitch_class_to_degree: Dict[int,int]):  
    # Kern format: prefix-roman-suffix-inversion
    # Ex:  I, vi, V7, bVII, iim7, viio7, V7/5
    suffix, lower = CHORD_QUALITY_TO_MXHM.get(quality, ('', False))  # default False
    prefix = ''
    
    if root_pitch_class in pitch_class_to_degree:
        # diatonic chord
        degree = pitch_class_to_degree[root_pitch_class]
        
    else:
        # chromatic chords 
        # flat if a flat below --> prefix 'b'
        flat  = (root_pitch_class + 1) % 12  # nearest grade a flat below (%12 to stayin range 0-11)
        sharp = (root_pitch_class - 1) % 12  # # nearest grade a sharp above 
    
        if flat in pitch_class_to_degree:
            degree = pitch_class_to_degree[flat]
            prefix = 'b'
        elif sharp in pitch_class_to_degree:
            degree = pitch_class_to_degree[sharp]
            prefix = '#'    # prefix IV
        else:
            degree = 1
            print("Chord grade not recognized")
            
    # build chord symbol
    if quality in ('dim', 'dim7'):
        # diminished
        roman = prefix + MINOR_FUNCTION.get(degree, 'i') + 'o'
        if quality == 'dim7':
            roman += '7'   # complete diminished seventh

    elif quality == 'hdim7':
        # half diminished
        roman = prefix + MINOR_FUNCTION.get(degree, 'i') + 'ø7'

    elif lower:
        # minor chords
        roman = prefix + MINOR_FUNCTION.get(degree, 'i') + suffix

    else:
        # maj, dom, aug
        roman = prefix + MAJOR_FUNCTION.get(degree, 'I') + suffix

    # inversions (0,1,2,3)
    if inversion == 1:
        roman += '/3'
    elif inversion == 2:
        roman += '/5'
    elif inversion >= 3:
        roman += '/7'

    return roman



# not supported 
def pitch_class_to_chord_notation(root_pitch_class: int, quality: str, inversion: int, pitch_class_to_degree: Dict[int,int]):
    
    suffix, lower = CHORD_QUALITY_TO_MXHM.get(quality, ('', False))  # default False
    # root_pitch_class: '11' '7' '10' '0' '9' '0'
    # pitch_class_to_degree: {'2': 1, '4': 2, '6': 3, '7': 4, '9': 5, '11': 6, '1': 7}  --> is in D
    
    # BUILD CHORD SYMBOL
    # KERN_NOTE_NAME = minor note names
    # SCREEN_NOTE_NAME = major note names
    if quality in ('dim', 'dim7'):
        # diminished
        chord_notation = KERN_NOTE_NAME.get(root_pitch_class) + 'o'  # degree: from 1 to 7
        if quality == 'dim7':
            chord_notation += '7'   # viio7 = settima diminuita completa

    elif quality == 'hdim7':
        # half diminished
        chord_notation = KERN_NOTE_NAME.get(root_pitch_class) + 'ø7'

    elif lower:
        # minor chords
        chord_notation = KERN_NOTE_NAME.get(root_pitch_class) + suffix

    else:
        # maj, dom, aug
        chord_notation = SCREEN_NOTE_NAME.get(root_pitch_class) + suffix

    # inversions (0,1,2,3)   <<<<<<<<<<<<<  to check
    if inversion == 1:
        bass = (root_pitch_class+4)%12
        chord_notation += f'/{SCREEN_NOTE_NAME.get(bass)}'
    elif inversion == 2:
        bass = (root_pitch_class+7)%12
        chord_notation += f'/{SCREEN_NOTE_NAME.get(bass)}'
    elif inversion >= 3:
        bass = (root_pitch_class+11)%12
        chord_notation += f'/{SCREEN_NOTE_NAME.get(bass)}'

    return chord_notation