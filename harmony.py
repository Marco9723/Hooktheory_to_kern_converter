from fractions import Fraction # for exact ractionals
from key_signatures import get_active_key
from data_conversions import build_scale, intervals_to_chord_quality, pitch_class_to_roman_numbers
from typing import List, Dict

def harmony_to_events(harmony: List[Dict], keys: List[Dict],):  # -> List[Tuple[Fraction, Fraction, str]]
    """
    non servono pause, non serve dividere alle stanghette la spina **mxhm non ha bisogno di riempire il tempo tra accordi.

    1) Troviamo la tonalità attiva al suo onset (per le modulazioni)
    2) Costruiamo la scala con build_scale() 
    3) Produciamo il numerale romano con pc_to_roman_numeral()

    harmony: lista di accordi (campo harmony delle annotations)
    keys   : lista dei cambi di tonalità (per gestire le modulazioni)

    Ritorna: lista di (onset, duration, mxhm_token) ordinata per onset
    """
    events = []  # List[Tuple[Fraction, Fraction, str]]

    # Ordiniamo per onset: il dataset dovrebbe già essere ordinato
    for chord in sorted(harmony, key=lambda c: c['onset']):

        # Convertiamo onset e offset in Fraction per precisione esatta
        onset  = Fraction(chord['onset']).limit_denominator(1024)
        offset = Fraction(chord['offset']).limit_denominator(1024)
        dur    = offset - onset

        # tonalità attiva al momento dell'accordo 
        tonic_pc, intervals = get_active_key(onset, keys)

        # costruiamo la mappa pitch_class >>> grado 
        pitch_class_to_degree, _ = build_scale(tonic_pc, intervals)

        # deduciamo la qualità dagli intervalli, elenco di intervalli per ogni accordo
        intervals_tuple = tuple(int(x) for x in chord['root_position_intervals'])
        # int(x) per sicurezza: i valori nel JSON potrebbero essere float (es. 4.0)
        # e la nostra tabella ha chiavi di interi puri (4, non 4.0)
        # Nota: 4 == 4.0 in Python, ma (4, 3) != (4.0, 3.0) come chiavi di dict!

        quality   = intervals_to_chord_quality(intervals_tuple)
        inversion = int(chord.get('inversion', 0))
        root_pc   = int(chord['root_pitch_class'])

        # produciamo il token
        token = pitch_class_to_roman_numbers(root_pc, quality, inversion, pitch_class_to_degree)
        events.append((onset, dur, token))

    return events