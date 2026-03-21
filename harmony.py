from fractions import Fraction # for exact ractionals
from key_signatures import get_active_key
from data_conversions import build_scale, intervals_to_chord_quality, pitch_class_to_roman_numbers, pitch_class_to_chord_notation
from typing import List, Dict

def harmony_to_events(harmony: List[Dict], keys: List[Dict],):  # -> List[Tuple[Fraction, Fraction, str]]
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
        onset  = Fraction(chord['onset']).limit_denominator(1024)
        offset = Fraction(chord['offset']).limit_denominator(1024)
        dur    = offset - onset

        # active key at the time of the chord 
        tonic_pc, intervals = get_active_key(onset, keys)
        
        # build pitch_class >>> grado map
        pitch_class_to_degree, _ = build_scale(tonic_pc, intervals)
        
        # we deduce quality from intervals, list of intervals for each chord
        intervals_tuple = tuple(int(x) for x in chord['root_position_intervals'])
        
        quality   = intervals_to_chord_quality(intervals_tuple)
        inversion = int(chord.get('inversion', 0))
        root_pc   = int(chord['root_pitch_class'])
        
        # token
        token = pitch_class_to_roman_numbers(root_pc, quality, inversion, pitch_class_to_degree)  # for roman numerals notation
        # token = pitch_class_to_chord_notation(root_pc, quality, inversion, pitch_class_to_degree)  # for standard chord notation
        
        events.append((onset, dur, token))

    return events