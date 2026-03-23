# beat convention used:  |0123|4567|...    bar at beat 4
# legato with [...] (on 2 different lines in the kern file)
from fractions import Fraction # for exact ractionals
from data_conversions import duration_to_kern
from typing import List, Dict,Tuple

def compute_barline_positions(meters: List[Dict], num_beats: int):
    '''
    # need Fraction to make coparisons of values
    # "meters" tag of json file. Example:
    # [{"beat": 0,  "beats_per_bar": 4, "beat_unit": 4},   4/4 from beat 0 to 15
    # {"beat": 16, "beats_per_bar": 3, "beat_unit": 4}]   3/4 from beat 16
    
    # NB: set instead of list for bars because it avoids duplicates
    # because a meter change could generate duplicate bar lines (the end of the old meter coincides with the start of the new one)
    # at the end we convert to a List and sort to get a sequence
      
    inputs:
        meters: list of meter changes from annotations
        num_beats: total song duration ('num_beats' field)

    returns:
        sorted list of Fractions — bar positions
    '''
    
    def get_beat(m): 
        return m['beat']
    
    # orders per beat --> sort meter changes by start beat
    sorted_meters = sorted(meters, key=get_beat)   
    
    # use a set to collect the bar lines: avoid duplicates (for example when the end of one meter coincides with the beginning of the next)
    barlines = set()      
    
    # iterate over the metric change
    for i, meter in enumerate(sorted_meters):
        #   i=0, meter={"beat":0, "beats_per_bar":4, ...}
        #   i=1, meter={"beat":16, "beats_per_bar":3, ...}
        start = Fraction(meter['beat'])   # beat start of the meter
        beats_per_bar   = meter['beats_per_bar']  # beats per measure
        
        # end meter calculation --> so each meter is active on [start, end)
        if i + 1 < len(sorted_meters):
            # if there is a subsequent meter (final beat of the meter)
            end = Fraction(sorted_meters[i + 1]['beat'])
        else:
            # if there is no next meter
            end = Fraction(num_beats)
            
        # generate bar lines at regular intervals of bpb beats
        # the first bar line is at start + bpb (not at start, which is the beginning)
        bar_line = start + beats_per_bar
        while bar_line <= end:
            # list of beats where the barline falls
            barlines.add(bar_line)   # add() on a set: only adds if it isn't already there
            bar_line += beats_per_bar

    # sorted() on a set: convert to a sorted list
    # sorted list of Fractions: positions of the bars (beats)
    return sorted(barlines)


def get_active_meter(beat: Fraction, meters: List[Dict]) -> Tuple[int, int]:
    # returns the time signature (beats_per_bar, beat_unit) active at a given position
    # this function is called for EVERY event in the song!!
    # returns a tuple (beats_per_bar, beat_unit) --> (4, 4) for 4/4
    beats_per_bar = 4
    beat_unit = 4
    
    # check if the new meter is arrived --> sort by beat!
    for m in sorted(meters, key=lambda x: x['beat']):
        if Fraction(m['beat'])<=beat:
            # the meter is active
            beats_per_bar=m['beats_per_bar']
            beat_unit=m.get('beat_unit',4)
        else:
            break
    return beats_per_bar, beat_unit

def split_at_barlines(onset: Fraction, duration: Fraction, kern_pitch: str, is_rest: bool, barline_positions: List[Fraction], beat_unit: int,):
    '''
    # divides an event that surpass a bar with legatos
    # list of tuples: one note can be 1, 2, 3 segments long
    # returns: (Fraction(3,2), Fraction(1,2), '[8f#')
    #           onset 3.5       dur 0.5 beat    token **kern
    
    Legatos in kern notation:
    A legato connects notes of the same pitch that sound like a single note 
    '[4c' = begins a legato 
    '4c]' = ends a legato 
    '[4c]' = note in the middle of a chain (both opening and closing)

    logic: only the FIRST segment does not have a '[' leading
        all non-first segments have a '[' leading
        only the LAST segment has a ']' trailing
        intermediate segments have both '[' and ']'
        rests do not use slurs (they simply split)
    '''
    
    offset = onset + duration # operation between Fraction elements, ok
    
    internal = []
    for bar_line in barline_positions:  # barline_positions computed in the previous function
        if onset < bar_line < offset:
            internal.append(bar_line)
            
    # if no bar is surpassed
    if not internal:
        dur = duration_to_kern(float(duration), beat_unit)
        # if rest
        if is_rest:
            token = f"{dur}r"
        else:
            token = f"{dur}{kern_pitch}"  # ex: 8f# = octave note of Fa#
        return [(onset, duration, token)]   

    # at least one bar surpassed
    boundaries = internal + [offset]  # (onset, end first bar), (begin first bar, end second bar), (begin second bar, offset)
    
    segments = []   # List[Tuple[Fraction, Fraction, str]]
    cur = onset 
    
    
    for idx, bnd in enumerate(boundaries):
        # enumerate gives (0, boundary[0]), (1, boundary[1]), ...
        # need idx to understand if we are at the first or last segment

        segment_dur = bnd - cur   # segment duration

        # for safety ignore segments of zero or negative duration (they may occur with inaccurate data)
        if segment_dur <= Fraction(0):
            cur = bnd
            continue   

        d = duration_to_kern(float(segment_dur), beat_unit)

        if is_rest:
            # rests are divided without ties: each segment is independent
            token = f"{d}r"

        else:
            # Note: We need to determine whether this segment is first, last or middle
            is_first = (idx == 0)
            is_last  = (bnd == offset)   # is this border the original end?

            if is_first and not is_last:
                # first of multiple segments: opens the ligature towards the next one
                token = f"[{d}{kern_pitch}"  # es: '[8f#' 

            elif is_last and not is_first:
                # last of multiple segments: closes the tie from the previous one
                token = f"{d}{kern_pitch}]" #es: '4f#]' 

            elif not is_first and not is_last:
                # intermediate: both opens (towards the next) and closes (from the previous)
                token = f"[{d}{kern_pitch}]"  # Ex: '[4f#]' = F# quarter note in the middle of a tied chain

            else: # is_first AND is_last: this shouldn't happen because
                token = f"{d}{kern_pitch}"

        segments.append((cur, segment_dur, token))
        cur = bnd   # the next segment starts where this one ends

    return segments


