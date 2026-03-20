# beat:  |0123|4567|...    bar at beat 4
# legato with [...] (on 2 different lines in the kern file)
from data_structures import KERN_NOTE_NAME, KERN_NOTE_DURATIONS, INTERVALS_TO_CHORD_QUALITY, CHORD_QUALITY_TO_MXHM, MAJOR_FUNCTION, MINOR_FUNCTION
from fractions import Fraction # for exact ractionals
from data_conversions import duration_to_kern
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
    
    #sorted_meters = sorted(meters, key=lambda m: m['beat'])
    # function to get beats
    def get_beat(m): 
        return m['beat']
    
    # orders per beat --> ordina i cambi di metrica in base al beat di inizio  (è una lista piccola!)
    sorted_meters = sorted(meters, key=get_beat)    # <<<<<<<<<<<<<<<<<<<<<<<  RIVEDI
    
    # usa un set per raccogliere le stanghette: evita duplicati (es. quando la fine di un metro coincide con l'inizio del successivo).
    barlines = set()      # <<<<<<<<<<<<<<<<<<<<<<<Set[Fraction]
    
    print("PRINT")
    
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
            bar_line += beats_per_bar

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

def split_at_barlines(onset: Fraction, duration: Fraction, kern_pitch: str, is_rest: bool, barline_positions: List[Fraction], beat_unit: int,):
    # divides an event that surpass a bar with legatos
    # list of tuples: one note can be 1, 2, 3 segments long
    # La funzione chiamante deve sapere quanti segmenti ha prodotto e dove iniziano.
    # Una lista è la struttura naturale per "zero o più risultati".
    # Es: (Fraction(3,2), Fraction(1,2), '[8f#')
    #     ↑ onset 3.5     ↑ dur 0.5 beat  ↑ token **kern
    '''
    La logica delle legature:
        In **kern una legatura collega note dello stesso pitch che devono
        suonare come una nota unica (senza reattaccare):
            '[4c'  = comincia una nota legata (il [ è PRIMA della durata)
            '4c]'  = finisce una nota legata  (il ] è DOPO il pitch)
            '[4c]' = nota nel mezzo di una catena (sia apre che chiude)

        Regola: solo il PRIMO segmento non ha '[' in testa.
                tutti i segmenti non-primi hanno '[' in testa.
                solo l'ULTIMO segmento ha ']' in coda.
                i segmenti intermedi hanno sia '[' che ']'.
        Le pause non usano legature (si dividono e basta).
    '''
    
    offset = onset + duration # operation between Fraction elements, ok
    
    internal = []
    for bar_line in barline_positions:  # barline_positions calcolate alla funzione prima
        if onset < bar_line < offset:
            internal.append(bar_line)
            
    # if no bar is surpassed
    if not internal:
        dur = duration_to_kern(float(duration), beat_unit)
        # se silenzio
        if is_rest:
            token = f"{dur}r"
        else:
            token = f"{dur}{kern_pitch}"  # es. '8f#' = croma Fa#
        return [(onset, duration, token)]   

    # at least one bar surpassed
    boundaries = internal + [offset]  # (onset,fine prima bar), (inizio prima bar, fine seconda bar), (inizio seconda bar, offset)
    
    segments = [] # : List[Tuple[Fraction, Fraction, str]]
    cur = onset 
    
    
    for idx, bnd in enumerate(boundaries):
        # enumerate dà (0, boundary[0]), (1, boundary[1]), ...
        # idx ci serve per capire se siamo al primo o all'ultimo segmento

        segment_dur = bnd - cur   # durata di questo segmento

        # Sicurezza: ignoriamo segmenti di durata zero o negativa (potrebbero capitare con dati imprecisi)
        if segment_dur <= Fraction(0):
            cur = bnd
            continue   

        d = duration_to_kern(float(segment_dur), beat_unit)

        if is_rest:
            # Le pause si dividono senza legature: ogni segmento è indipendente
            token = f"{d}r"

        else:
            # Note: dobbiamo determinare se questo segmento è primo, ultimo o intermedio
            is_first = (idx == 0)
            is_last  = (bnd == offset)   # questo confine è la fine originale?

            if is_first and not is_last:
                # primo di più segmenti: apre la legatura verso il prossimo
                token = f"[{d}{kern_pitch}"  # es: '[8f#' 

            elif is_last and not is_first:
                # ultimo di più segmenti: chiude la legatura dal precedente
                token = f"{d}{kern_pitch}]" #es: '4f#]' 

            elif not is_first and not is_last:
                # INTERMEDIO: sia apre (verso il prossimo) che chiude (dal precedente)
                token = f"[{d}{kern_pitch}]"  # Es: '[4f#]' = semiminima Fa# nel mezzo di una catena legata

            else: # is_first AND is_last: non dovrebbe capitare perché
                token = f"{d}{kern_pitch}"

        segments.append((cur, segment_dur, token))
        cur = bnd   # il prossimo segmento inizia dove finisce questo

    return segments


