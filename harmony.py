from fractions import Fraction # for exact ractionals
from key_signatures import get_active_key
from data_conversions import build_scale, intervals_to_chord_quality, pitch_class_to_roman_numbers
from typing import List, Dict

def harmony_to_events(harmony: List[Dict], keys: List[Dict]):  
    """
    no rests are needed, no barline divisions are needed and **mxhm doesn't need to fill the time between chords

    1) find the active key at its onset (for modulations)
    2) build the scale (build_scale())
    3) produce the roman numeral / chord notation with letters

    harmony: list of chords (harmony field of annotations)
    keys: list of key changes (for modulations)
    returns: list of (onset, duration, mxhm_token) sorted by onset
    """
    events = []  # List[Tuple[Fraction, Fraction, str]]

    # order by onsets for safety
    for chord in sorted(harmony, key=lambda c: c['onset']):

        # convert onset and offset to Fraction for exact precision
        # find the simplest fraction with denominator <= 1024 that approximates this value
        onset  = Fraction(chord['onset']).limit_denominator(1024)
        offset = Fraction(chord['offset']).limit_denominator(1024)
        dur    = offset - onset

        # active key at the time of the chord 
        tonic_pc, intervals = get_active_key(onset, keys)
        
        # build pitch_class >>> grades map
        pitch_class_to_degree, _ = build_scale(tonic_pc, intervals)
        
        # we deduce quality from intervals, list of intervals for each chord: [2,3,3] --> into tuple (2,3,3)
        intervals_tuple = tuple(int(x) for x in chord['root_position_intervals'])
        
        quality   = intervals_to_chord_quality(intervals_tuple)
        inversion = int(chord.get('inversion', 0))
        root_pc   = int(chord['root_pitch_class'])
        
        # token
        token = pitch_class_to_roman_numbers(root_pc, quality, inversion, pitch_class_to_degree)  # for roman numerals notation
        
        events.append((onset, dur, token))

    return events