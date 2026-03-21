from fractions import Fraction # for exact ractionals
from data_conversions import pitch_to_midi, midi_to_kern_pitch
from temporal_structures import split_at_barlines
from typing import List, Dict

def split_into_voices(notes: List[Dict]) -> List[List[Dict]]:
    """
    we want to divide them into the minimum number of groups such that no interval within each group overlaps
    1) sort the intervals by onset
    2) for each interval assign it to the first available voice (the one whose last note has already ended!)
    3) if no voice is available, create a new one
    Args: notes: list of notes with fields onset, offset, pitch_class, octave
          returns: voices lists
    """
    
    if not notes:
        return [[]]  #problems with []
    
    # orders by onset
    # we use pitch_class as a secondary key for reproducibility: if two notes have the same onset, the order between them is deterministic
    # the key is a tuple: Python compares the first element (onset) first, then the second (pitch_class) if there's a tie
    sorted_notes = sorted(notes, key=lambda n: (n['onset'], n['pitch_class']))
    
    # data structures
    voices = []     # each element is a list of notes  List[List[Dict]]
    voice_ends = []      # offset of the last note of each voice List[float]

    for note in sorted_notes:
        onset = float(note['onset'])   # float() for comparing with voice_ends (Fraction is not needed)
        placed = False                  # flag: have you found a foice?

        # search for available voice
        for v, end in enumerate(voice_ends):
            # 1e-9 = tolerance for floating-point: this entry is available if its last note is finished
            if end <= onset + 1e-9:
                voices[v].append(note)          # add the not to the voice
                voice_ends[v] = float(note['offset'])   # update the end
                placed = True
                break   # we have found the right voice

        # no available voice: create a new one
        if not placed:
            voices.append([note])                        # new list with this note
            voice_ends.append(float(note['offset']))     # its offset is the end

    return voices



def voice_to_events(voice_notes: List[Dict], barline_positions: List[Fraction], num_beats: int, beat_unit: int):
    
    # converts the notes of a voice into the complete sequence of kern events,
    # filling gaps with rests and splitting notes at bar lines.
    
    events = []  # List[Tuple[Fraction, Fraction, str]]
    current = Fraction(0)        # cursor: we advance beat by beat
    total   = Fraction(num_beats)

    for note in sorted(voice_notes, key=lambda n: n['onset']):
        # convert onset and offset to a fraction with a maximum denominator of 1024
        # limit_denominator(1024) simplifies the fraction by avoiding big denominators
        # ex: Fraction('3.5') --> Fraction(7, 2)  (already simple)
        #     Fraction(3.333...) --> could give Fraction(9999, 3000) without limit
        onset  = Fraction(note['onset']).limit_denominator(1024)
        offset = Fraction(note['offset']).limit_denominator(1024)
        dur    = offset - onset

        # Gap before note: add rest
        if onset > current:
            rest_dur = onset - current
            # The rest may cross bar lines, so let's split it to
            # kern_pitch='r': indicates a rest (not used for is_rest=True)
            # is_rest=True: no legatos, only duration division
            rest_segs = split_at_barlines(current, rest_dur,'r', True, barline_positions, beat_unit)
            events.extend(rest_segs)
            # extend() adds all elements of rest_segs to the events list (append would add the list as one element)

        # Actual melody note
        midi = pitch_to_midi(note['octave'], note['pitch_class'])
        kern_pitch = midi_to_kern_pitch(midi)

        # is_rest=False: This is a true note, use legatos if necessary
        note_segs = split_at_barlines(onset, dur,kern_pitch,False,barline_positions,beat_unit)
        events.extend(note_segs)
        current = offset   # update cursor at the end of this note

    # final rest: from the end of the last note to num_beats
    if current < total:
        rest_dur  = total - current
        rest_segs = split_at_barlines(current, rest_dur, 'r', True, barline_positions, beat_unit)
        events.extend(rest_segs)

    return events