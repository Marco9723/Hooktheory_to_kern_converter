from fractions import Fraction 
from typing import List, Tuple

def is_rest(tok: str):
    clean = tok.lstrip('[') # otherwise isdigit() doesn't work
    idx = 0 # from zero!
    
    # check the token without [
    # if is a digit or a simble like . or %
    # keep going until i'm reading the numeric part of the token duration
    while idx < len(clean) and (clean[idx].isdigit() or clean[idx] in '.%'):
        idx += 1
    
    # true if the token is a pause, has r after the numeric part
    # if r is the las one, index is 1 less than the position of the rest r
    if idx < len(clean) and clean[idx] == 'r':
         return True
    else:  # this does not happen if there is no r, no rest
        return False

    
def beamable(tok: str):
    # kern duration >= 8 (eighth note or shorter) and is not a rest
    clean = tok.lstrip('[') 
    digits = ''
    # if it is a number (stop as soon as you find something that isn't a number)
    for ch in clean:
        if ch.isdigit(): 
            digits += ch
        else: 
            break
        
    if digits:
        duration_value = int(digits)
    else:
        duration_value = None
    
    if duration_value is not None and duration_value >= 8 and not is_rest(tok):
        return True
    else:
        return False        


def add_beams(events: List[Tuple[Fraction, Fraction, str]], beats_per_bar: int, beat_unit: int):

    # in 6/8 time beaming is grouped into 2 groups of 3 octaves, in 9/8 time 3 groups, 12/8 4 groups
    if beat_unit == 8 and beats_per_bar in (6, 9, 12):
        group_dur = Fraction(3)  # 3 octaves per beat
    else:
        group_dur = Fraction(1)  # one beat only

    copy = list(events)   # work on a copy of the original list of events
    i = 0

    # check all events
    while i < len(copy): 
        onset, dur, token = copy[i]  # it is an event!

        if not beamable(token):  # is a rest or bigger than octave note
            i += 1
            continue # next iteration of while cicle

        # beginning and ending of the beat group to which this note belongs
        group_start = (onset // group_dur) * group_dur
        group_end   = group_start + group_dur

        # collect the indexes of the beamable notes in the group
        beam_indices = []
        j = i # start from current note
        # until: i'm not at the end of the list, the event onset is still within the group, the token is beamable
        # copy[j][0] = onset of current note, copy[j][2] = token of current note
        while j < len(copy) and copy[j][0] < group_end and beamable(copy[j][2]):
            beam_indices.append(j)   #group beamable notes
            j += 1

        # beam if there are at least two notes
        if len(beam_indices) >= 2:
            o, d, t = copy[beam_indices[0]]   # onset, duration, token
            copy[beam_indices[0]] = (o, d, t + 'L')  # adds L to the first token in the group
            o, d, t = copy[beam_indices[-1]]
            copy[beam_indices[-1]] = (o, d, t + 'J')  # adds J to the first token in the group

        i = (beam_indices[-1] + 1) if beam_indices else (i + 1)  # jump to the next unbeamable note

    return copy