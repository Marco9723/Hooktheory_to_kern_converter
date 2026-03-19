from data_structures import SHARPS, FLATS, MODES, KERN_NOTE_NAME,  MAJOR_KEY_ALTERATIONS, INTERVALS_TO_MODE, CHORD_QUALITY_TO_MXHM, MAJOR_FUNCTION, MINOR_FUNCTION
from fractions import Fraction # for exact ractionals
from data_conversions import duration_to_kern
from typing import List, Dict,Tuple, Optional, Any, Set

def get_active_key(beat: Fraction, keys: List[Dict]) -> Tuple[int, List[int]]:
    """
    Restituisce la firma tonale attiva (tonica, intervalli) a una data posizione.
    Identica logica di get_active_meter() ma per la tonalità.
    Gestisce le modulazioni: se il brano cambia tonalità a metà, ogni accordo verrà analizzato con il suo contesto tonale corretto.

    Esempio di modulazione:
        keys = [
            {"beat": 0,  "tonic_pitch_class": 0, ...},  ← Do maggiore
            {"beat": 32, "tonic_pitch_class": 7, ...}   ← Sol maggiore dal beat 32
        ]
        get_active_key(beat=20, keys) → (0, [2,2,1,2,2,2])  ← ancora Do
        get_active_key(beat=36, keys) → (7, [2,2,1,2,2,2])  ← ora Sol

    Args:
        beat: posizione in beat
        keys: lista dei cambi di tonalità

    Returns:
        Tuple (tonic_pitch_class, scale_degree_intervals)
    """
    # Default: Do maggiore
    tonic_pc  = 0
    intervals = [2, 2, 1, 2, 2, 2]

    for k in sorted(keys, key=lambda x: x['beat']):
        if Fraction(k['beat']) <= beat:
            tonic_pc  = k['tonic_pitch_class']
            intervals = k['scale_degree_intervals']
        else:
            break

    return tonic_pc, intervals


def build_kern_key_sig(tonic_pitch_class: int, intervals: List[int]) -> str:
    # creates kern token of the key signature: *k[<alterations>]
    # example: *k[f#c#] for D major but also B minor
    # based on circle of fifths: f c g d a e b
    # the relative minor will have the same alterations
    
    # convertiamo la lista in tupla per usarla come chiave
    mode = INTERVALS_TO_MODE.get(tuple(intervals), 1)   # default: modo 1 (maggiore)
    
    # se minore naturale
    if mode == 6:
        # trovo relativa maggiore (+3st)
        relative_major=(tonic_pitch_class+3)%12
    else:
        # for semplicity we use directly the tonic
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
    # tonality kern token: *D, *a , *G[mix]
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
    