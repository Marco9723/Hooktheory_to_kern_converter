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
    
    # function to get beats
    def get_beat(m): 
        return m['beat']
    
    # orders per beat --> ordina i cambi di metrica in base al beat di inizio  (è una lista piccola!)
    sorted_meters = sorted(meters, key=get_beat)    # <<<<<<<<<<<<<<<<<<<<<<<  RIVEDI
    
    # usa un set per raccogliere le stanghette: evita duplicati (es. quando la fine di un metro coincide con l'inizio del successivo).
    barlines: Set[Fraction] = set()      # <<<<<<<<<<<<<<<<<<<<<<<
    
    # itera sul cambio di metrica
    for i, meter in enumerate(sorted_meters):
        #   i=0, meter={"beat":0, "beats_per_bar":4, ...}
        #   i=1, meter={"beat":16, "beats_per_bar":3, ...}
        start = Fraction(meter['beat'])   # beat inizio del metro
        beats_per_bar   = meter['beats_per_bar']  # beats per battuta
        
        # calcolo fine del metro
        # Quindi ogni metro è attivo su [start, end)
        if i + 1 < len(sorted_meters):
            # se esiste un metro successivo (beat finale del metro)
            end = Fraction(sorted_meters[i + 1]['beat'])
        else:
            # se non esiste un metro successivo
            end = Fraction(num_beats)
            
        # Generiamo stanghette a intervalli regolari di bpb beat
        # La prima stanghetta è a start + bpb (non a start, che è l'inizio)
        bar_line = start + beats_per_bar
        while bar_line <= end:
            # lista di beats dove cade la barline
            barlines.add(bar_line)   # add() su un set: aggiunge solo se non c'è già
            bl += beats_per_bar

    # sorted() su un set: converte in lista ordinata
    # lista ordinata di Fraction: posizioni delle stanghette (beats)
    return sorted(barlines)


def get_active_meter(beat: Fraction, meters: List[Dict]) -> Tuple[int, int]:
    # Restituisce la metrica (beats_per_bar, beat_unit) attiva a una data posizione.
    # funzione viene chiamata per OGNI evento del brano
    # returns Tuple (beats_per_bar, beat_unit) — es. (4, 4) per 4/4
    beats_per_bar = 4
    beat_unit = 4
    
    for m in sorted(meters, key=lambda x: x['beat']):
        if Fraction(m['beat'])<=beat:
            # the meter is active
            beats_per_bar=m['beats_per_bar']
            beat_unit=m.get('beat_unit',4)
        else:
            break
    return beats_per_bar, beat_unit


