from fractions import Fraction # for exact ractionals
from data_conversions import pitch_to_midi, midi_to_kern_pitch
from temporal_structures import split_at_barlines
from typing import List, Dict

def split_into_voices(notes: List[Dict]) -> List[List[Dict]]:
    """
    Vogliamo dividerli nel minimo numero di gruppi tali che all'interno di ogni gruppo nessun intervallo si sovrapponga
    1. Ordina gli intervalli per onset.
    2. Per ogni intervallo, assegnalo alla prima "voce" disponibile (quella la cui ultima nota è già finita).
    3. Se nessuna voce è disponibile, creane una nuova.
    Args: notes: lista di note con campi onset, offset, pitch_class, octave

    """
    
    if not notes:
        return [[]]  #problems with []
    
    # orders per onset
    # Usiamo pitch_class come chiave secondaria per riproducibilità: se due note hanno lo stesso onset, l'ordine tra loro è deterministico
    # La key è una tupla: Python confronta prima il primo elemento (onset), poi il secondo (pitch_class) in caso di parità.
    sorted_notes = sorted(notes, key=lambda n: (n['onset'], n['pitch_class']))
    
    # data structures
    voices = []     # ogni elemento è una lista di note   List[List[Dict]]
    voice_ends = []      # offset dell'ultima nota di ogni voce List[float]
    # Perché float e non Fraction? Qui non facciamo aritmetica, solo confronti: il float va bene.

    for note in sorted_notes:
        onset = float(note['onset'])   # float() per il confronto con voice_ends
        placed = False                  # flag: abbiamo trovato una voce?

        # cerca una voce disponibile 
        for v, end in enumerate(voice_ends):
            # 1e-9 = tolleranza per floating-point:  "questa voce è disponibile se la sua ultima nota è finita"
            if end <= onset + 1e-9:
                voices[v].append(note)          # aggiungiamo la nota alla voce
                voice_ends[v] = float(note['offset'])   # aggiorniamo la fine
                placed = True
                break   # usciamo dal for: abbiamo trovato la voce giusta

        # nessuna voce disponibile: nuova voce
        if not placed:
            voices.append([note])                        # nuova lista con questa nota
            voice_ends.append(float(note['offset']))     # il suo offset è la fine

    return voices



def voice_to_events(voice_notes: List[Dict], barline_positions: List[Fraction], num_beats: int, beat_unit: int,):
    
    # Converte le note di una voce nella sequenza completa di eventi **kern,
    # riempiendo i gap con pause e dividendo le note alle stanghette.
    
    events = []  # List[Tuple[Fraction, Fraction, str]]
    current = Fraction(0)        # cursore: avanziamo beat per beat
    total   = Fraction(num_beats)

    for note in sorted(voice_notes, key=lambda n: n['onset']):
        # Convertiamo onset e offset in Fraction con denominatore massimo 1024
        # limit_denominator(1024): semplifica la frazione evitando denominatori enormi
        # Es: Fraction('3.5') → Fraction(7, 2)  (già semplice)
        #     Fraction(3.333...) → potrebbe dare Fraction(9999, 3000) senza limit
        onset  = Fraction(note['onset']).limit_denominator(1024)
        offset = Fraction(note['offset']).limit_denominator(1024)
        dur    = offset - onset

        # Gap prima della nota: aggiungi pausa
        if onset > current:
            rest_dur = onset - current
            # La pausa potrebbe attraversare stanghette, splittiamo anche lei
            # kern_pitch='r': indica pausa (non usato per is_rest=True)
            # is_rest=True: nessuna legatura, solo divisione durata
            rest_segs = split_at_barlines(current, rest_dur,'r', True, barline_positions, beat_unit)
            events.extend(rest_segs)
            # extend() aggiunge tutti gli elementi di rest_segs alla lista events (append aggiungerebbe la lista come un elemento solo)

        # Nota melodica effettiva
        midi = pitch_to_midi(note['octave'], note['pitch_class'])
        kern_pitch = midi_to_kern_pitch(midi)

        # is_rest=False: questa è una nota vera, usa legature se necessario
        note_segs = split_at_barlines(onset, dur,kern_pitch,False,barline_positions,beat_unit)
        events.extend(note_segs)
        current = offset   # aggiorna il cursore alla fine di questa nota

    # pausa finale: dalla fine dell'ultima nota a num_beats
    if current < total:
        rest_dur  = total - current
        rest_segs = split_at_barlines(current, rest_dur, 'r', True, barline_positions, beat_unit)
        events.extend(rest_segs)

    return events