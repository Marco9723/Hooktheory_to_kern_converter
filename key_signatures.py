from data_structures import SHARPS, FLATS, MODES, KERN_NOTE_NAME,  MAJOR_KEY_ALTERATIONS, INTERVALS_TO_MODE, CHORD_QUALITY_TO_MXHM, MAJOR_FUNCTION, MINOR_FUNCTION
from fractions import Fraction # for exact ractionals
from data_conversions import duration_to_kern
from typing import List, Dict,Tuple, Optional, Any, Set

def get_active_key(beat: Fraction, keys: List[Dict]):
    """
    returns the active tonal signature (root, intervals) at a given position (similar to get_active_meter()). To manage modulations!
    modulation example (in 'key' tag) form C to G:  {"beat": 0,  "tonic_pitch_class": 0, ...}  --> {"beat": 32, "tonic_pitch_class": 7, ...}

    inputs:
        beat: position in beat
        keys: list of tonality change
    returns:
        Tuple (tonic_pitch_class, scale_degree_intervals)
    """
    # default: C major
    tonic_pc  = 0
    intervals = [2, 2, 1, 2, 2, 2]

    # check "key" field of the dataset
    # update as long as the change is in the past, stop as soon as you find one in the future
    for k in sorted(keys, key=lambda x: x['beat']):  # sort the keys list by the beat field in ascending order
        if Fraction(k['beat']) <= beat:
            tonic_pc  = k['tonic_pitch_class']
            intervals = k['scale_degree_intervals']
        else:
            break

    return tonic_pc, intervals


def build_kern_key_sig(tonic_pitch_class: int, intervals: List[int]):
    # creates kern token of the key signature: *k[<alterations>]
    # example: *k[f#c#] for D major but also B minor
    # based on circle of fifths: f c g d a e b
    # the relative minor will have the same alterations
    
    # we convert the list to a tuple to use it as a key!!
    mode = INTERVALS_TO_MODE.get(tuple(intervals), 1)   # default: mode 1 (major)
    
    # if natura minor
    if mode == 6:
        # find relative major (+3st)
        relative_major=(tonic_pitch_class+3)%12
    else:
        # otherwise for semplicity we use directly the tonic
        relative_major = tonic_pitch_class
        
    n = MAJOR_KEY_ALTERATIONS.get(relative_major,0)
    
    # string of alterations
    if n == 0:
        return '*k[]'
    
    # how many # there are
    elif n>0:
        alterations = ''.join(f"{note}#" for note in SHARPS[:n])
    
    # how many b there are
    else:
        alterations = ''.join(f"{note}-" for note in FLATS[:abs(n)])
    
    return f"*k[{alterations}]"


def build_tonal_token(tonic_pitch_class: int, intervals: List[int]) -> str:
    # tonality kern token: *D, *a , *G[mix] if mixolydian!
    # different function becuse D is different from relative minor scale b
    note_name = KERN_NOTE_NAME.get(tonic_pitch_class, 'C')  #default C
    mode = INTERVALS_TO_MODE.get(tuple(intervals), 1)
    
    if mode == 1:
        return f"*{note_name}:"
    
    elif mode == 6:
        # minor: lower letter
        return f"*{note_name.lower()}:"  
    
    else: 
        modal_scale = MODES.get(mode, 'unknown')
        return f"*{note_name}[{modal_scale}]:"
    