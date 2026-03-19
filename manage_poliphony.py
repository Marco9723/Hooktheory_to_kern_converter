from data_structures import KERN_NOTE_NAME, KERN_NOTE_DURATIONS, INTERVALS_TO_CHORD_QUALITY, CHORD_QUALITY_TO_MXHM, MAJOR_FUNCTION, MINOR_FUNCTION
from fractions import Fraction # for exact ractionals
from data_conversions import duration_to_kern, pitch_to_midi, midi_to_kern_pitch
from temporal_structures import split_at_barlines
from typing import List, Dict,Tuple, Optional, Any, Set

def split_into_voices(notes: List[Dict]) -> List[List[Dict]]:
    """
        Vogliamo dividerli nel minimo numero di gruppi tali che all'interno di ogni gruppo nessun intervallo si sovrapponga.
        Questo è il problema del "coloring of interval graphs".
        1. Ordina gli intervalli per onset.
        2. Per ogni intervallo, assegnalo alla prima "voce" disponibile (quella la cui ultima nota è già finita).
        3. Se nessuna voce è disponibile, creane una nuova.

    Esempio:
        Note: [A: onset=0, offset=4], [B: onset=2, offset=5], [C: onset=4, offset=6]
        1. Ordinate: A, B, C
        2. A → voce 0 (disponibile) ; voice_ends = [4]
        3. B → voce 0 occup. (end=4 > 2) → voce 1 nuova ; voice_ends = [4, 5]
        4. C → voce 0 dispon. (end=4 ≤ 4) ; voice_ends = [6, 5]
        Risultato: voce 0 = [A, C], voce 1 = [B]

    Args:
        notes: lista di note con campi 'onset', 'offset', 'pitch_class', 'octave'

    Returns:
        Lista di voci (ognuna è una lista di note in ordine cronologico).
        Restituisce [[]] se notes è vuota (almeno una voce, anche se vuota).
    """
    
    if not notes:
        return [[]]  #problems with []
    
    # orders per onset
    # Usiamo pitch_class come chiave secondaria per riproducibilità: se due note hanno lo stesso onset, l'ordine tra loro è deterministico.
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
    """
    Converte le note di una voce nella sequenza completa di eventi **kern,
    riempiendo i gap con pause e dividendo le note alle stanghette.

    Perché questa funzione deve "riempire i gap con pause"?
    Perché in **kern ogni spina deve coprire l'INTERA durata del brano:
        se la melodia va da beat 1 a beat 8 (su 16 beat totali),
        dobbiamo aggiungere:
          - pausa da beat 0 a beat 1 (gap iniziale)
          - pausa da beat 8 a beat 16 (gap finale)

    Se non lo facessimo, l'allineamento con le altre spine (accordi, altre voci)
    sarebbe sbagliato: ogni voce deve avere esattamente lo stesso numero di
    "frame temporali" per poterle sincronizzare.

    Esempio visivo:
        beat:    0    1    2    3    4    5    6    7    8
        note:         [  B4  ] [  A4  ] [E4][  F#4  ]
        eventi:  [4r] [4b ] [4a ] [8e][8f#][4r] [4r]
                  ↑                               ↑
               pausa                           pausa
               iniziale                        finale

    Args:
        voice_notes      : note della voce (dal split_into_voices)
        barline_positions: per dividere le note alle stanghette
        num_beats        : durata totale del brano
        beat_unit        : per la conversione delle durate in stringa **kern

    Returns:
        Lista di (onset, duration, token) che copre esattamente [0, num_beats]
    """
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
            rest_segs = split_at_barlines(current, rest_dur,
                'r',    # kern_pitch='r': indica pausa (non usato per is_rest=True)
                True,   # is_rest=True: nessuna legatura, solo divisione durata
                barline_positions,
                beat_unit
            )
            events.extend(rest_segs)
            # extend() aggiunge tutti gli elementi di rest_segs alla lista events (append aggiungerebbe la lista come un elemento solo)

        # Nota melodica effettiva
        midi = pitch_to_midi(note['octave'], note['pitch_class'])
        kern_pitch = midi_to_kern_pitch(midi)

        note_segs = split_at_barlines(
            onset, dur,
            kern_pitch,
            False,   # is_rest=False: questa è una nota vera, usa legature se necessario
            barline_positions,
            beat_unit
        )
        events.extend(note_segs)
        current = offset   # aggiorna il cursore alla fine di questa nota

    # pausa finale: dalla fine dell'ultima nota a num_beats
    if current < total:
        rest_dur  = total - current
        rest_segs = split_at_barlines(current, rest_dur, 'r', True, barline_positions, beat_unit)
        events.extend(rest_segs)

    return events