# functions to transform one data format/type in another one
# to manage the data flux!
# one task --> one function
from data_structures import KERN_NOTE_NAME, KERN_NOTE_DURATIONS
from fractions import Fraction # for exact ractionals

# we do not convert really in midi, we use midi numbers only as a reference
# Only as reference: C-1=0 (+1!!), C0=12, C1=24, C2=36, C3=48, C4=60 (middle C), C5=72, C6=84
# BUT Hooktheory uses another conversion: octave 0  is octave 4 in MIDI, octave 1 is octave 5 in MIDI, octave -1 is octave 3 in MIDI, ecc.
# MIDI = (octave + 4 + 1) * 12 + pitch_class
def pitch_to_midi(octave: int, pitch_class: int):
    return (octave + 5) * 12 + pitch_class

def midi_to_kern_pitch(midi: int):
    octave = (midi // 12) - 1 # integer division
    pitch_class = midi % 12 # resto
    base = KERN_NOTE_NAME[pitch_class]   # ex: c#
    letter = base[0]    # ex: c (first character of string "c#")
    alterations = base[1:]  # ex: everything after letter: "#" or " "
    if octave >= 4:
        reps = octave - 4 + 1 # how many times i have to repeat the letter
        return letter.lower() * reps + alterations   # + alterations: concatenate "#" or nothing 
    else:
        reps = 4 - octave
        return letter.upper() * reps + alterations


# Fraction(1, 3) is exactly 1/3, no approximations! (Python represents it as couple of integers)
# floating point problem: 0.1 + 0.2 == 0.3  is  False in Python
# Converts duration in beat in the relative kern duration (beat unit default=4)
def duration_to_kern(beats_dur: float, beat_unit: int = 4):
    '''
    beats_dur: absolute duration in beat (1.0, 1.5, 2.0, etc.)
    beat_unit: denominator of the metric (if meter is 3/4 --> 4)
    
    To remember:
    in 4/4 (beat_unit=4): 1 beat = 1 quarter note (semiminima) = 4 in lern
    in 6/8 (beat_unit=8): 1 beat = 1 octave note (croma)  = 8 in kern
        
    IDEA: In **kern the duration is the DENOMINATOR wrt QUARTER NOTES
          we have to express beats_dur as fraction of quarter notes
    '''
    quarter_note = Fraction( int(round(beats_dur * 1024 * 4 / beat_unit)), 1024).limit_denominator(1024)

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
    
    
            


