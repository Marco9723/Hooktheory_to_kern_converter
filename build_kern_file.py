from fractions import Fraction 
from temporal_structures import get_active_meter, compute_barline_positions
from key_signatures import get_active_key, build_kern_key_sig, build_tonal_token
from manage_poliphony import split_into_voices, voice_to_events
from harmony import harmony_to_events
from typing import List, Dict




def build_kern_file(song_id: str, song: Dict):
    """
    input:
        song_id: key in the dataset (hooktheory id)
        song   : whole song dictionary
    returns:
        string with kern file content (to be written) 
    """

    # 1) data extraction from annotations
    annotations = song.get('annotations', {})  # otherwise empty dict
    num_beats    = int(annotations.get('num_beats', 0)) # convert to integer
    meters       = annotations.get('meters', [{'beat':0,'beats_per_bar':4,'beat_unit':4}])
    keys         = annotations.get('keys', [{'beat':0,'tonic_pitch_class':0, 'scale_degree_intervals':[2,2,1,2,2,2]}])
    melody_notes = annotations.get('melody')  or []  # if melody null, returns None
    harmony_list = annotations.get('harmony') or []
    
    # Estimate num_beats if missing from the maximum offset of the notes or chords
    if num_beats == 0 and melody_notes:
        # max() with key returns the note with the largest offset, then we take its offset and round up
        num_beats = int(max(melody_notes, key=lambda n: n['offset'])['offset'] + 0.99)  # 
    if num_beats == 0 and harmony_list:
        num_beats = int(max(harmony_list, key=lambda c: c['offset'])['offset'] + 0.99)
    if num_beats == 0:
        num_beats = 4   # minimum fallback: at least one measure of 4/4

    # 2) Initial meter and key signature: we need these to write the file header. input: current beat and meter
    init_beats_per_bar, init_beat_unit = get_active_meter(Fraction(0), meters) # returns the time signature (beats_per_bar, beat_unit) active at a given position
    init_tonic, init_intervals = get_active_key(Fraction(0), keys) # same for key
    
    # 3) bars computation
    barline_positions = compute_barline_positions(meters, num_beats)
    
    # 4) manage poliphony into minimum number of voices 
    voices = split_into_voices(melody_notes)
    if not voices or voices == [[]]:
        voices = [[]]
        print("No melodic lines: spine **kern empty.")
    
    n_voices = len(voices)
    total_spines = n_voices + 1

    # build the list of events for each entry
    # it's a list of lists of tuples: for each entry, a sequence of events
    voice_events_list = []  # List[List[Tuple[Fraction, Fraction, str]]]
    for v_notes in voices:
        v_events = voice_to_events(v_notes, barline_positions, num_beats, init_beat_unit)
        voice_events_list.append(v_events)
    
    # 5) conversion chord to events
    harm_events = harmony_to_events(harmony_list, keys)
    
    # 6) collect all attack timestamps (set to automatically eliminate duplicates)
    # (example: voice and chord might have an attack on the same beat)
    all_onsets = set()  

    for v_ev in voice_events_list:
        for (t, _, _) in v_ev:
            all_onsets.add(t)
 
    for (t, _, _) in harm_events:
        all_onsets.add(t)

    # add the bar lines as timestamps
    for bl in barline_positions:
        all_onsets.add(bl)

    # sort the list of events
    sorted_onsets = sorted(all_onsets)

    # 7) scroll indices: for each timeline (vocals or harmony), maintain an index pointing to the current event. We advance it only when we emit that event.
    v_idx = [0] * n_voices    # voice indexes
    h_idx = 0                  # chords index
    
    # 8) build rows of kern file
    lines = []     
    
    # 9) metadata
    hk   = song.get('hooktheory', {})
    # yt   = song.get('youtube', {})
    # urls = hk.get('urls', {})
    
    def rename(slug: str) -> str:   #  adam-lambert--> Adam Lambert
        return ' '.join(w.capitalize() for w in slug.split('-'))

    artist_name = rename(hk.get('artist', 'Unknown Artist'))
    song_name   = rename(hk.get('song',   'Unknown Song'))
    
    def all_spines(token: str) -> str:
        # replies token on all spines, divided by TAB
        return '\t'.join([token] * total_spines)
    
    # 10) File intro
    lines.append(f"!!!title: {song_name}")
    lines.append(f"!!!OTL: {song_name}")
    lines.append(f"!!!COM: {artist_name}")
    lines.append(f"!!!OPR: {artist_name}")
    lines.append(f"!!!hooktheory-id: {song_id}")
    
    # 11) spines opening: ['**kern'] * n_voices  && ['**mxhm'] 
    lines.append('\t'.join(['**kern'] * n_voices + ['**mxhm']))

    # 12) initial configuration tokens
    # standard treble clef, the **mxhm plug receives '*' = "null token" (it has no key)
    clef_row = '\t'.join(['*clefG2'] * n_voices + ['*'])
    lines.append(clef_row)
    

    # state variables to keep track of the current configuration
    # used to avoid rewriting identical tokens and to detect key/meter changes
    key_sig_token  = build_kern_key_sig(init_tonic, init_intervals) # inputs: tonic_pitch_class and intervals (INTERVALS_TO_MODE)
    tonal_token    = build_tonal_token(init_tonic, init_intervals) # same
    time_sig_token = f"*M{init_beats_per_bar}/{init_beat_unit}"
    
    # tokens to repeat on all spines
    lines.append(all_spines(key_sig_token))    # *k[f#]\t*k[f#]
    lines.append(all_spines(tonal_token))      # *D:\t*D:
    lines.append(all_spines(time_sig_token))   # *M4/4\t*M4/4

    # =1- = opening bar
    lines.append(all_spines('=1-'))

    # state variables for main loop 
    bar_number        = 1     # current bar (from 1)
    next_barline_idx  = 0     # pointer to barline_positions list

    # MAIN LOOP: loop through all the timestamps 
    for t in sorted_onsets:

        # set bar: if this timestamp is a bar, we emit it before the events
        # then continues processing events that have an onset coinciding with the bar 
        if (next_barline_idx < len(barline_positions) and t == barline_positions[next_barline_idx]):
            bar_number += 1
            lines.append(all_spines(f"={bar_number}"))
            next_barline_idx += 1
            
        # check if the meter has changed since the last one. Meter changes always coincide with a bar line.
        bpb_t, bu_t = get_active_meter(t, meters)
        
        new_time_sig = f"*M{bpb_t}/{bu_t}"
        
        if new_time_sig != time_sig_token and t in set(barline_positions):
            lines.append(all_spines(new_time_sig))
            time_sig_token = new_time_sig    

        # check tonality change
        tonic_t, intervals_t = get_active_key(t, keys)
        new_key_sig = build_kern_key_sig(tonic_t, intervals_t)
        new_tonal   = build_tonal_token(tonic_t, intervals_t)
        if new_key_sig != key_sig_token:
            # write both the key signature and the key token
            lines.append(all_spines(new_key_sig))
            lines.append(all_spines(new_tonal))
            key_sig_token = new_key_sig    # update state

        # melodic voices token (list of strings)
        row_tokens = []  

        for v in range(n_voices):
            v_events = voice_events_list[v]   # events for this voice
            i = v_idx[v]                       # current index of this voice

            if i < len(v_events) and v_events[i][0] == t:
                # this entry event starts exactly at this timestamp
                row_tokens.append(v_events[i][2])   # [2] is **kern token
                v_idx[v] += 1                      
            else:
                # no timestamp attack for this entry: previous event continues: append token '.'
                row_tokens.append('.')

        # chord token
        if h_idx < len(harm_events) and harm_events[h_idx][0] == t:
            harm_tok = harm_events[h_idx][2]
            h_idx += 1
        else:
            harm_tok = '.'   # previous chord still in progress

        # write the row
        # add the line only if at least one spine has a real event: to avoid unnecessary lines of only '.'
        if any(tok != '.' for tok in row_tokens) or harm_tok != '.':
            lines.append('\t'.join(row_tokens + [harm_tok]))

    # spine ending
    lines.append('\t'.join(['*-'] * total_spines))

    return '\n'.join(lines)