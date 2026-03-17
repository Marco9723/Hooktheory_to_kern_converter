# beat:  |0123|4567|...    bar at beat 4
# legato with [...] (on 2 different lines in the kern file)
from data_structures import KERN_NOTE_NAME, KERN_NOTE_DURATIONS, INTERVALS_TO_CHORD_QUALITY, CHORD_QUALITY_TO_MXHM, MAJOR_FUNCTION, MINOR_FUNCTION
from fractions import Fraction # for exact ractionals
from typing import List, Dict,Tuple, Optional, Any, Set

def compute_barline_positions(meters: List[Dict], num_beats: int) -> List[Fraction]:
    # need Fraction to make coparisons of values
    # "meters" tag of json file. Example:
    # [{"beat": 0,  "beats_per_bar": 4, "beat_unit": 4},   4/4 from beat 0 to 15
    # {"beat": 16, "beats_per_bar": 3, "beat_unit": 4}]   3/4 from beat 16
    
    # Perché usiamo un Set invece di una List per raccogliere le stanghette? Perché a un cambio di metrica potremmo generare stanghette duplicate
    # (la fine del metro vecchio coincide con l'inizio del nuovo). Il Set elimina automaticamente i duplicati.
    # Alla fine convertiamo in List e ordiniamo per avere una sequenza.
    
    '''     
    Args:
        meters   : lista di cambi di metrica dalle annotations
        num_beats: durata totale del brano (campo 'num_beats')

    Returns:
        Lista ordinata di Fraction — posizioni delle stanghette
    '''
    
    return